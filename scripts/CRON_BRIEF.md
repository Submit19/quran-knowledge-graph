# Cron orchestrator brief

This file is read verbatim by each cron-fired subagent. The cron prompt just says "execute the brief in scripts/CRON_BRIEF.md" — keeps the cron job lean and lets us edit the brief without recreating the cron.

---

You are running ONE tick of the QKG ralph loop. You start with zero context. Read everything from disk. Be terse.

Working directory: `C:\Users\alika\Agent Teams\quran-graph-standalone`
Repo: https://github.com/Submit19/quran-knowledge-graph

## Context primer (read these FIRST, in order, briefly)

1. `CLAUDE_INDEX.md` — 75-line lean project index
2. `STATE_SNAPSHOT.md` — current state
3. `SESSION_LOG.md` top entry — last operator hand-off

If `CLAUDE_INDEX.md` doesn't exist, fall back to `CLAUDE.md`.

## Tool-use guidance

- Soft target: ≤30 tool calls per tick. Past 30, ask yourself "am I making real progress or spiraling on a fix-retry loop?" Spec-format failures (`NEEDS_CONTEXT` → `FAILED` → manual recovery) are the classic anti-pattern; if you see one, fix the spec ONCE and move on rather than retrying the same broken pattern.
- Hard cap: 40 tool calls. If you legitimately need more, your scope is too big — split the task in a proposal.

## Procedure

1. **Halt check.** If `data/RALPH_STOP` exists, exit silently with "halted by RALPH_STOP".

2. **Pull latest:** `git pull --rebase`.

3. **Decide cycle from `ralph_state.json` `tick_count`:**
   - tick_count % 12 == 0 → MAINTENANCE tick
   - else if tick_count % 2 == 0 → IMPL tick (proposal-review at start)
   - else → RESEARCH tick

4. **IMPL tick procedure:**

   **4a. Quick proposal review.** Read `data/proposed_tasks.yaml`. For each entry under `pending:`:
   - Decide APPROVE / REJECT / DEFER. APPROVE: append to `ralph_backlog.yaml` under `tasks:` (use `acceptance: file_min_bytes: { path, min }` — NEVER `value:`). Remove from pending. REJECT: move to `rejected:` with one-line `reason:`. DEFER: bump `seen_count`; auto-reject after 3 cycles.
   - Save `data/proposed_tasks.yaml` back. If anything changed: commit "review: proposals" first.
   - If `pending: []` (empty), skip this step entirely — don't burn tokens on a no-op read.

   **4b. IMPL work.** Pick highest-priority pending task in {agent_creative, cypher_analysis, cleanup} from `ralph_backlog.yaml` that's not done/quarantined.
   - cypher_analysis or cleanup: do the work directly. Local Neo4j: NEO4J_URI=neo4j://127.0.0.1:7687, user=neo4j, password=Bismillah19, database=quran. Then `python ralph_tick.py --task <id>`.
   - agent_creative: if description contains `[opus]`, spawn a NESTED general-purpose subagent with `model="opus"` for the deliverable. Else handle inline. Then `RALPH_AGENT_BACKEND=manual python ralph_tick.py --task <id>`.
   - **Spec format gotcha:** `cypher_analysis` tasks need either `query` or `script` field in their spec, plus `query_kind: python_script` if using a script. If a task fails twice with NEEDS_CONTEXT due to spec format, FIX THE SPEC in `ralph_backlog.yaml` and re-run — don't retry the broken spec.

5. **RESEARCH tick procedure:**
   a. Read `data/research_neo4j_crawl/neo4j_research_queue.yaml`. Pop ONE item from highest-priority non-empty source.
   b. If handler == "yt-transcript-skill": `python "C:\Users\alika\.claude\skills\yt-transcript-skill\scripts\fetch_transcript.py" <url> --output "data/research_neo4j_crawl/yt_<videoid>.md" --timestamps`. If 429/IPBlocked: re-add to queue and PICK A DIFFERENT SOURCE.
   c. Else (WebFetch): WebFetch the URL with a focused QKG-relevance prompt.
   d. Extract findings into the source's `findings_file` keyed by URL/ID. TL;DR + key takeaways + verdict.
   e. **If actionable: append to `data/proposed_tasks.yaml` under `pending:` (NOT directly to ralph_backlog.yaml).**
   f. Save the queue YAML back (popped item removed).
   g. Bump `ralph_state.json` tick_count by 1.

6. **MAINTENANCE tick (every 12th):** Dedupe / retire / re-rank across all backlogs. Run proposal review first. Commit "ralph maintenance: tick <N>".

7. **End-of-tick housekeeping:** `python scripts/tick_finalize.py` (runs state_snapshot.py + vault_update.py + MORNING_REPORT.md every 12 ticks).

8. **Commit:** single commit with deliverable + state JSON + backlog/queue YAMLs + STATE_SNAPSHOT.md + QKG Obsidian/* + MORNING_REPORT.md (if updated). Push.

## Stop conditions
- `data/RALPH_STOP` exists
- Same task fails 3x (check `state.attempts[task_id]`)
- All queues empty in permitted filters

## If you hit a session/rate cap
Abandon gracefully — no partial commit.

## Final reply format
```
Cycle: IMPL|RESEARCH|MAINTENANCE
Task: <id or "review-only" or "queue-emptied">
Status: <DONE|DONE_WITH_CONCERNS|FAILED|HALTED|RATE_LIMITED>
Commit: <short sha or "none">
```
