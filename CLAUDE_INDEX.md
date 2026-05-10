# QKG — index for AI agents

Lean replacement for CLAUDE.md as the loop's system context. Per Jeff Huntley's
Ralph rule: ~60 lines, hyperlinks not full content. Read these files when needed.

## What QKG is

Neo4j-backed agentic Quran retrieval. 6,234 verses (Khalifa English + Hafs Arabic).
Anthropic API agentic loop with 21 tools. Hybrid retrieval (BM25 + BGE-M3 + RRF +
cross-encoder rerank). Citation verification (NLI + MiniCheck). 3D verse graph in
the frontend. **NOT using `neo4j-graphrag-python`** (everything hand-rolled with raw
neo4j driver). Local Neo4j Desktop, password in `.env`.

## Spec files (read on demand)

- `CLAUDE.md` — full project guidance (large)
- `STATE_SNAPSHOT.md` — current state (auto-generated, read first)
- `SESSION_LOG.md` — hand-offs between sessions (top entry = most recent)
- `QKG Obsidian/MOC.md` — knowledge vault entry point
- `ARCHITECTURE.md` — end-to-end Mermaid diagrams
- `pipeline_config.yaml` — tunables

## Code map

- `chat.py` — 21 agentic tools + dispatch + tool-call cache
- `app_free.py` — FastAPI server :8085 (recommended), bridges sync agent loop to SSE
- `retrieval_gate.py` — cross-encoder rerank (`BAAI/bge-reranker-v2-m3`)
- `citation_verifier.py` — NLI + MiniCheck, atomic claim decomposition
- `reasoning_memory.py` — writes `(:Query)-[:TRIGGERED]->(:ReasoningTrace)-[:HAS_STEP]->(:ToolCall)-[:RETRIEVED]->(:Verse)` per chat
- `ref_resolver.py` — citation NER ([2:255], Surah X verse Y, Arabic refs)
- `answer_cache.py` — 1500+ entry cache, 0.98 cosine dedupe
- `ralph_loop.py` / `ralph_run.py` / `ralph_tick.py` — overnight self-improvement loop

## Loop architecture

Cron `7 * * * *` fires the orchestrator prompt → spawns ONE fresh general-purpose
subagent per tick → subagent reads state from disk, picks one task, does the work,
runs `ralph_tick.py`, commits + pushes, returns 4-line summary. Halt with
`data/RALPH_STOP`. Pacing: `--max-calls-per-day`, `--min-api-gap-sec` in `ralph_run.py`.

Tick alternation by `state.tick_count % 2`: even → IMPL, odd → RESEARCH. Research
ticks pop from `data/research_neo4j_crawl/neo4j_research_queue.yaml` (5 sources, ~111 items).

Manual mode: `RALPH_AGENT_BACKEND=manual python ralph_tick.py --task <id>` — Opus
operator does the work out-of-band; gate validates against acceptance criteria.

## Key envs

`SEMANTIC_SEARCH_INDEX=verse_embedding_m3` (BGE-M3 EN, recommended).
`RERANKER_MODEL=BAAI/bge-reranker-v2-m3`. `NEO4J_DATABASE=quran`.
`RALPH_AGENT_BACKEND=openrouter|manual`. `TOOL_CACHE_TTL_SEC=30`.

## Critical decisions made (full ADRs in `QKG Obsidian/decisions/`)

- BGE-M3 over MiniLM (5× MAP@10 lift on QRCD)
- Multilingual reranker over English-only (32-pt hit@10 lift on Arabic)
- SKIP ColBERT mode (only +1.2 nDCG@10; cross-encoder already late-interaction-like)
- SKIP Aura Agent migration (locks to Gemini + OpenAI/Google embeddings — incompatible with BGE-M3)
- KEEP local Neo4j (vs Aura/VPS); good enough for solo dev with PC on overnight
- Orchestrator + fresh-subagent pattern over plain cron-into-session (avoids context fall-off)

## Active research artefacts

`data/research_neo4j_crawl/INDEX.md` — entry point. 4 deep-crawl docs (vector,
agentic, perf, AI graph) + 12 YT extracts (06a/b/c) + Ralph YT extract (05). Findings
that matter live as `from_neo4j_crawl_*` / `from_neo4j_yt_*` / `from_research_*`
tasks in `ralph_backlog.yaml`.

## Operator rituals

Session start: `python scripts/state_snapshot.py` → read STATE_SNAPSHOT.md → read
top of SESSION_LOG.md → check `git log --since="1 week ago" --oneline`.

Session end: append a block to SESSION_LOG.md with shipped/queued/decisions/tip.
Optionally write a longer reflection in `QKG Obsidian/sessions/session-YYYY-MM-DD.md`.
