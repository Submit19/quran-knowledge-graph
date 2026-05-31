"""Build data/khalifa_corpus/sermons/MANIFEST.json from the scraped sermon files.

Reads the YAML-ish frontmatter of every data/khalifa_corpus/sermons/*.md and the
scrape run-results log, and emits a per-file index plus aggregate stats (videos
kept, total Rashad words, videos skipped with reason).

Usage:
    python scripts/build_sermons_manifest.py
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERMONS = ROOT / "data" / "khalifa_corpus" / "sermons"
RUN_RESULTS = (
    ROOT / "data" / "research" / "sermon_transcript_hunt" / "scrape_run_results.json"
)
MANIFEST = SERMONS / "MANIFEST.json"

_NUM_FIELDS = {"segments_kept", "segments_dropped", "total_words"}


def parse_frontmatter(text: str) -> dict:
    """Parse the leading --- ... --- block. Frontmatter is author-controlled and
    flat (key: value), so a line parser is sufficient and dependency-free."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith('"') and val.endswith('"') and len(val) >= 2:
            val = val[1:-1].replace('\\"', '"').replace("\\\\", "\\")
        if key in _NUM_FIELDS:
            try:
                val = int(val)
            except ValueError:
                pass
        fm[key] = val
    return fm


def main() -> None:
    files = sorted(SERMONS.glob("*.md"))
    entries = []
    for f in files:
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        entries.append(
            {
                "file": f.name,
                "youtube_id": fm.get("youtube_id", ""),
                "title": fm.get("title", ""),
                "source": fm.get("source", ""),
                "upload_date": fm.get("upload_date", ""),
                "default_speaker": fm.get("default_speaker", ""),
                "segments_kept": fm.get("segments_kept", 0),
                "segments_dropped": fm.get("segments_dropped", 0),
                "total_words": fm.get("total_words", 0),
                "sha256": fm.get("sha256", ""),
            }
        )

    skipped = []
    if RUN_RESULTS.exists():
        for r in json.loads(RUN_RESULTS.read_text(encoding="utf-8")):
            if r.get("status") != "ok":
                skipped.append(
                    {
                        "youtube_id": r.get("id", ""),
                        "status": r.get("status", ""),
                        "title": r.get("title", ""),
                        "reason": (
                            "no Rashad-attributed content after segmentation"
                            if r.get("status", "").startswith("skipped")
                            else r.get("status", "")
                        ),
                    }
                )

    manifest = {
        "bucket": "sermons",
        "description": (
            "Speaker-segmented Rashad Khalifa sermon/lecture transcripts, "
            "scraped from human-authored English subtitle tracks on the "
            "@asubmitter2god YouTube channel. Only Rashad's own turns are "
            "kept (Khalifa-only source rule)."
        ),
        "source_channel": "@asubmitter2god",
        "transcript_type": "manual_human_authored",
        "speaker_segmented": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "videos_kept": len(entries),
            "total_rashad_words": sum(e["total_words"] for e in entries),
            "total_segments_kept": sum(e["segments_kept"] for e in entries),
            "total_segments_dropped": sum(e["segments_dropped"] for e in entries),
            "videos_skipped": len(skipped),
        },
        "videos": entries,
        "skipped": skipped,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"wrote {MANIFEST} — {len(entries)} videos, "
        f"{manifest['stats']['total_rashad_words']} Rashad words, "
        f"{len(skipped)} skipped"
    )


if __name__ == "__main__":
    main()
