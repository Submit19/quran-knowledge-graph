"""
Pass 2 — strip invalid `[surah:verse]` citations from cache answers.

For every entry in data/answer_cache.json:
  * Extract all `[N:M]` tokens from the answer via the same regex the audit
    uses.
  * Batch-validate against Neo4j (single UNWIND query on the union of all
    cited verseIds across the cache, same pattern as scripts/audit_cache_quality.py).
  * For invalid citations, remove just the `[N:M]` token from the answer
    text. Run a small set of generic cleanups on the residue: empty bold
    `**[X]**` → ``, doubled commas/semicolons, double spaces inside a
    line, and any `(  )` empty parens.
  * Prune the corresponding keys from the entry's `verses` dict (the
    project's "citations field" is `verses`, keyed `"S:V"`).
  * Record `invalid_cites_stripped` (occurrence count, not unique).

Stop / investigate flag (NOT abort): if any single answer would lose >5
citations, log it conspicuously to stderr but proceed — the brief says
flag, don't remove. These entries are surfaced in the final report.

NO Anthropic API calls. Read-only Neo4j (one MATCH).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

CITE_RX = re.compile(r"\[(\d{1,3}):(\d{1,3})\]")
HEAVY_FLAG_THRESHOLD = 5  # >5 invalid cites in one entry → flag (don't abort)


def extract_cites(text: str) -> list[tuple[int, int]]:
    return [(int(s), int(v)) for s, v in CITE_RX.findall(text or "")]


def fetch_valid_set(
    cites: set[tuple[int, int]],
) -> set[tuple[int, int]]:
    """Single batched UNWIND query — same pattern as audit_cache_quality.py."""
    load_dotenv(ROOT / ".env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pw = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "quran")
    if not (uri and user and pw):
        print("Missing Neo4j env vars", file=sys.stderr)
        sys.exit(2)
    valid: set[tuple[int, int]] = set()
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    try:
        with driver.session(database=db) as s:
            rows = s.run(
                """
                UNWIND $cites AS pair
                WITH pair[0] AS surah, pair[1] AS verse
                MATCH (v:Verse {surah: surah, verseNum: verse})
                RETURN surah, verse
                """,
                cites=[list(c) for c in cites],
            ).data()
    finally:
        driver.close()
    for row in rows:
        valid.add((row["surah"], row["verse"]))
    return valid


def strip_token(answer: str, surah: int, verse: int) -> tuple[str, int]:
    """Remove every literal `[surah:verse]` occurrence from `answer`.
    Returns (new_text, occurrences_removed)."""
    tok = f"[{surah}:{verse}]"
    n = answer.count(tok)
    if n == 0:
        return answer, 0
    return answer.replace(tok, ""), n


def cleanup_residue(text: str) -> str:
    """Generic, minimal cleanup after citation removal. Conservative — does
    not touch prose."""
    # Empty bold (left over from `**[X]**` → `****`).
    text = re.sub(r"\*\*\s*\*\*", "", text)
    # Empty parens / brackets left after the cite was the only content.
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    # Doubled punctuation from "[A], [B]" → ", [B]" patterns.
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r";\s*;", ";", text)
    text = re.sub(r",\s*(?=[.;:!?])", "", text)
    text = re.sub(r";\s*(?=[.])", "", text)
    # Hanging "verse " / "verses " / "ayah " / "ayat " followed by punctuation
    # (would be left if the only cite after them was stripped).
    text = re.sub(r"\b(verse|verses|ayah|ayat)s?\s+(?=[.,;])", "", text, flags=re.I)
    # Double spaces inside a line (don't touch leading indent — markdown lists).
    text = re.sub(r"(?<=\S) {2,}(?=\S)", " ", text)
    text = re.sub(r" +\n", "\n", text)
    # Tighten residue around stripped tokens at the very start of a line.
    text = re.sub(r"^[ \t]*[,;]\s*", "", text, flags=re.M)
    return text


def main() -> int:
    answer_cache._reset_memory_cache_for_tests()
    entries = answer_cache._load_cache()
    total = len(entries)
    print(f"Loaded {total} cache entries")

    # Build union of unique cites across the cache.
    all_cites: set[tuple[int, int]] = set()
    for e in entries:
        for c in extract_cites(e.get("answer", "") or ""):
            all_cites.add(c)
    print(f"Unique cited verseIds across cache: {len(all_cites)}")

    valid = fetch_valid_set(all_cites)
    invalid = all_cites - valid
    print(f"Valid (Neo4j-resolvable):   {len(valid)}")
    print(f"Invalid (to be stripped):   {len(invalid)}")

    if not invalid:
        print("No invalid citations — nothing to strip.")
        return 0

    # Per-entry strip.
    entries_modified = 0
    total_occurrences_stripped = 0
    heavy_entries: list[tuple[int, str, int]] = []  # (idx, question, count)
    samples: list[tuple[int, str, str, str]] = []
    verses_keys_pruned_total = 0

    for i, e in enumerate(entries):
        before = e.get("answer", "") or ""
        if not before:
            continue
        cites_here = set(extract_cites(before))
        invalid_here = cites_here & invalid
        if not invalid_here:
            continue
        after = before
        occ = 0
        for s, v in invalid_here:
            after, n = strip_token(after, s, v)
            occ += n
        after = cleanup_residue(after)
        e["answer"] = after
        e["invalid_cites_stripped"] = occ
        entries_modified += 1
        total_occurrences_stripped += occ

        # Prune corresponding keys from verses dict.
        verses = e.get("verses") or {}
        if isinstance(verses, dict):
            removed_keys = 0
            for s, v in invalid_here:
                key = f"{s}:{v}"
                if key in verses:
                    del verses[key]
                    removed_keys += 1
            verses_keys_pruned_total += removed_keys

        if occ > HEAVY_FLAG_THRESHOLD:
            heavy_entries.append((i, e.get("question", "")[:120], occ))

        if len(samples) < 5:
            # Capture a localized snippet around the first stripped position.
            first_inv = next(iter(invalid_here))
            tok = f"[{first_inv[0]}:{first_inv[1]}]"
            pos = before.find(tok)
            if pos >= 0:
                lo = max(0, pos - 60)
                hi = min(len(before), pos + len(tok) + 60)
                snip_before = before[lo:hi]
                # Re-locate same anchor in after — heuristic: use the 30
                # chars BEFORE the stripped token as the anchor.
                anchor = before[max(0, pos - 30) : pos]
                after_pos = after.find(anchor)
                snip_after = (
                    after[after_pos : after_pos + (hi - lo)]
                    if after_pos >= 0
                    else after[: hi - lo]
                )
                samples.append((i, e.get("question", "")[:80], snip_before, snip_after))

    print("\nPass 2 summary:")
    print(f"  entries modified:        {entries_modified}/{total}")
    print(f"  invalid cites stripped:  {total_occurrences_stripped} occurrences")
    print(f"  verses-dict keys pruned: {verses_keys_pruned_total}")

    if heavy_entries:
        print(
            f"\n  entries losing >{HEAVY_FLAG_THRESHOLD} citations (flagged, not removed):"
        )
        for idx, q, n in sorted(heavy_entries, key=lambda r: -r[2])[:15]:
            print(f"    [#{idx}] {n} cites stripped — {q!r}")

    print("\n--- 5 sample before/after snippets ---")
    for idx, q, before_snip, after_snip in samples:
        print(f"\n[#{idx}] Q: {q}")
        print(f"  BEFORE: {before_snip!r}")
        print(f"  AFTER:  {after_snip!r}")

    print("\nSaving cache via answer_cache._save_cache …")
    answer_cache._save_cache(entries)
    print("Saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
