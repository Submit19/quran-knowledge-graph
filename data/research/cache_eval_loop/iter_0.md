# iter_0 — baseline measurement

Date: 2026-05-27
Branch: `claude/cache-eval-loop-2026-05-27`
Cache file: `data/answer_cache.json` (worktree copy, identical to main HEAD `d650eba`)
Cache size: 1,612 entries / 90 MB / 1,607 with `embedding_m3`

## Summary

| Signal | Value |
|---|---|
| Shape A hard_pass | **51/57 (89.5%)** |
| Shape A cache_hits | 57/57 (100%) |
| Shape B any_hit | **14/15 (93.3%)** |
| Shape B avg top1 similarity | 0.726 |
| Shape B avg top1 answer length | 7,666 chars |
| Shape B avg top1 citation count | 23.47 |
| pytest | 209 passed, 1 skipped |

Shape A is the primary loop signal (deterministic, fast). Shape B is a programmatic proxy for cache-context lift quality; the held-out questions have empty asserts so there is no hard-pass measurement available.

## Shape A — per-bucket hard_pass

| Bucket | Hard-pass | Rate |
|---|---|---|
| STRUCTURED | 4/4 | 100.0% |
| BROAD | 20/21 | 95.2% |
| CONCRETE | 6/7 | 85.7% |
| ABSTRACT | 21/25 | 84.0% |

ABSTRACT is the weakest bucket. CONCRETE has a single named-entity (Lot) citation gap. BROAD has one Code-19-adjacent failure.

## Shape A — the 6 failures

All 6 have `similarity=1.000` (the question IS the cached question). Failures are content gaps in the cached answer, not retrieval misses.

| ID | Bucket | Failed assert | Cached question |
|---|---|---|---|
| `abstract-003` | ABSTRACT | substring `shukr` missing | "How does the Quran portray gratitude?" |
| `abstract-014` | ABSTRACT | substring `yaqeen` missing | "How does the Quran address doubt and certainty?" |
| `abstract-016` | ABSTRACT | cite `35:6` missing | "How does the Quran characterise Satan and the ways he misleads people?" |
| `abstract-017` | ABSTRACT | cite `2:26` missing | "What lessons does the Quran offer about being led astray (dalal)?" |
| `broad-012` | BROAD | cite `74:30` missing | "How does the Quran speak of its own miraculous nature?" |
| `concrete-004` | CONCRETE | cite `11:77` missing | "What befell Lot's people according to the Quran?" |

State file flagged the first 5 explicitly; `broad-012` (Code-19 anchor `74:30`) was newly surfaced. All 6 are small surgical edits — add the missing verse or word inside the existing cached answer body, re-cite, save back via `save_answer` (0.98 cosine dedupe overwrites).

## Shape B — the held-out signal

14/15 have `any_hit` at threshold 0.6. One CACHE_MISS:

- `structured-held-001`: **"What is the shortest surah in the Quran, and what is its message?"** — no entry exists. This is the single highest-leverage Shape-B fix.

The 4 lowest cache-quality hits (after the miss above):

| ID | top1_sim | cites | length | Notes |
|---|---|---|---|---|
| `concrete-held-002` | 0.604 | 13 | 7,090 | David (Dawud) — adjacent to Solomon/Job but not a tight match |
| `broad-held-002` | 0.667 | 14 | 6,187 | Ar-Rahman recurring lesson |
| `broad-held-003` | 0.674 | 22 | 10,749 | Solomon (Sulayman) |
| `concrete-held-001` | 0.674 | 22 | 5,494 | Thamud — people of |

All four are answerable from the graph; the cache just doesn't have these specific questions. Targets for new-entry additions in early iterations.

## Strategy for iter_1

Hit the 6 Shape A failures first — all are content gaps in entries that already exist, fixes are surgical (add 1 citation or 1 word), and they pull hard_pass from 89.5% → 100% in a single iteration if they all land cleanly.

Each fix workflow:
1. Verify the target verse via Cypher (`MATCH (v:Verse {verseId:'X:Y'}) RETURN v.text`)
2. Read the existing cached answer
3. Compose a replacement that integrates the missing citation/substring without losing the existing structure or citations
4. Verify 100% citation validity (every `[s:v]` in the new answer exists in the graph)
5. `save_answer(question, new_answer)` — dedupe overwrites

If all 6 land cleanly, iter_1 outcome = CLEAR_IMPROVEMENT (Shape A 89.5% → 100%). If 5/6 land, still CLEAR_IMPROVEMENT (≥2pp). Risk: a sloppy regeneration could drop existing citations from the cached answer, regressing other already-passing asserts. Mitigation: extract the existing citations list before composing and verify the new answer preserves them.

## Tool-assertion handling note

Shape A skips `tools_used_must_include` / `tools_used_must_not_include` asserts. The cached entry's stored `tools_used` reflects what tools were called when the entry was generated, not what a live agent would invoke now. Live-trajectory hard_pass against the cache is a different measurement; see state file's "tools (invoked-honest) 2/57" vs "tools (agent-equivalent) 47/57" split for the full picture. The 89.5% figure here is "content-quality hard_pass" — what the cached answer asserts on its own merits.
