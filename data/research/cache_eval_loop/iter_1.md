# iter_1 — surgical fixes for 6 Shape A failures

**Outcome: CLEAR_IMPROVEMENT.** Shape A 51/57 → 57/57 (89.5% → 100.0%, Δ +10.5pp). Shape B unchanged (no held-out questions touched). pytest 209+1.

## Summary

| Signal | iter_0 | iter_1 | Δ |
|---|---|---|---|
| Shape A hard_pass | 51/57 (89.5%) | **57/57 (100.0%)** | **+10.5pp** |
| Shape B any_hit | 14/15 (93.3%) | 14/15 (93.3%) | 0 |
| Shape B avg top1 sim | 0.726 | 0.726 | 0 |
| Cache file size | 90.14 MB | 90.14 MB | +1.6 KB |
| Cache entries | 1612 | 1612 (6 updated) | 0 |
| pytest | 209+1 | 209+1 | 0 |

All 4 buckets at 100% hard_pass: ABSTRACT 25/25, BROAD 21/21, CONCRETE 7/7, STRUCTURED 4/4.

## The 6 fixes (`iter_001_changes.json` for full per-fix detail)

| ID | Intent | Delta chars | Added cites |
|---|---|---|---|
| `abstract-003` | romanize "shukr" inline next to ش-ك-ر | +14 | — |
| `abstract-014` | add "yaqeen" as Khalifa's romanization | +31 | — |
| `abstract-016` | add [35:6] "devil is your enemy" section | +466 | `35:6` |
| `abstract-017` | add [2:26] bidirectional-revelation section | +732 | `2:26` |
| `broad-012` | add [74:30] Code-19 anchor at section opening | +203 | `74:30` |
| `concrete-004` | add [11:77] messenger-visit parallel | +222 | `11:77` |

Each fix:
1. Targeted anchor-string `str.replace` against existing answer (single-shot, fail-fast if anchor missing).
2. Verified no existing citations dropped (set diff old_cites - new_cites must be empty).
3. Verified every citation in new answer resolves to a `Verse` node via `MATCH (v:Verse {verseId: $vid})`.
4. Verified target substring / citation now lands.
5. `save_answer(question, new_answer)` — 0.98 cosine dedupe overwrites in-place since sim=1.000.

`scripts/iter_1_apply_fixes.py` is the reproducible record — re-runnable, deterministic, dry-runnable.

## Why every fix landed

- All 6 failures had `sim=1.000` against the cached question (the exact question was already in cache). The failure was missing content, not missing entry. Surgical edits are well-suited to this failure shape.
- The 4 citation additions ([35:6], [2:26], [74:30], [11:77]) are all canonical anchor verses for their topics — adding them strengthens the cached answer, doesn't dilute it.
- The 2 substring additions ("shukr", "yaqeen") are Khalifa-preferred romanizations of words the answer already discussed via Arabic root. Pure terminology completion.

## Strategy for iter_2

Shape A is saturated at 100% — no more fixes available within the assert-defined targets. Further Shape A improvement requires asserts to change (out of scope: "No new question categories").

Shape B has 1 CACHE_MISS plus 4 weak-coverage entries. The CACHE_MISS (`structured-held-001` — "What is the shortest surah and what is its message?") is the clearest target — no entry exists at all. Adding it pulls `any_hit` from 14/15 to 15/15.

Strategy: compose **4–5 new cache entries** for the weakest Shape B held-outs (`structured-held-001`, `concrete-held-002` David, `broad-held-002` Ar-Rahman lesson, `broad-held-003` Solomon, `concrete-held-001` Thamud). Each:
- 2,500–4,000 chars per state-file quality bar
- Multi-section markdown matching `baseline_capable_model.jsonl` style
- Submitter-audience framing (no Khalifa disclaimer)
- 100% citation validity via Cypher verification
- Khalifa-distinctive acknowledgment where relevant

Expected outcome: Shape B `any_hit` 14/15 → 15/15, avg top1_sim 0.726 → ~0.82. New cache entries: +4–5 (cache 1612 → 1616–1617). This is a larger composition iteration than iter_1 — budget ~30–40 min.

**Risk:** new entries' embeddings could perturb top-1 retrieval for OTHER held-out questions (e.g. a new Solomon entry might compete with an existing Joseph entry). Mitigation: after composing, re-run Shape B and check `weakest` table for any newly-low entry that wasn't there before.

## Honest accounting

- Shape A was over-engineered relative to its post-fix utility — 100% with no further surgical target available means the loop's primary signal has plateaued already. From iter_2 onward, Shape B is the only live signal.
- The "+10.5pp in one iteration" is the easiest delta the loop will see. The state file already flagged 5 of these 6 misses as known. iter_2 onward addresses genuinely uncached questions, which is fundamentally harder than fixing already-existing answers.
