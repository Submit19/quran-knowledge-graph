# Operator Quickstart

You're sitting down to work on QKG. **Read this first.** Two minutes, then you're oriented.

## 1. Where the truth lives

| Question | Answer |
|----------|--------|
| What does QKG look like RIGHT NOW? | [[CURRENT STATE]] (mirror of `STATE_SNAPSHOT.md`) |
| What did the last session actually do? | Top entry of `repo://SESSION_LOG.md` and most recent file in [[sessions/]] |
| Why was that decision made? | [[decisions/]] folder, ranked by `adr` number |
| What's the current architecture? | [[architecture/overview]] |
| What research is in flight? | `data/research_neo4j_crawl/INDEX.md` and Dataview query in [[Research Index]] (if you have Dataview installed) |

## 2. Is the loop running?

Open Claude Code. In the active session, type `CronList` (or check that an hourly job ID like `d21fe275` is alive).

If it isn't:
```
/loop 1h <orchestrator prompt>
```
The orchestrator prompt body lives in your prior session's transcript. If lost: read `CLAUDE_INDEX.md` § "Loop architecture" — re-derive from there.

## 3. Halt the loop

Create the marker file:
```bash
touch data/RALPH_STOP
```
Next tick will exit silently. Remove the file to resume.

## 4. Manual tick (when you want to drive)

```bash
# IMPL tick (does the work yourself, then runs the gate)
RALPH_AGENT_BACKEND=manual python ralph_tick.py --task <task_id>

# RESEARCH tick (just delegate to a fresh subagent in your active CC session)
# — pop top item from data/research_neo4j_crawl/neo4j_research_queue.yaml,
#   spawn an Agent with the brief, write findings, commit
```

## 5. End-of-session ritual (when you stop working)

```bash
python scripts/tick_finalize.py     # refreshes STATE_SNAPSHOT + vault daily note
```

Then append a block to `repo://SESSION_LOG.md` with: shipped, queued, decisions, tip-for-next-session. Optionally write a longer reflection in [[sessions/]] dated today.

## 6. New decision? Write an ADR.

```bash
# Find the next ADR number
ls "QKG Obsidian/decisions/" | tail -3
```

Copy an existing ADR as a template, increment the number, fill in Context/Decision/Consequences/Cross-references.

## 7. Where the loop's tick logs live

- Per-tick row: `ralph_log.md` (markdown table)
- Full state: `ralph_state.json`
- Codebase Patterns block (durable lessons): inside `ralph_log.md` between `<!-- PATTERNS:START -->` markers

## 8. Backups

If anything goes catastrophically wrong:
- Tag: `git reset --hard backup-pre-ralph-chain-2026-05-08`
- Sibling clone: `..\quran-graph-standalone-backup-2026-05-08\`
- Per-tick atomic commits = `git revert <sha>` undoes one tick cleanly

## 9. Don't accidentally commit

`.gitignore` already excludes:
- `.vault_update_state.json` (per-machine vault state)
- `QKG Obsidian/.obsidian/workspace.json` (per-user vault layout)
- `.env` (Neo4j password lives here)
- `data/answer_cache.json` (regenerable, large)

If you find yourself running `git add -A`, double-check the diff first.

---

**Backlinks:** [[MOC]] · [[CURRENT STATE]]
