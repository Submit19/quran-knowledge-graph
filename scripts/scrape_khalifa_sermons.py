"""
Scrape Khalifa sermon transcripts from the @asubmitter2god YouTube channel.

The transcripts are human-authored English subtitle tracks (NOT machine ASR)
uploaded by the community. See
data/research/sermon_transcript_hunt/findings_2026-05-27.md for the full hunt.

Pipeline per video:
  1. yt-dlp pulls metadata (title, upload_date) + the manual English subtitle
     track (en / en-US), caching the raw .vtt under .cache/sermon_subs/.
  2. The .vtt is parsed into timestamped cues.
  3. Speaker segmentation keeps ONLY Rashad Khalifa's spoken turns and drops
     every other named speaker (Linda, Kathryn, Edip, Layth, Audience, ...).
  4. One Markdown file per kept video lands under data/khalifa_corpus/sermons/.

Khalifa-only source rule (project-foundational): the corpus may contain only
Khalifa's own words. The community transcripts carry inline speaker labels
(`Rashad:`, `Edip:`, `Audience:`), but a label appears only on a speaker
*change* — mid-monologue cues are unlabeled and belong to whoever spoke last.
So naive "keep lines starting with Rashad:" would discard ~95% of his actual
speech. We instead track the current speaker statefully:

  - In a Friday Sermon ("by Dr. Rashad Khalifa"), Rashad is the DEFAULT speaker;
    unlabeled cues are his until a label switches away.
  - In a community-led study session ("Quran Study by Linda"), Rashad is NOT the
    default — only cues explicitly switched to him (and their unlabeled
    continuations until the next label) are kept. Conservative, rule-safe.

Usage:
    python scripts/scrape_khalifa_sermons.py                 # all en-subtitled videos
    python scripts/scrape_khalifa_sermons.py --ids A,B,C     # only these video ids
    python scripts/scrape_khalifa_sermons.py --limit 3       # first N (smoke test)
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CENSUS = (
    ROOT
    / "data"
    / "research"
    / "sermon_transcript_hunt"
    / "asubmitter2god_subtitle_census.csv"
)
CACHE_DIR = ROOT / ".cache" / "sermon_subs"
OUT_DIR = ROOT / "data" / "khalifa_corpus" / "sermons"
CHANNEL = "@asubmitter2god"

# When False (default), fetch() reuses cached info.json + .vtt instead of
# re-hitting YouTube — so a re-segmentation run is network-free. --refresh forces
# a fresh download.
REFRESH = False

# Speaker-label aliases that ARE Rashad.
RASHAD_ALIASES = {
    "rashad",
    "rashad khalifa",
    "dr. rashad khalifa",
    "dr rashad khalifa",
    "dr. rashad",
    "dr rashad",
    "rk",
    "r.k.",
    "r.k",
    "rashad k",
    "rashad k.",
}

# A cue's text begins with a speaker label when it matches:  Name:  text
# Name = 1-3 short word-tokens (letters, ., ', -), total <= 25 chars, then a
# colon. This catches "Rashad:", "Edip :", "guy:", "Ahmad's wife:", "Audience:"
# while NOT matching "4:69", "Sura no. 1", or transliterations (no leading colon).
_LABEL_RE = re.compile(r"^\s*([A-Za-z][A-Za-z .'\-]{0,24})\s*:\s+(.*)$")

_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->")

# Single lowercase role-words that ARE valid (unnamed) speaker labels.
GENERIC_SPEAKERS = {
    "guy",
    "audience",
    "man",
    "woman",
    "lady",
    "boy",
    "girl",
    "kid",
    "child",
    "questioner",
    "someone",
    "brother",
    "sister",
    "wife",
    "husband",
    "voice",
}

# Function/verb words that betray a PROSE colon ("he says:", "in the famous
# book:") rather than a speaker label. A candidate label containing any of
# these is rejected — otherwise it flips the speaker mid-monologue and silently
# drops the rest of the current speaker's words.
_PROSE_WORDS = {
    "the",
    "a",
    "an",
    "to",
    "of",
    "in",
    "on",
    "is",
    "are",
    "was",
    "were",
    "say",
    "says",
    "said",
    "saying",
    "simply",
    "which",
    "means",
    "meaning",
    "here",
    "there",
    "they",
    "he",
    "she",
    "it",
    "its",
    "but",
    "and",
    "so",
    "that",
    "this",
    "these",
    "those",
    "famous",
    "book",
    "expression",
    "will",
    "would",
    "can",
    "could",
    "about",
    "then",
    "what",
    "when",
    "where",
    "who",
    "because",
    "if",
    "as",
    "at",
    "by",
    "for",
    "with",
    "from",
    "god",
    "allah",
    "quran",
    "verse",
    "sura",
    "you",
    "we",
    "i",
    "my",
    "your",
    "our",
    "his",
    "her",
    "them",
    "us",
    "all",
    "not",
    "no",
    "yes",
    "now",
    "out",
    "up",
}


def valid_label(raw: str) -> bool:
    """True if `raw` (the text before a colon) is a real speaker label rather
    than a prose fragment. Real labels are short names/roles: "Rashad",
    "Edip", "Ahmad's wife", "guy", "Audience". Prose like "he says" or
    "in the famous book" is rejected."""
    norm = raw.strip().lower().rstrip(" .")
    if norm in RASHAD_ALIASES:
        return True
    words = [w for w in re.split(r"[ .']+", norm) if w]
    if not (1 <= len(words) <= 3):
        return False
    if any(w in _PROSE_WORDS for w in words):
        return False
    if norm in GENERIC_SPEAKERS:
        return True
    # A name: starts with a capital (in the ORIGINAL casing).
    return raw.strip()[:1].isupper()


def _find_cached_vtt(video_id: str):
    """Return the cached manual-en .vtt for a video (prefer en-US), or None."""
    for cand in (f"{video_id}.en-US.vtt", f"{video_id}.en.vtt"):
        p = CACHE_DIR / cand
        if p.exists():
            return p
    matches = sorted(CACHE_DIR.glob(f"{video_id}.en*.vtt"))
    return matches[0] if matches else None


def parse_speaker(cue: str) -> tuple[bool, bool, str]:
    """Classify a cue. Returns (is_label, is_rashad, text).
    is_label is False for prose colons — the whole cue is then treated as
    continued speech of the current speaker."""
    m = _LABEL_RE.match(cue)
    if m and valid_label(m.group(1)):
        label = m.group(1).strip().lower().rstrip(" .")
        return True, label in RASHAD_ALIASES, m.group(2).strip()
    return False, False, cue


def log(msg: str) -> None:
    print(msg, flush=True)


def read_census() -> list[dict]:
    """Return [{id, dur_s, subs:[...]}] for every census row."""
    rows = []
    text = CENSUS.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines()):
        line = line.strip()
        if not line or i == 0:  # skip header
            continue
        parts = line.split("|")
        if len(parts) < 3:
            continue
        vid, dur, subs = parts[0], parts[1], parts[2]
        sub_list = [s.strip() for s in subs.split(",") if s.strip()]
        rows.append({"id": vid, "dur_s": float(dur) if dur else 0.0, "subs": sub_list})
    return rows


def has_manual_english(row: dict) -> bool:
    return any(s.lower().startswith("en") for s in row["subs"])


def pick_en_lang(row: dict) -> str:
    """Prefer en-US, then en, then any en* manual track."""
    lower = {s.lower(): s for s in row["subs"]}
    for cand in ("en-us", "en"):
        if cand in lower:
            return lower[cand]
    for s in row["subs"]:
        if s.lower().startswith("en"):
            return s
    return "en"


def ytdlp(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "yt_dlp", *args],
        capture_output=True,
        text=True,
        timeout=180,
    )


def fetch(video_id: str) -> dict | None:
    """Download info.json + manual en subtitle into the cache. Returns metadata.

    Reuses the cached info.json + .vtt when present (unless REFRESH), making
    re-segmentation runs network-free and idempotent."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    info_path = CACHE_DIR / f"{video_id}.info.json"
    cached_vtt = _find_cached_vtt(video_id)
    if not REFRESH and info_path.exists() and cached_vtt is not None:
        info = json.loads(info_path.read_text(encoding="utf-8"))
        return {
            "title": info.get("title", ""),
            "upload_date": info.get("upload_date", ""),
            "vtt_path": cached_vtt,
        }
    url = f"https://www.youtube.com/watch?v={video_id}"
    out_tmpl = str(CACHE_DIR / f"{video_id}.%(ext)s")
    res = ytdlp(
        [
            "--write-info-json",
            "--write-subs",
            "--sub-langs",
            "en.*",
            "--skip-download",
            "--convert-subs",
            "vtt",
            "-o",
            out_tmpl,
            url,
        ]
    )
    if res.returncode != 0:
        log(
            f"    yt-dlp failed ({res.returncode}): {res.stderr.strip().splitlines()[-1] if res.stderr.strip() else ''}"
        )
        return None

    info_path = CACHE_DIR / f"{video_id}.info.json"
    if not info_path.exists():
        log("    no info.json written")
        return None
    info = json.loads(info_path.read_text(encoding="utf-8"))

    # Find the downloaded manual en vtt (prefer en-US).
    vtt = None
    for cand in (f"{video_id}.en-US.vtt", f"{video_id}.en.vtt"):
        p = CACHE_DIR / cand
        if p.exists():
            vtt = p
            break
    if vtt is None:
        matches = sorted(CACHE_DIR.glob(f"{video_id}.en*.vtt"))
        vtt = matches[0] if matches else None

    return {
        "title": info.get("title", ""),
        "upload_date": info.get("upload_date", ""),  # YYYYMMDD
        "vtt_path": vtt,
    }


def parse_vtt(vtt_text: str) -> list[str]:
    """Return the text payload of each cue, in order (one string per cue,
    multi-line cues joined with a space). Header/timestamp lines dropped."""
    cues = []
    buf = []
    for raw in vtt_text.splitlines():
        line = raw.rstrip()
        if not line:
            if buf:
                cues.append(" ".join(b.strip() for b in buf).strip())
                buf = []
            continue
        if (
            line.startswith("WEBVTT")
            or line.startswith("Kind:")
            or line.startswith("Language:")
        ):
            continue
        if _TS_RE.match(line):
            # new cue begins; flush any pending (defensive — cues are blank-separated)
            if buf:
                cues.append(" ".join(b.strip() for b in buf).strip())
                buf = []
            continue
        if line.isdigit():  # numeric cue index (srt-style); skip
            continue
        buf.append(line)
    if buf:
        cues.append(" ".join(b.strip() for b in buf).strip())
    return [c for c in cues if c]


def default_speaker_is_rashad(title: str) -> bool:
    """Decide the DEFAULT speaker for unlabeled cues from the video title.

    Returns True when Rashad is the default speaker (solo lecture / Friday
    sermon — unlabeled cues are his). Returns False for community-led study
    sessions ("... by Linda") and for ambiguous titles, so that only cues
    explicitly switched to "Rashad:" are kept. Conservative toward the
    Khalifa-only rule: when unsure, default to NOT-Rashad.
    """
    t = title.lower()

    # "by <someone>" where <someone> is NOT Rashad => a community leader runs it.
    if re.search(r"\bby\s+(?!dr\.?\s*rashad\b|rashad\b|r\.?k\.?\b)", t):
        return False

    # Rashad is named, or it's an unambiguously Rashad-led format.
    if (
        "rashad" in t
        or "khalifa" in t
        or re.search(r"\brk\b", t)
        or "friday sermon" in t
        or "khutba" in t
        or "khutbah" in t
        or "jumua" in t
        or "jumaa" in t
    ):
        return True

    # No speaker cue at all => conservative: keep only explicit Rashad: turns.
    return False


# Back-compat alias (older name).
def is_sermon_title(title: str) -> bool:
    return default_speaker_is_rashad(title)


def segment_rashad(cues: list[str], default_rashad: bool) -> tuple[list[str], int, int]:
    """Stateful speaker segmentation. Returns (kept_texts, kept, dropped)."""
    current_is_rashad = default_rashad
    kept, dropped = [], 0
    for cue in cues:
        is_label, is_rashad, text = parse_speaker(cue)
        if is_label:
            current_is_rashad = is_rashad
        if current_is_rashad:
            if text:
                kept.append(text)
        else:
            dropped += 1
    return kept, len(kept), dropped


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return (s[:50]).strip("_") or "untitled"


def yaml_escape(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_markdown(
    video_id: str,
    meta: dict,
    kept_texts: list[str],
    kept: int,
    dropped: int,
    default_rashad: bool,
) -> Path:
    body = "\n\n".join(kept_texts).strip() + "\n"
    total_words = sum(len(t.split()) for t in kept_texts)
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    upload = meta["upload_date"]
    upload_iso = (
        f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if len(upload) == 8 else upload
    )

    fm = [
        "---",
        f"title: {yaml_escape(meta['title'])}",
        f"source: https://www.youtube.com/watch?v={video_id}",
        f"channel: {yaml_escape(CHANNEL)}",
        f"youtube_id: {video_id}",
        f"upload_date: {upload_iso}",
        "transcript_type: manual_human_authored",
        "speaker_segmented: true",
        f"default_speaker: {'rashad' if default_rashad else 'other'}",
        'segmentation_filter: ["Rashad"]',
        "segmentation_policy: stateful_speaker_tracking",
        f"segments_kept: {kept}",
        f"segments_dropped: {dropped}",
        f"total_words: {total_words}",
        f"scraped_at: {datetime.now(timezone.utc).isoformat()}",
        f"sha256: {sha}",
        "---",
        "",
    ]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{video_id}__{slugify(meta['title'])}.md"
    out.write_text("\n".join(fm) + body, encoding="utf-8")
    return out


def process(row: dict) -> dict:
    vid = row["id"]
    log(f"[{vid}] fetching...")
    meta = fetch(vid)
    if not meta or not meta.get("vtt_path"):
        return {"id": vid, "status": "fetch_failed"}

    cues = parse_vtt(meta["vtt_path"].read_text(encoding="utf-8"))
    default_rashad = default_speaker_is_rashad(meta["title"])
    kept_texts, kept, dropped = segment_rashad(cues, default_rashad)
    total_words = sum(len(t.split()) for t in kept_texts)

    if kept == 0 or total_words < 30:
        log(
            f"    SKIP — no Rashad content (kept={kept}, words={total_words}, "
            f"default_rashad={default_rashad}, title={meta['title']!r})"
        )
        return {
            "id": vid,
            "status": "skipped_no_rashad",
            "title": meta["title"],
            "default_rashad": default_rashad,
            "cues": len(cues),
        }

    out = write_markdown(vid, meta, kept_texts, kept, dropped, default_rashad)
    log(
        f"    OK — kept {kept} cues / {dropped} dropped / {total_words} words "
        f"(default_rashad={default_rashad}) -> {out.name}"
    )
    return {
        "id": vid,
        "status": "ok",
        "title": meta["title"],
        "file": out.name,
        "default_rashad": default_rashad,
        "segments_kept": kept,
        "segments_dropped": dropped,
        "total_words": total_words,
        "upload_date": meta["upload_date"],
        "cues": len(cues),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", help="comma-separated video ids (overrides census filter)")
    ap.add_argument("--limit", type=int, default=0, help="process only first N")
    ap.add_argument("--sleep", type=float, default=2.0, help="seconds between videos")
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="force re-download even if a cached .vtt exists",
    )
    args = ap.parse_args()

    global REFRESH
    REFRESH = args.refresh

    census = read_census()
    by_id = {r["id"]: r for r in census}

    if args.ids:
        wanted = [
            by_id.get(i.strip(), {"id": i.strip(), "dur_s": 0.0, "subs": ["en"]})
            for i in args.ids.split(",")
            if i.strip()
        ]
    else:
        wanted = [r for r in census if has_manual_english(r)]
    if args.limit:
        wanted = wanted[: args.limit]

    log(
        f"census rows: {len(census)} | manual-en: {sum(1 for r in census if has_manual_english(r))} "
        f"| processing: {len(wanted)}"
    )

    results = []
    for i, row in enumerate(wanted, 1):
        log(f"--- {i}/{len(wanted)} ---")
        try:
            results.append(process(row))
        except subprocess.TimeoutExpired:
            log(f"    TIMEOUT on {row['id']}")
            results.append({"id": row["id"], "status": "timeout"})
        except Exception as e:  # noqa: BLE001 — keep the batch going, record the failure
            log(f"    ERROR on {row['id']}: {e!r}")
            results.append({"id": row["id"], "status": f"error:{type(e).__name__}"})
        if args.sleep and i < len(wanted):
            time.sleep(args.sleep)

    # Run summary (NOT the corpus manifest — that's built separately).
    ok = [r for r in results if r["status"] == "ok"]
    log("\n=== SUMMARY ===")
    log(
        f"ok: {len(ok)} | skipped: {sum(1 for r in results if r['status'].startswith('skip'))} "
        f"| failed: {sum(1 for r in results if r['status'] not in ('ok',) and not r['status'].startswith('skip'))}"
    )
    log(f"total Rashad words: {sum(r.get('total_words', 0) for r in ok)}")
    run_log = (
        ROOT
        / "data"
        / "research"
        / "sermon_transcript_hunt"
        / "scrape_run_results.json"
    )
    run_log.parent.mkdir(parents=True, exist_ok=True)
    run_log.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"run results -> {run_log}")


if __name__ == "__main__":
    main()
