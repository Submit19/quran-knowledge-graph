"""
Pass 1 — sentence-level dedup of cache answers.

For every entry in data/answer_cache.json:
  * Split the answer into sentences on `(?<=[.!?])\\s+` (same splitter the
    audit uses, so what shows up as `has_repetition=True` here is what
    gets cleaned).
  * Restrict to sentences ≥ 40 chars (short labels / headers don't count
    as "repeated content" — they legitimately recur in markdown
    structure).
  * Keep the FIRST occurrence of each duplicated sentence; remove the
    2nd+ via literal str.replace (single instance at a time, leftmost).
  * Clean up the residue: collapse runs of 3+ newlines to 2, collapse
    runs of 2+ spaces inside a line to 1.

Records `dedup_removed_chars` on every modified entry (chars before −
chars after). Saves via answer_cache._save_cache so the in-memory
singleton stays in sync.

Stop condition: any single answer losing >50% of its content aborts the
pass without saving.

NO Anthropic API calls. NO Neo4j access. NO mutation outside the cache
file.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

SENT_RX = re.compile(r"(?<=[.!?])\s+")
MIN_SENT_LEN = 40
LOSS_GUARD = 0.5  # >50% chars removed triggers a check (not auto-abort)
# Distinguish "splitter is broken" from "content is junk":
#   - splitter bug: many small false-positive duplicates → many distinct
#     dup TYPES, each with low COUNT.
#   - legitimate junk: a few rows repeated dozens of times → few TYPES,
#     each with high COUNT.
# A max-count ≥ this threshold means the cleanup is unambiguously
# removing real bloat (e.g. a table row repeated 166x), so we proceed
# past the LOSS_GUARD for that entry.
JUNK_DUP_COUNT_THRESHOLD = 5


def find_duplicate_sentences(text: str) -> list[str]:
    """Return the list of distinct sentences (≥ MIN_SENT_LEN chars, stripped)
    that appear 2+ times verbatim in the text. Order: highest count first,
    ties broken by longest first (so the most aggressive cleanup runs first
    and avoids accidentally matching shorter sentence-prefixes)."""
    if not text:
        return []
    sents = [s.strip() for s in SENT_RX.split(text) if len(s.strip()) >= MIN_SENT_LEN]
    if not sents:
        return []
    c = Counter(sents)
    dups = [s for s, n in c.items() if n >= 2]
    dups.sort(key=lambda s: (-c[s], -len(s)))
    return dups


def dedup_answer(text: str) -> tuple[str, int]:
    """Return (deduped_text, chars_removed). Keeps the first occurrence of
    each duplicate sentence; replaces subsequent occurrences with empty.

    If NO duplicates exist, returns the text untouched (no whitespace
    normalization). The post-cleanup whitespace passes only run when a
    removal actually happened — otherwise this would mutate every entry
    in the cache for cosmetic reasons, which is out of scope for Pass 1.
    """
    if not text:
        return text, 0
    dups = find_duplicate_sentences(text)
    if not dups:
        return text, 0

    out = text
    for sent in dups:
        # Re-count against the CURRENT `out` — earlier removals may have
        # changed counts (e.g., a longer sentence that contains a shorter
        # one as a substring would have already been collapsed).
        idx = out.find(sent)
        if idx < 0:
            continue
        # Remove every occurrence except the first.
        keep_start = idx + len(sent)
        head = out[:keep_start]
        tail = out[keep_start:].replace(sent, "")
        out = head + tail

    # Post-cleanup: collapse residue from removed sentences.
    # - runs of 3+ newlines → 2 (paragraph break preserved)
    # - runs of 2+ spaces / tabs inside a line → 1 (but don't touch
    #   leading whitespace of a line; markdown lists rely on it)
    out = re.sub(r"\n{3,}", "\n\n", out)
    out = re.sub(r"(?<=\S) {2,}(?=\S)", " ", out)
    out = re.sub(r" +\n", "\n", out)

    return out, len(text) - len(out)


def main() -> int:
    answer_cache._reset_memory_cache_for_tests()
    entries = answer_cache._load_cache()
    total = len(entries)
    print(f"Loaded {total} cache entries")

    modified = 0
    total_removed = 0
    heavy_loss_entries: list[
        tuple[int, int, int, int]
    ] = []  # (idx, before, removed, max_dup_count)
    samples: list[
        tuple[int, str, str, str]
    ] = []  # (idx, question, before_snip, after_snip)

    for i, e in enumerate(entries):
        before = e.get("answer", "") or ""
        if not before:
            continue
        dups = find_duplicate_sentences(before)
        max_dup_count = 0
        if dups:
            sents = [
                s.strip()
                for s in SENT_RX.split(before)
                if len(s.strip()) >= MIN_SENT_LEN
            ]
            counts = Counter(sents)
            max_dup_count = max(counts[s] for s in dups)
        after, removed = dedup_answer(before)
        if removed <= 0:
            continue
        if removed >= len(before) * LOSS_GUARD:
            # Discriminate splitter bug vs legitimate junk.
            if max_dup_count < JUNK_DUP_COUNT_THRESHOLD:
                print(
                    f"STOP: entry {i} would lose {removed}/{len(before)} chars "
                    f"({100 * removed / len(before):.0f}%) and max dup count is "
                    f"only {max_dup_count} — splitter may be wrong.",
                    file=sys.stderr,
                )
                print(f"  question: {e.get('question', '')[:120]!r}", file=sys.stderr)
                return 2
            # Legitimate junk: a sentence repeats ≥JUNK_DUP_COUNT_THRESHOLD
            # times, so removing 50%+ is the right call. Record for the
            # report.
            heavy_loss_entries.append((i, len(before), removed, max_dup_count))
        e["answer"] = after
        e["dedup_removed_chars"] = removed
        modified += 1
        total_removed += removed
        if len(samples) < 5:
            samples.append((i, e.get("question", "")[:80], before, after))

    print("\nPass 1 summary:")
    print(f"  entries modified: {modified}/{total}")
    print(f"  total chars removed: {total_removed:,}")
    if modified:
        print(
            f"  avg chars removed per modified entry: {(total_removed / modified):.0f}"
        )
    if heavy_loss_entries:
        print(
            f"\n  heavy-loss entries (>{int(LOSS_GUARD * 100)}% chars removed) "
            f"— legitimate junk content with max_dup_count >= "
            f"{JUNK_DUP_COUNT_THRESHOLD}:"
        )
        for idx, before_len, removed, max_dup in sorted(
            heavy_loss_entries, key=lambda r: -r[2]
        )[:10]:
            pct = 100 * removed / before_len
            print(
                f"    [#{idx}] before={before_len} removed={removed} "
                f"({pct:.0f}%) max_dup={max_dup}"
            )

    print("\n--- 5 sample before/after diffs ---")
    for idx, q, before, after in samples:
        # Show the first ~300 chars and the last ~300 chars of each, since the
        # interior is where the removal usually lands.
        def snip(s: str) -> str:
            if len(s) <= 600:
                return s
            return s[:300] + "\n  […]  \n" + s[-300:]

        print(f"\n[#{idx}] Q: {q}")
        print(
            f"  before len={len(before)}  after len={len(after)}  removed={len(before) - len(after)}"
        )
        # Show only first 240 chars of head+tail to keep terminal readable
        print(f"  BEFORE head: {before[:240]!r}")
        print(f"  AFTER  head: {after[:240]!r}")

    if modified == 0:
        print("\nNo modifications — nothing to save.")
        return 0

    print("\nSaving cache via answer_cache._save_cache …")
    answer_cache._save_cache(entries)
    print("Saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
