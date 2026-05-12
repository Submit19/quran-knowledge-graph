# Cross-research synthesis — 2026-05-12 (tick 96 MAINT, 4th synthesis)

_Generated at MAINTENANCE tick 96. Covers IMPL ticks 91–95 since last synthesis
(ticks 84–90 synthesis). Sources: recent analysis files, backlog state, ADR-0037._

---

## TL;DR (5 bullets)

- **Backlog is now clean: 46 done, 25 pending, 0 quarantined.** Bulk-close at tick 95
  resolved 41 DONE_WITH_CONCERNS tasks that had valid deliverables but were never
  marked done in the YAML. Backlog health is the best it has ever been.
- **Tool description rewrite is complete (ADR-0026 implemented).** 6 of 21 chat.py
  tools were substantively improved: concept_search priority, Arabic hybrid primary,
  recall_similar_query first-call, run_cypher last-resort, semantic_search fallback
  label, search_keyword redirect. This directly reduces the abstract-query routing
  failures identified in the prior synthesis.
- **SAME_AS dedup work confirms ArabicRoot is clean; Concept layer gap is manageable.**
  3 cross-language pairs (iblis/satan, satan/devil, paradise/heaven) and 1 transliteration
  pair (haamaan/hamaan) are confirmed high-priority SAME_AS candidates. Porter-stem
  already handles English morphological variants — no redundant work needed.
- **Reasoning memory schema extension spec is ready (ADR-0037).** `thought` + `confidence`
  props on ToolCall/ReasoningStep are additive, zero-migration, and directly enable
  self-improvement signal mining. Implementation is next IMPL tick that picks
  a schema task.
- **Top 3 IMPL-unblocked tasks by impact:** `hand_grade_26_answers` (p88, manual,
  operator-only), `refresh_query_embedding_to_bge_m3` (p85, no blockers), and
  `qwen3_reranker_ab_qrcd` (p78, no blockers). The reranker A/B (Qwen3 vs bge-reranker)
  is the highest-ROI eval task available to the loop right now.

---

## Cross-cutting insights since last synthesis

1. **Tool description quality directly reduces abstract-query routing failures.**
   The audit (tick 95) found 6 of 21 tools lacked clear "USE FIRST" or "NEVER USE WHEN"
   guidance. The fixes are in. Cross-check: same-session synthesis finding #3 (tool
   descriptions are primary routing signal) is now implemented. Adaptive-routing design
   tasks (backlog p80) can proceed on a clean description foundation.

2. **Concept dedup scope is narrow and bounded.** 8 cross-language pairs + 3 proper-noun
   variants + 1 transliteration pair = ~12 high-priority SAME_AS edges. This is a
   2-hour IMPL task. The work will tighten concept_search recall for queries like
   "Satan" (won't retrieve "iblis" verses) and "Paradise" (won't retrieve "jannah"
   verses).

3. **Reasoning memory is approaching schema completeness.** Done: ReasoningStep node
   (ADR via tick 91), bitemporal RETRIEVED edges (backlog p75), QueryCluster
   consolidation spec (tick 83). Remaining: thought+confidence props (spec ready,
   ADR-0037 written this tick), trace_embedding migration (backlog pending).
   The memory schema is 3 tasks from being the full Context Graph pattern.

4. **The Qwen3-Reranker-0.6B A/B is the clearest quality win still pending.**
   Prior synthesis identified reranker harm on Arabic. The 2-profile gate (ADR-0032,
   tick 73) fixed BROAD queries. The remaining gap: Qwen3 is a drop-in swap for
   bge-reranker-v2-m3 at same parameter count (+8.8pt MTEB-R). Task `qwen3_reranker_ab_qrcd`
   (p78) is in backlog with no blockers and no pre-reqs. This is the loop's next
   highest-confidence quality lift.

5. **Research queue still has 80 yt_neo4j items — diminishing returns expected.**
   Prior synthesis finding #6 noted external research is producing more "validating"
   than "novel" findings. The yt_neo4j queue at 80 items will take ~40 RESEARCH
   ticks to drain at current 1–2 items/tick. With 4:1 IMPL:RESEARCH ratio that is
   ~200 ticks (~100h cron time). RECOMMEND: keep current ratio, do not accelerate.

---

## Backlog re-prioritization (delta only)

No priority changes warranted this tick — the prior synthesis already applied major
re-rankings and the intervening IMPL ticks executed them correctly. Confirming the
top 5 pending tasks are correctly sequenced:

| pri | id | note |
|----:|------|------|
| 88 | `hand_grade_26_answers` | operator-only; correctly highest |
| 85 | `refresh_query_embedding_to_bge_m3` | no blockers; enables hipporag re-run |
| 80 | `refresh_answer_cache_through_new_pipeline` | no blockers; straightforward |
| 78 | `qwen3_reranker_ab_qrcd` | no blockers; highest-ROI eval |
| 75 | `try_lower_max_tool_turns` | blocked on rerun_eval (DONE) — should be unblocked |

Action: `try_lower_max_tool_turns` lists `rerun_eval_against_current` as a blocker,
which is now DONE. This task is effectively unblocked — no yaml change needed as
blockers are checked against status at runtime, but note for operator: this task
is ready to run.

---

## New tasks surfaced

None this tick. Prior synthesis + intervening IMPL ticks have a healthy 25-task
backlog. Next synthesis is at tick 120.
