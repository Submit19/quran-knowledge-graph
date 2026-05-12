# Cross-research synthesis — 2026-05-13 (tick 120 MAINT, 5th synthesis)

_Generated at MAINTENANCE tick 120. Covers IMPL ticks 97–119 since last synthesis
(tick 96 MAINT synthesis). Sources: analysis files from ticks 97-119, ADR-0038 through
ADR-0044, recent YT research files, and the tick 96 synthesis baseline._

---

## TL;DR (5 bullets)

- **Tool robustness is now end-to-end.** Pre-execution validation (ADR-0045, tick 119)
  + post-execution structured errors (ADR-0038, tick 99) close the full silent-failure
  loop. 5 tools now reject invalid args before any Cypher fires. This is the most
  impactful reliability fix since the tool description rewrite.
- **Eval infrastructure is clean and canonical.** `eval_common.py` (tick 115) eliminates
  the `recall_at_k 0 vs 0.0` drift that was producing false metric divergence across
  the 5 eval scripts. All future QRCD runs will read from a single shared module.
- **Reranker A/B experiments are unblocked but still unmeasured.** Both the Cohere
  reranker design (ADR-0043) and Qwen3-Reranker-0.6B plan (ADR-0030, task p78) are
  fully specced. Neither has been executed. The reranker is still the highest-leverage
  pending quality win.
- **Architecture exploration is producing design docs faster than implementation.**
  Ticks 97-119 shipped 8+ DONE_WITH_CONCERNS design docs (parallel worktrees, session
  layer, HyDE spike, sufficiency gate, memory consolidation, Cohere reranker, adaptive
  routing profiles). These are valuable specs, but implementation throughput is lagging.
  The backlog has 15 pending tasks as of tick 120, many of them design->impl follow-ons.
- **Top operator-only blocker remains.** `hand_grade_26_answers` (p88) and
  `refresh_query_embedding_to_bge_m3` (p85) have been at the top of the backlog since
  tick 96. Neither can proceed without the operator. Loop cannot help here.

---

## Cross-cutting insights since last synthesis

1. **Tool validation + structured errors form a complete defence pair.**
   The combination of `from_ai_graph_tool_error_audit` (post-execution) and
   `from_blog_tool_input_validation` (pre-execution) closes the full tool-failure
   signal gap identified in Layer 4 Production Gotchas. The agent now receives
   structured `{error, reason, valid_range}` at both layers — before and after
   Cypher fires. This eliminates the silent-retry anti-pattern on hallucinated values.
   Cross-check: ADR-0038 + ADR-0045 are the paired decisions.

2. **Eval metric drift is a silent quality killer.**
   The `recall_at_k 0 vs 0.0` drift in the 5 eval scripts (found during tick 115
   extraction) was causing false divergence between eval runs on the same data. This
   is fixed in `eval_common.py`. Going forward, all QRCD eval scripts share a single
   canonical module. Any future eval helper drift will be caught at the module level.

3. **The reranker slot is still the highest-ROI pending change.**
   Synthesis #4 (tick 96) identified this; synthesis #5 confirms it is still true.
   `qwen3_reranker_ab_qrcd` (p78) has no blockers. The Cohere reranker design
   is also ready (ADR-0043). The loop should prioritise these in the next IMPL window.
   Note: the 2-profile gate (ADR-0032) is deployed — BROAD queries already skip the
   reranker. The next step is validating Qwen3 as a drop-in improvement for the
   remaining profiles.

4. **Design-doc throughput is high; implementation throughput is lower.**
   Ticks 97-119 produced ~8 DONE_WITH_CONCERNS deliverables — nearly all design docs
   or specs rather than live code changes. This is expected for the current IMPL mix
   (agent_creative tasks dominate). The main risk is spec-staleness: if design docs
   age >10 ticks without implementation, they should be reviewed for relevance before
   executing. Currently at-risk: HyDE spike (5 ticks old), session layer (5 ticks old),
   sufficiency gate (20+ ticks old).

5. **Parallel worktree architecture is designed but deferred (ADR-0044).**
   The spike confirmed the pattern is viable with shard files + .gitattributes union
   driver, but Neo4j write-conflict resolution is unresolved. This remains a 2-4×
   throughput lever when the operator approves the write isolation strategy.

6. **Memory hygiene arch_drift_spotcheck has a Windows codec bug.**
   The `memory_hygiene.py` `arch_drift_spotcheck` fails with a `charmap` codec error
   when writing Unicode arrows (→) to a file opened without explicit `encoding='utf-8'`.
   All other hygiene steps complete cleanly. This should be patched in a cleanup tick.

---

## Backlog re-prioritization (delta only)

One change warranted: bump `cypher_retry_metric` (p60) → p65 given the parallel
worktree design doc explicitly mentions Cypher retry as an open issue in its risk
register. Otherwise, top-5 ordering is unchanged:

| pri (old) | pri (new) | id | note |
|---:|---:|---|---|
| 88 | 88 | `hand_grade_26_answers` | operator-only; highest |
| 85 | 85 | `refresh_query_embedding_to_bge_m3` | operator-only; enables hipporag re-run |
| 80 | 80 | `refresh_answer_cache_through_new_pipeline` | no blockers |
| 78 | 78 | `qwen3_reranker_ab_qrcd` | no blockers; highest-ROI eval |
| 75 | 75 | `try_lower_max_tool_turns` | unblocked since tick 96 |

---

## New tasks surfaced

1. **Fix `memory_hygiene.py` arch_drift_spotcheck codec bug** — open Unicode file
   with `encoding='utf-8'` in `arch_drift_spotcheck()`. Low-complexity cleanup task.
   Suggested: type `cleanup`, priority 40.

2. **Implement Qwen3-Reranker-0.6B A/B eval** (`qwen3_reranker_ab_qrcd`, p78) —
   already in backlog. No new task needed; flagging as overdue per synthesis signal.

---

_Next synthesis at tick 144._
