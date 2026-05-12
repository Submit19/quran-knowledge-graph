# QKG Obsidian Vault — Map of Content

The "MOC" (Map of Content) is the single entry point. Everything links from here.

## What this vault is

Persistent human-readable knowledge layer for the **Quran Knowledge Graph** project. Markdown notes + Obsidian wikilinks + native graph view = a queryable knowledge graph alongside our actual Neo4j Quran graph.

The repo it lives in: `C:\Users\alika\Agent Teams\quran-graph-standalone\`. This vault is at the repo root in `QKG Obsidian/`.

## Folder convention

| Folder | What goes here |
|--------|----------------|
| `research/` | One note per research finding. Tagged `#research/<topic>`. Linked from the matching `data/research_*.md` file in the repo. |
| `decisions/` | Architectural Decision Records (ADRs). One per major call ("use BGE-M3 over MiniLM", "skip ColBERT", "stay on local Neo4j"). |
| `architecture/` | Component diagrams, schema notes, system maps. Excalidraw-friendly. |
| `daily/` | Daily notes. End-of-day reflection — what shipped, what's queued, what's stuck. |
| `sessions/` | One note per Claude Code session (`session-2026-05-10.md` etc). At session end, append the work summary. New sessions read the most recent entry as their first action. |

Tag convention: `#research/<area>` — e.g. `#research/retrieval`, `#research/agent-memory`, `#research/neo4j-yt`.

## Top-level entry points

- [[Operator Quickstart]] — sit-down ritual, 2 minutes, then you're oriented
- [[CURRENT STATE]] — auto-generated state snapshot (overwritten by `scripts/state_snapshot.py`). Read this first when picking up context.
- [[MORNING REPORT]] — refreshed every 12 ticks (created by `scripts/tick_finalize.py`)

## Backfilled content (auto-refreshed by memory_hygiene.py)

### Decisions (ADRs) (36)
- [[decisions/0001-use-khalifa-translation]]
- [[decisions/0002-bge-m3-over-minilm]]
- [[decisions/0003-multilingual-reranker]]
- [[decisions/0004-skip-colbert]]
- [[decisions/0005-skip-aura-agent]]
- [[decisions/0006-local-neo4j]]
- [[decisions/0007-orchestrator-fresh-subagent]]
- [[decisions/0008-no-ralph-plugin]]
- [[decisions/0009-hand-rolled-retrievers]]
- [[decisions/0010-hipporag-ppr-negative]]
- [[decisions/0011-minicheck-nli-citation-verification]]
- [[decisions/0012-5-tier-memory-stack]]
- [[decisions/0013-cron-fresh-subagent-pattern]]
- [[decisions/0014-ralph-agent-backend-manual-mode]]
- [[decisions/0015-manual-cypher-analysis-task-mode]]
- [[decisions/0016-cron-prompt-file-based-brief]]
- [[decisions/0017-tool-use-soft-hard-caps]]
- [[decisions/0018-haiku-end-of-tick-prep]]
- [[decisions/0019-sonnet-pre-warming-for-opus-tasks]]
- [[decisions/0020-30min-cadence-max-20x-plan]]
- [[decisions/0021-4to1-impl-research-ratio]]
- [[decisions/0022-blocked-on-research-field]]
- [[decisions/0023-synthesis-sub-step-every-4th-maint]]
- [[decisions/0024-keep-reranker-adaptive-routing-not-global-disable]]
- [[decisions/0025-skip-phone-friendly-status-md]]
- [[decisions/0026-tool-descriptions-as-primary-routing-signal]]
- [[decisions/0027-8-tool-startup-set-3-discoverable-bundles]]
- [[decisions/0028-arabic-fulltext-routing-bm25-path]]
- [[decisions/0029-reflexion-pattern-for-weak-query-cluster]]
- [[decisions/0030-qwen3-reranker-0.6b-as-next-reranker-candidate]]
- [[decisions/0031-skip-lightrag-spike]]
- [[decisions/0032-2profile-adaptive-reranker-gate-broad-only]]
- [[decisions/0033-querycluster-batch-consolidation-greedy-cosine]]
- [[decisions/0034-positive-framing-for-loop-instructions]]
- [[decisions/0035-graph-backed-tool-registry]]
- [[decisions/0036-3-way-sufficiency-gate]]

### Architecture (9)
- [[architecture/agent-loop]]
- [[architecture/citation-verification]]
- [[architecture/data-pipeline]]
- [[architecture/graph-schema]]
- [[architecture/memory-stack]]
- [[architecture/overview]]
- [[architecture/ralph-loop]]
- [[architecture/reasoning-memory]]
- [[architecture/retrieval-pipeline]]

### Research (16)
- [[research/agent-memory-yt-extracts]]
- [[research/agentic-graphrag-yt-patterns]]
- [[research/agentic-patterns-neo4j]]
- [[research/ai-graph-ecosystem-extracts]]
- [[research/bge-m3-dense-vs-colbert]]
- [[research/cypher-perf-gds]]
- [[research/eval-qrcd-report]]
- [[research/hipporag-negative-result]]
- [[research/log]]
- [[research/mcp-tool-registry-patterns]]
- [[research/neo4j-crawl-all-proposals]]
- [[research/ralph-loop-best-practices]]
- [[research/research-2026-04-27-stack-alternatives]]
- [[research/research-2026-04-28-deep-dive]]
- [[research/synthesis-226-05-12]]
- [[research/vector-graphrag-neo4j-docs]]

### Sessions / milestones (8)
- [[sessions/session-2026-04-22-overnight-report]]
- [[sessions/session-2026-04-24-overnight-report-2]]
- [[sessions/session-2026-04-26-weekend-report]]
- [[sessions/session-2026-04-27-research-stack-alternatives]]
- [[sessions/session-2026-04-28-autonomous-run]]
- [[sessions/session-2026-04-28-research-deep-dive]]
- [[sessions/session-2026-05-07-eval-v1-v2]]
- [[sessions/session-2026-05-10]]

## Dataview queries (require the Dataview plugin)

If you've installed the Dataview plugin, these will auto-populate. Without it they show as code blocks (harmless).

````markdown
## Open research with priority ≥ 70

```dataview
TABLE priority, status, file.link
FROM "research"
WHERE status = "open" AND priority >= 70
SORT priority DESC
```

## Recent ADRs

```dataview
TABLE status, date, file.link
FROM "decisions"
SORT adr DESC
LIMIT 5
```

## Last 7 daily notes

```dataview
TABLE file.link
FROM "daily"
SORT file.name DESC
LIMIT 7
```
````

## Source documents (in the QKG repo, not in this vault)

These live outside the vault but the vault links into them:

- `CLAUDE.md` — project guidance (large, source of truth)
- `CLAUDE_INDEX.md` — 60-line lean version (loop's system context)
- `ralph_log.md` — append-only tick log + Codebase Patterns block
- `ralph_state.json` — operational state
- `ralph_backlog.yaml` / `data/research_backlog.yaml` — task + research queues
- `data/research_neo4j_crawl/` — the deep-crawl research artefacts
- `SESSION_LOG.md` — append-only session log (single-line entries)
- `STATE_SNAPSHOT.md` — auto-rolled "what does QKG look like NOW"

## The 5-tier memory model (for orientation)

```
TIER 5  ──  This vault (QKG Obsidian/) ◄── you are here
              human-readable knowledge graph, queryable via Dataview
TIER 4  ──  CLAUDE_INDEX.md + Codebase Patterns block
              compaction-resistant context — always in smart zone
TIER 3  ──  SESSION_LOG.md, STATE_SNAPSHOT.md, MORNING_REPORT.md
              session-bridge — survives this session ending
TIER 2  ──  ralph_state.json, backlog YAMLs, git commits
              operational state — already had this
TIER 1  ──  Live context (4-line tick summaries via subagent orchestrator)
              current session — minimized via fresh-subagent pattern
```

## Recommended Obsidian plugins (manually install via Settings → Community plugins)

| Plugin | Why |
|--------|-----|
| **Dataview** | Turn this vault into a queryable database. E.g. `LIST FROM "research" WHERE actionable = true SORT priority DESC`. |
| **Templater** | Standardized templates for new notes. See `architecture/_templates/` once we add it. |
| **Excalidraw** | Architecture sketches inline next to research. |
| **Daily notes** | Built-in. Configured to write to `daily/YYYY-MM-DD.md`. |
| **Obsidian Git** | Auto-commit the vault. Optional — Claude already commits the repo per tick. |

## How to use it as a session-start ritual

When you sit down to work on QKG (or when a fresh Claude Code session starts):

1. Read `STATE_SNAPSHOT.md` (if exists) — the auto-rolled summary.
2. Open the most recent `sessions/session-YYYY-MM-DD.md` — the previous session's tail.
3. Skim the top 5 entries in the [[Research Index]] for anything pending.
4. Glance at the Codebase Patterns block in `ralph_log.md` for durable advice.

Total context-loading time: ~2 minutes. Far cheaper than re-reading 100 commits.
