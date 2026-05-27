# Running log — cache eval loop 2026-05-27

Append-only. One short paragraph per iteration. Patterns and dead-ends here, not full reports — those live in `iter_NNN.md`.

## iter_0 (baseline)

- **Shape A: 51/57 = 89.5%** hard_pass. 6 failures, all `sim=1.000` (cache content gaps, not retrieval misses): `abstract-003` (shukr), `abstract-014` (yaqeen), `abstract-016` (35:6), `abstract-017` (2:26), `broad-012` (74:30), `concrete-004` (11:77).
- **Shape B: 14/15 any_hit, avg top1_sim=0.726.** One CACHE_MISS (`structured-held-001` — "shortest surah"). Four weak-coverage held-outs: `concrete-held-002` (David), `broad-held-002` (Ar-Rahman), `broad-held-003` (Solomon), `concrete-held-001` (Thamud).
- **ABSTRACT is the weakest bucket (84%).** STRUCTURED is at 100%. BROAD has one straggler (Code-19 anchor missing). CONCRETE has one straggler (Lot citation missing).
- **Strategy for iter_1:** surgical regeneration of the 6 Shape A failures. All are entries-that-exist needing 1–2 character/citation additions. Expected outcome: Shape A 89.5% → 95–100%.
- **Risk to watch:** regression — a sloppy regeneration could drop existing citations and flip a passing entry to failing. Mitigation: extract existing citations before composing, verify preservation after.
- **Skipped asserts:** `tools_used_*` (cache-direct scoring can't measure agent invocation).
