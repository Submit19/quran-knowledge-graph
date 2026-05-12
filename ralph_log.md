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
| 2026-05-07T13:18 | discover_new_followups | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-10T11:22 | from_neo4j_crawl_enable_slow_query_log | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T12:18 | from_neo4j_yt_router_agent | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-10T16:23 | from_neo4j_crawl_audit_indexes | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T16:23 | from_neo4j_crawl_audit_indexes | cypher_analysis | FAILED |  | wrote ralph_analysis_from_neo4j_crawl_audit_indexes.md / ACCEPTANCE FAILED: file_exists data/ralph_analysis_from_neo4j_crawl_audit_indexes.md=pass; file_min_byt |
| 2026-05-10T16:24 | from_neo4j_crawl_audit_indexes | cypher_analysis | DONE |  | wrote ralph_analysis_from_neo4j_crawl_audit_indexes.md |
| 2026-05-10T17:23 | from_neo4j_crawl_check_neo4j_version | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T17:23 | from_neo4j_crawl_check_neo4j_version | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T17:23 | from_neo4j_crawl_check_neo4j_version | cypher_analysis | NEEDS_CONTEXT |  |  / QUARANTINED after 3 attempts |
| 2026-05-11T00:00 | from_neo4j_crawl_check_neo4j_version | cypher_analysis | DONE |  | Neo4j 2026.02.2 Enterprise; no in-index pre-filter (3-arg proc only); SIMD via Lucene; quant=True all indexes |
| 2026-05-10T19:23 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T19:23 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T19:24 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | NEEDS_CONTEXT |  |  / QUARANTINED after 3 attempts |
| 2026-05-10T19:24 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-10T19:24 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | FAILED |  | wrote ralph_analysis_from_ai_graph_zeroentropy_cohere_reranker_ab.md / ACCEPTANCE FAILED: file_exists data/ralph_analysis_from_ai_graph_zeroentropy_cohere_reran |
| 2026-05-10T19:26 | from_ai_graph_zeroentropy_cohere_reranker_ab | cypher_analysis | DONE |  | wrote ralph_analysis_from_ai_graph_zeroentropy_cohere_reranker_ab.md |
| 2026-05-10T20:22 | from_ralph_yt_01_tokenize_claudemd | cleanup | DONE |  | [from-ralph-yt] Run CLAUDE.md through tiktoken (cl100k_base). Jeff's rule of thu / quality gate ok |
| 2026-05-10T22:22 | from_neo4j_crawl_trace_vector_index | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_neo4j_crawl_trace_vector_index.md (review before use) |
| 2026-05-11T02:22 | from_neo4j_crawl_adopt_graphrag_retrievers | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T04:22 | from_ai_graph_disable_reranker_baseline | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-11T04:23 | from_ai_graph_disable_reranker_baseline | cypher_analysis | NEEDS_CONTEXT |  | spec missing 'query' or 'script' |
| 2026-05-11T04:23 | from_ai_graph_disable_reranker_baseline | cypher_analysis | FAILED |  | wrote ralph_analysis_from_ai_graph_disable_reranker_baseline.md / ACCEPTANCE FAILED: file_exists data/ralph_analysis_from_ai_graph_disable_reranker_baseline.md= |
| 2026-05-11T05:21 | from_ai_graph_rag_triad_eval_metrics | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_ai_graph_rag_triad_eval_metrics.md (review before use) |
| 2026-05-11T07:22 | from_neo4j_yt_memory_05_reasoning_step | cleanup | DONE |  | [from-neo4j-yt] Insert (:ReasoningStep {turn_number, rationale}) between Reasoni / quality gate ok |
| 2026-05-11T12:50 | from_adaptive_routing_design | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T13:45 | from_research_finetune_bge_m3_qrcd | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T14:17 | from_neo4j_yt_mcp_tool_description_audit | cleanup | FAILED |  | [from-neo4j-yt][synthesis-promoted 2026-05-12] Audit and rewrite all 21 chat.py  / QUALITY GATE FAILED:  |
| 2026-05-11T14:18 | from_neo4j_yt_mcp_tool_description_audit | cleanup | FAILED |  | [from-neo4j-yt][synthesis-promoted 2026-05-12] Audit and rewrite all 21 chat.py  / QUALITY GATE FAILED:  |
| 2026-05-11T14:44 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_add_5_targeted_eval_questions.md (review before use) |
| 2026-05-11T15:45 | from_neo4j_crawl_single_shot_vector_traversal | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T16:14 | from_neo4j_yt_mcp_balanced_tool_grouping | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T17:20 | from_adaptive_routing_50q_bucketed_eval | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T17:20 | from_adaptive_routing_50q_bucketed_eval | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T18:17 | from_ai_graph_reflexion_pattern | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_ai_graph_reflexion_pattern.md (review before use) |
| 2026-05-11T18:45 | from_neo4j_crawl_arabic_fulltext_index | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_neo4j_crawl_arabic_fulltext_index.md (review before use) |
| 2026-05-11T19:46 | from_ai_graph_arabic_reranker_research | cypher_analysis | DONE_WITH_CONCERNS |  | manual mode — deliverable produced out-of-band; gate will validate |
| 2026-05-11T20:15 | from_neo4j_yt_memory_01_bitemporal_retrieved | cleanup | FAILED |  | [from-neo4j-yt] Add valid_from (ISO timestamp) and model_version string properti / QUALITY GATE FAILED:  |
| 2026-05-11T20:16 | from_neo4j_yt_memory_01_bitemporal_retrieved | cleanup | DONE |  | [from-neo4j-yt] Add valid_from (ISO timestamp) and model_version string properti |
| 2026-05-11T20:45 | from_neo4j_crawl_pagination_cursors | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_neo4j_crawl_pagination_cursors.md (review before use) |
| 2026-05-11T21:16 | from_ai_graph_lightrag_neo4j_spike | cypher_analysis | DONE_WITH_CONCERNS |  | manual mode — deliverable produced out-of-band; gate will validate |
| 2026-05-11T22:17 | from_adaptive_routing_2profile_spike | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_adaptive_routing_2profile_spike.md (review before use) |
| 2026-05-11T22:18 | from_adaptive_routing_2profile_spike | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_adaptive_routing_2profile_spike.md (review before use) |
| 2026-05-11T22:19 | from_adaptive_routing_2profile_spike | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_adaptive_routing_2profile_spike.md (review before use) |
| 2026-05-11T23:15 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-11T23:44 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_add_5_targeted_eval_questions.md (review before use) |
| 2026-05-12T00:44 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_add_5_targeted_eval_questions.md (review before use) |
| 2026-05-12T01:13 | add_5_targeted_eval_questions | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-12T02:17 | from_ralph_yt_03_audit_negative_prompts | cleanup | FAILED |  | [from-ralph-yt] Audit ralph_tick.py system prompt, CLAUDE.md, ralph_backlog.yaml / QUALITY GATE FAILED:  |
| 2026-05-12T02:45 | from_neo4j_yt_memory_03_consolidation_job | cypher_analysis | DONE_WITH_CONCERNS |  | manual mode — deliverable produced out-of-band; gate will validate |
| 2026-05-12T03:45 | from_ralph_yt_02_filter_test_output | cleanup | FAILED |  | [from-ralph-yt] Wrap eval_v1.py and Cypher smoke-test scripts with an output fil / QUALITY GATE FAILED:  |
| 2026-05-12T03:46 | from_ralph_yt_02_filter_test_output | cleanup | FAILED |  | [from-ralph-yt] Wrap eval_v1.py and Cypher smoke-test scripts with an output fil / QUALITY GATE FAILED:  |
| 2026-05-12T04:15 | from_neo4j_yt_mcp_graph_backed_registry | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_neo4j_yt_mcp_graph_backed_registry.md (review before use) |
| 2026-05-12T04:45 | from_neo4j_yt_sufficiency_gate | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_neo4j_yt_sufficiency_gate.md (review before use) |
| 2026-05-12T05:45 | from_blog_extend_reasoning_memory_confidence | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-12T06:17 | from_blog_same_as_dedup_concepts | cypher_analysis | DONE_WITH_CONCERNS |  | manual mode — deliverable produced out-of-band; gate will validate |
| 2026-05-12T07:16 | from_neo4j_yt_mcp_tool_description_audit | cleanup | FAILED |  | [from-neo4j-yt][synthesis-promoted 2026-05-12] Audit and rewrite all 21 chat.py  / QUALITY GATE FAILED: Address(('::1', 7687, 0, 0)) (reason [WinError 10061] No |
| 2026-05-12T08:46 | from_ai_graph_tool_error_audit | cleanup | FAILED |  | [from-ai-graph] Audit all 21 tools in chat.py for the 'tool failures ignored' pr / QUALITY GATE FAILED: Address(('::1', 7687, 0, 0)) (reason [WinError 10061] No |
| 2026-05-12T08:47 | from_ai_graph_tool_error_audit | cleanup | FAILED |  | [from-ai-graph] Audit all 21 tools in chat.py for the 'tool failures ignored' pr / QUALITY GATE FAILED: Address(('::1', 7687, 0, 0)) (reason [WinError 10061] No |
| 2026-05-12T09:45 | from_blog_stateful_ai_memory_path_convention | cleanup | FAILED |  | [from-research] Add structured `memory_path` property (e.g. sessions/<id>/traces / QUALITY GATE FAILED: Address(('::1', 7687, 0, 0)) (reason [WinError 10061] No |
| 2026-05-12T10:14 | from_neo4j_yt_memory_01_bitemporal_retrieved | cleanup | DONE |  | [from-neo4j-yt] Add valid_from (ISO timestamp) and model_version string properti |
| 2026-05-12T11:15 | from_blog_reasoning_memory_session_layer | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_blog_reasoning_memory_session_layer.md (review before use) |
| 2026-05-12T11:17 | from_blog_reasoning_memory_session_layer | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_blog_reasoning_memory_session_layer.md (review before use) |
| 2026-05-12T11:47 | from_blog_hyde_semantic_search_spike | agent_creative | DONE_WITH_CONCERNS |  | wrote ralph_agent_from_blog_hyde_semantic_search_spike.md (review before use) |
| 2026-05-12T11:48 | from_blog_hyde_semantic_search_spike | agent_creative | DONE_WITH_CONCERNS |  | manual backend — deliverable produced out-of-band; gate will validate |
| 2026-05-12T12:16 | share_minilm_across_modules | cleanup | FAILED |  | Share one all-MiniLM-L6-v2 instance across chat / reasoning_memory / answer_cach / QUALITY GATE FAILED: Address(('::1', 7687, 0, 0)) (reason [WinError 10061] No |
