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

- [[CURRENT STATE]] — auto-generated state snapshot (overwritten by `scripts/state_snapshot.py`). Read this first when picking up context.
- [[Decisions Index]] — ranked decision log
- [[Research Index]] — all research notes by tag
- [[Open Questions]] — known unknowns + speculation

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
