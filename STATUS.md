# QKG — Status

_Updated 2026-05-11 12:33 UTC — auto by `scripts/state_snapshot.py`_

## Loop
- Tick **50** | last `2026-05-11T20:30`
- In progress: **_idle_**
- 24h API calls: 2

## Last 5 ticks

- ✓ `from_neo4j_yt_memory_05_reasoning_step` (DONE, 2026-05-11T07:22)
- ⚠ `from_ai_graph_rag_triad_eval_metrics` (DONE_WITH_CONCERNS, 2026-05-11T05:22)
- ✓ `from_ai_graph_disable_reranker_baseline` (DONE, 2026-05-11T04:24)
- ✗ `from_ai_graph_disable_reranker_baseline` (FAILED, 2026-05-11T04:23)
- ? `from_ai_graph_disable_reranker_baseline` (NEEDS_CONTEXT, 2026-05-11T04:23)

## Recent commits

```
cfe2336 loop: Max 20x optimization — 30min cadence, faster MAINT, batched research, Sonnet pre-warming
e68169e research tick: yt_priority/kQu5pWKS8GA — 7 Levels of Claude Code & RAG — validating, no new tasks; QKG already at Level 6-7
53cd6fd loop: end-of-tick Haiku prep (validate + precache + classify proposals)
a6bdcf6 loop: ship 3 optimizations (cron brief→file, soft cap 30, manual cypher_analysis)
ca48104 queue 3 adaptive-routing tasks for orchestrator review
3e5a204 Revert "app_free: switch primary inference to OpenRouter (gpt-oss-120b:free)"
408a674 app_free: switch primary inference to OpenRouter (gpt-oss-120b:free)
d3c9cbe ralph maintenance: tick 48 — dedup, retire, re-rank
```

## Top 5 pending tasks

- **95** `rerun_eval_against_current` (eval)
- **88** `hand_grade_26_answers` (manual)
- **85** `refresh_query_embedding_to_bge_m3` (embed_op)
- **80** `refresh_answer_cache_through_new_pipeline` (cache_op)
- **78** `from_neo4j_crawl_single_shot_vector_traversal` (agent_creative) 🧠 ⭐

## Backlog health

- **39** pending • **25** done • **0** quarantined
- Research queue: **21** items across 6 sources
- Open research topics: **51**

## Files worth opening

- [📊 MORNING_REPORT.md](MORNING_REPORT.md) — refreshed every 6 ticks
- [📋 STATE_SNAPSHOT.md](STATE_SNAPSHOT.md) — full detail view
- [📝 SESSION_LOG.md](SESSION_LOG.md) — operator hand-offs between sessions
- [📚 ralph_backlog.yaml](ralph_backlog.yaml) — task queue
- [📥 data/proposed_tasks.yaml](data/proposed_tasks.yaml) — pending review (Haiku pre-annotated)
- [🧠 data/sonnet_drafts/](data/sonnet_drafts/) — Opus pre-warmed plans
- [🗒️ QKG Obsidian/](QKG%20Obsidian/) — knowledge vault (MOC.md entry)

_Tap any link to open in GitHub. Use the file watcher on your phone for live updates._
