# Ralph Loop — tick log

## Codebase Patterns
_Consolidated learnings from prior ticks. Append, don't replace.
 A pattern goes here when it's general/reusable enough that future
 ticks (and future humans) should know it. Keep entries terse._

<!-- PATTERNS:START -->
<!-- PATTERNS:END -->

## Tick history

| ts | task_id | type | status | metric Δ | notes |
|----|---------|------|--------|----------|-------|
|----|---------|------|--------|----------|-------|
| 2026-05-07T11:48 | rerun_eval_track_per_question_delta | cypher_analysis | failed |  | ", line 293, in load     return loads(fp.read(),                  ^^^^^^^^^   File "C:\Program Files\Python312\Lib\encodings\cp1252.py", line 23, in decode      |
| 2026-05-07T11:49 | rerun_eval_track_per_question_delta | cypher_analysis | success |  | wrote ralph_analysis_rerun_eval_track_per_question_delta.md |
| 2026-05-07T12:06 | rerun_eval_track_per_question_delta | cypher_analysis | DONE |  | wrote ralph_analysis_rerun_eval_track_per_question_delta.md |
| 2026-05-07T12:07 | add_5_targeted_eval_questions | agent_creative | NEEDS_CONTEXT |  | OPENROUTER_API_KEY not set |
| 2026-05-07T12:07 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_add_5_targeted_eval_questions.md (review before use) |
| 2026-05-07T12:37 | rerun_eval_track_per_question_delta | cypher_analysis | DONE |  | wrote ralph_analysis_rerun_eval_track_per_question_delta.md |
| 2026-05-07T12:50 | measure_per_tool_latency | cypher_analysis | DONE |  | wrote ralph_analysis_measure_per_tool_latency.md |
| 2026-05-07T12:51 | measure_cache_hit_rate | cypher_analysis | DONE |  | wrote ralph_analysis_measure_cache_hit_rate.md |
| 2026-05-07T12:51 | propose_speed_tunings | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_propose_speed_tunings.md (review before use) |
| 2026-05-07T12:52 | propose_streaming_progress_indicator | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_propose_streaming_progress_indicator.md (review before use) |
| 2026-05-07T12:53 | measure_reranker_speed_vs_quality | cleanup | DONE |  | Run eval twice — once with reranker on, once with RERANK_DISABLED=1 — compare ti |
| 2026-05-07T12:56 | propose_citation_tooltip_v2 | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_propose_citation_tooltip_v2.md (review before use) |
| 2026-05-07T12:57 | analyze_retrieved_edges_top_per_tool | cypher_analysis | DONE |  | wrote ralph_analysis_analyze_retrieved_edges_top_per_tool.md |
| 2026-05-07T12:57 | propose_session_memory_ux | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_propose_session_memory_ux.md (review before use) |
| 2026-05-07T13:00 | surface_underperforming_questions | cypher_analysis | DONE |  | wrote ralph_analysis_surface_underperforming_questions.md |
| 2026-05-07T13:00 | propose_search_bar_autocomplete | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_propose_search_bar_autocomplete.md (review before use) |
| 2026-05-07T13:02 | surface_retrieval_noise | cypher_analysis | DONE |  | wrote ralph_analysis_surface_retrieval_noise.md |
| 2026-05-07T13:02 | discover_new_followups | agent_creative | FAILED |  | wrote ralph_agent_discover_new_followups.md (review before use) / ACCEPTANCE FAILED: file_exists data/ralph_proposed_tasks.yaml=FAIL; file_min_bytes data/ralph_ |
