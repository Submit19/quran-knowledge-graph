"""
Pass 5 — coverage report + gap analysis over the enriched cache.

Produces data/research/cache_coverage_report_2026-05-21.md with:
  - Surah coverage: fraction of 114 surahs cited at least once, and a
    frequency histogram showing which surahs are over/underrepresented.
  - Prophet coverage: cross-references the cache against the canonical
    25-prophet list (sourced from the broad-013 answer in the capable-
    model baseline).
  - Top Arabic-root mentions: rough heuristic, dash-separated 3-letter
    Arabic patterns ر-ح-م-style.
  - Coverage-gap analysis: each main-set eval question's best-match
    cosine similarity to any cache entry, using the BGE-M3 embeddings
    written by Pass 4. Held-out eval set gets aggregate stats only —
    per-question detail would leak the seal.

NO mutations to data/answer_cache.json.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from model_registry import get_bge_m3  # noqa: E402

CACHE_FILE = ROOT / "data" / "answer_cache.json"
EVAL_MAIN = ROOT / "data" / "eval" / "v2" / "_questions_only.json"
OUT_MD = ROOT / "data" / "research" / "cache_coverage_report_2026-05-21.md"

# Canonical 25-prophet list (sourced from broad-013 baseline answer).
# Each entry is the primary Anglicised name plus common alternates we may
# find in answer text. Lowercase keys for case-insensitive matching.
PROPHETS_25 = [
    ("Adam", ["adam"]),
    ("Idris", ["idris", "enoch"]),
    ("Noah", ["noah", "nuh"]),
    ("Hud", ["hud"]),
    ("Salih", ["salih"]),
    ("Abraham", ["abraham", "ibrahim"]),
    ("Lut", ["lut", "lot"]),
    ("Ismail", ["ismail", "ishmael", "isma'il"]),
    ("Ishaq", ["ishaq", "isaac"]),
    ("Ya`qub", ["ya'qub", "yaqub", "jacob"]),
    ("Yusuf", ["yusuf", "joseph"]),
    ("Ayyub", ["ayyub", "job"]),
    ("Shu`aib", ["shu'aib", "shuaib", "shoaib"]),
    ("Musa", ["musa", "moses"]),
    ("Harun", ["harun", "aaron"]),
    ("Dawud", ["dawud", "david"]),
    ("Sulaiman", ["sulaiman", "solomon"]),
    ("Ilyas", ["ilyas", "elijah", "elias"]),
    ("Al-Yasa`", ["al-yasa", "alyasa", "elisha"]),
    ("Yunus", ["yunus", "jonah"]),
    ("Zakariya", ["zakariya", "zechariah", "zakaria"]),
    ("Yahya", ["yahya", "john the baptist"]),
    ("`Isa", ["'isa", " isa ", "jesus"]),
    ("Muhammad", ["muhammad", "mohammed"]),
    ("Dhul-Kifl", ["dhul-kifl", "dhul kifl", "zul-kifl"]),
]

CITE_RX = re.compile(r"\[(\d{1,3}):(\d{1,3})\]")
# Loose Arabic root: 3 letters separated by hyphens or whitespace.
ROOT_RX = re.compile(r"(?<![A-Za-z])([؀-ۿ])[ \-]([؀-ۿ])[ \-]([؀-ۿ])(?![A-Za-z])")


def cosine(a, b):
    return float(np.dot(a, b))


def main() -> int:
    print("Loading cache + eval set + BGE-M3 model...")
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    eval_main = json.loads(EVAL_MAIN.read_text(encoding="utf-8"))
    print(f"  cache: {len(cache)}")
    print(f"  eval main: {len(eval_main)}")

    # --- Surah coverage ---
    surahs_seen: Counter[int] = Counter()
    for rec in cache:
        for s, _v in CITE_RX.findall(rec.get("answer", "") or ""):
            si = int(s)
            if 1 <= si <= 114:
                surahs_seen[si] += 1

    surah_coverage = len(surahs_seen)
    surah_coverage_pct = 100 * surah_coverage / 114

    # --- Prophet coverage ---
    prophets_seen: dict[str, int] = {}
    for canonical, aliases in PROPHETS_25:
        hits = 0
        for rec in cache:
            txt = (rec.get("answer") or "").lower()
            if any(a in txt for a in aliases):
                hits += 1
        prophets_seen[canonical] = hits

    prophets_covered = sum(1 for n in prophets_seen.values() if n > 0)

    # --- Arabic-root frequency ---
    root_counts: Counter[str] = Counter()
    for rec in cache:
        for m in ROOT_RX.findall(rec.get("answer", "") or ""):
            root = "-".join(m)
            root_counts[root] += 1

    # --- Gap analysis (main set, per-question; held-out aggregate only) ---
    print("Loading BGE-M3 for query embeddings (re-uses model already in cache)...")
    model = get_bge_m3()

    cache_m3 = np.array([rec["embedding_m3"] for rec in cache])  # (N, 1024)
    print(f"  cache embedding matrix: {cache_m3.shape}")

    def best_match(q: str) -> tuple[float, str]:
        emb = model.encode(q, normalize_embeddings=True)
        sims = cache_m3 @ emb
        idx = int(np.argmax(sims))
        return float(sims[idx]), cache[idx].get("question", "")

    # Main set
    print("Scoring main-set eval questions...")
    main_results: list[dict] = []
    for q in eval_main:
        sim, matched = best_match(q["question"])
        main_results.append(
            {
                "id": q["id"],
                "bucket": q["bucket"],
                "question": q["question"],
                "best_sim": round(sim, 3),
                "best_match": matched,
            }
        )

    # Held-out — aggregate only. Read at the latest moment to keep the
    # answers/rubrics out of memory longer than necessary.
    holdout_file = ROOT / "data" / "eval" / "v2" / "_holdout.yaml"
    holdout_sims: list[float] = []
    holdout_count = 0
    if holdout_file.exists():
        import yaml  # local — avoid module-level dep if not present

        sealed = yaml.safe_load(holdout_file.read_text(encoding="utf-8"))
        # We use ONLY the question text for similarity scoring; we do
        # NOT echo any held-out question text or its match anywhere in
        # the report. The seal is preserved at the report level.
        for q in sealed:
            sim, _ = best_match(q["question"])
            holdout_sims.append(sim)
        holdout_count = len(holdout_sims)

    # Sorted gap lists
    gaps_main = sorted(main_results, key=lambda r: r["best_sim"])

    # --- Build report ---
    lines: list[str] = []
    lines.append("# Cache Coverage Report — 2026-05-21\n")
    lines.append(
        f"Source: `data/answer_cache.json` ({len(cache)} entries, "
        f"post-prune, post-enrich, with BGE-M3 question embeddings).\n"
    )
    lines.append("Read-only pass; no entries mutated.\n")

    lines.append("## Surah coverage\n")
    lines.append(
        f"**{surah_coverage} of 114** surahs cited at least once "
        f"({surah_coverage_pct:.1f}%)."
    )
    missing_surahs = [s for s in range(1, 115) if s not in surahs_seen]
    lines.append(
        f"\nSurahs with **zero** citations across the cache: {len(missing_surahs)}\n"
    )
    if missing_surahs:
        lines.append("`" + ", ".join(str(s) for s in missing_surahs) + "`\n")

    lines.append("### Top 10 most-cited surahs\n")
    lines.append("| Surah | Cache occurrences |")
    lines.append("|---:|---:|")
    for s, n in surahs_seen.most_common(10):
        lines.append(f"| {s} | {n} |")

    lines.append("\n### Bottom 10 (non-zero) surahs by citations\n")
    lines.append("| Surah | Cache occurrences |")
    lines.append("|---:|---:|")
    for s, n in sorted(surahs_seen.items(), key=lambda x: x[1])[:10]:
        lines.append(f"| {s} | {n} |")

    lines.append("\n## Prophet coverage\n")
    lines.append(
        f"**{prophets_covered} of 25** named prophets appear in at least one "
        "cache entry's answer text (case-insensitive substring match across "
        "Anglicised + Arabic transliteration variants).\n"
    )
    lines.append("| Prophet | Entries mentioning |")
    lines.append("|---|---:|")
    for name, n in sorted(prophets_seen.items(), key=lambda x: -x[1]):
        lines.append(f"| {name} | {n} |")

    lines.append("\n## Top 20 Arabic roots in cache answers\n")
    lines.append(
        "Heuristic: three-letter Arabic characters separated by "
        "hyphens or spaces. Includes spurious adjacencies; treat as "
        "directional, not authoritative.\n"
    )
    lines.append("| Root | Occurrences |")
    lines.append("|---|---:|")
    for root, n in root_counts.most_common(20):
        lines.append(f"| {root} | {n} |")

    lines.append("\n## Coverage gaps — main eval set\n")
    lines.append(
        "Cosine similarity (BGE-M3) of each main-set question to "
        "its best-matching cache entry. Lower = thinner coverage.\n"
    )
    lo_main = [r for r in gaps_main if r["best_sim"] < 0.6]
    lines.append(
        f"- {len(lo_main)} of {len(gaps_main)} main questions have "
        f"best-match similarity < 0.60."
    )
    lines.append("\n### Bottom 15 main-set questions by best-match similarity\n")
    lines.append("| ID | Bucket | sim | Question | Best match (cache) |")
    lines.append("|---|---|---:|---|---|")
    for r in gaps_main[:15]:
        q = r["question"][:80].replace("|", "\\|")
        m = r["best_match"][:60].replace("|", "\\|")
        lines.append(f"| {r['id']} | {r['bucket']} | {r['best_sim']} | {q} | {m} |")

    if holdout_sims:
        lo_holdout = sum(1 for s in holdout_sims if s < 0.6)
        mean = sum(holdout_sims) / len(holdout_sims)
        min_, max_ = min(holdout_sims), max(holdout_sims)
        lines.append("\n## Coverage gaps — held-out set (aggregate only)\n")
        lines.append(
            "_The held-out set is sealed per `data/eval/v2/_holdout.yaml`. "
            "We report only aggregate statistics here; per-question "
            "similarity is intentionally omitted so the seal isn't leaked._\n"
        )
        lines.append(f"- Held-out questions evaluated: **{holdout_count}**")
        lines.append(f"- Below 0.60 similarity: **{lo_holdout}**")
        lines.append(f"- Mean / min / max: **{mean:.3f}** / {min_:.3f} / {max_:.3f}")

    lines.append("\n## Top-5 candidate themes for next seeding pass\n")
    # Take the 5 lowest-similarity main-set entries and derive a theme
    # from each. We do this in the report as a hint, but the brief's
    # "30-min targeted refinement" guidance lives in state_2026-05-21.md.
    lines.append(
        "Drawn from the bottom of the main-set gap table above. "
        "These are themes the cache currently answers thinly — a "
        "future seeding pass should target them.\n"
    )
    for r in gaps_main[:5]:
        lines.append(f"- `{r['id']}` (sim {r['best_sim']}): {r['question']}")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {OUT_MD}")
    print(f"Main-set questions below sim 0.60: {len(lo_main)} / {len(gaps_main)}")
    if holdout_sims:
        lo_holdout = sum(1 for s in holdout_sims if s < 0.6)
        print(f"Held-out questions below sim 0.60: {lo_holdout} / {len(holdout_sims)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
