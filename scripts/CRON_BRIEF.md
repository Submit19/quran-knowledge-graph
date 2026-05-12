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

Prefer `CLAUDE_INDEX.md`; if absent, read `CLAUDE.md` instead.

## Tool-use guidance

- Soft target: ≤35 tool calls per tick. Past 35, ask yourself "am I making real progress or spiraling on a fix-retry loop?" Spec-format failures (`NEEDS_CONTEXT` → `FAILED` → manual recovery) are the classic anti-pattern; if you see one, fix the spec ONCE and move on rather than retrying the same broken pattern.
- Hard cap: 50 tool calls. If you legitimately need more, your scope is too big — split the task in a proposal.

## Procedure

1. **Halt check.** If `data/RALPH_STOP` exists, exit silently with "halted by RALPH_STOP".

2. **Sync with GitHub:** `git pull --rebase && git push`. The push is a safety net — if the prior tick committed locally but failed to push (transient network/auth), this flushes it. Idempotent when in sync (no-op).

3. **Decide cycle from `ralph_state.json` `tick_count`:**
   - tick_count % 6 == 0 → MAINTENANCE tick (every 6 fires)
   - else if tick_count % 3 == 0 → RESEARCH tick (1 in 3 — was 1 in 2; foundational research is done, biasing toward IMPL throughput)
   - else → IMPL tick (proposal-review at start)

   Resulting ratio across 12 ticks: 2 MAINT + 2 RESEARCH + 8 IMPL = **4:1 IMPL:RESEARCH**. Re-tune if research backlog grows past 40 items (drop to % 2) or empties below 5 (raise to % 4).

4. **IMPL tick procedure:**

   **4a. Quick proposal review.** Read `data/proposed_tasks.yaml`. For each entry under `pending:`:
   - **Use `haiku_notes` if present.** Each pending entry should have a `haiku_notes` block written by `scripts/haiku_prep.py` at the previous tick's end: `{classification, duplicate_of, relates_to, note}`. Haiku's classification is a hint — verify with your own check (it shortcuts discovery but treat as a starting point, not a final verdict).
     - `classification: actionable` → likely APPROVE (still verify priority/spec format).
     - `classification: duplicate` with `duplicate_of: <id>` → likely REJECT with that reason.
     - `classification: maybe_subsumed` → check `relates_to`; if subsumed, REJECT; if synergistic, APPROVE.
     - `classification: obvious_reject` → REJECT with the `note` as the reason.
   - APPROVE: append to `ralph_backlog.yaml` under `tasks:` (use `acceptance: file_min_bytes: { path, min }` — always use `file_min_bytes`, always use `file_min_bytes` over `value:`). Remove from pending. REJECT: move to `rejected:` with one-line `reason:`. DEFER: bump `seen_count`; auto-reject after 3 cycles.
   - Save `data/proposed_tasks.yaml` back. If anything changed: commit "review: proposals" first.
   - When `pending: []` (empty), proceed directly to step 4b to conserve tokens.

   **4b. IMPL work.** Pick highest-priority pending task in {agent_creative, cypher_analysis, cleanup} from `ralph_backlog.yaml` with status outside {done, quarantined}.
   - **Honor `blocked_on_research:` fields.** If a candidate task has a `blocked_on_research: [<topic_id>, ...]` field, check each listed topic. If ANY topic is still status: open in `data/research_backlog.yaml` OR present in any source queue of `data/research_neo4j_crawl/neo4j_research_queue.yaml`, **defer the task** and select the next-highest unblocked one. Log the deferral in your reply summary so the operator knows.
   - cypher_analysis or cleanup: do the work directly. Local Neo4j: NEO4J_URI=neo4j://127.0.0.1:7687, user=neo4j, password=Bismillah19, database=quran. Then `python ralph_tick.py --task <id>`.
   - agent_creative: if description contains `[opus]`, spawn a NESTED general-purpose subagent with `model="opus"` for the deliverable.
     - **Check for a pre-warmed plan at `data/sonnet_drafts/<task_id>.md`** before spawning Opus. If present, INCLUDE its full text in the Opus subagent's prompt as "Pre-warmed implementation plan (use as starting point, verify before executing)". This saves Opus tokens by skipping cold discovery.
     - Else handle inline. Then `RALPH_AGENT_BACKEND=manual python ralph_tick.py --task <id>`.
   - **Spec format gotcha:** `cypher_analysis` tasks need either `query` or `script` field in their spec, plus `query_kind: python_script` if using a script. If a task fails twice with NEEDS_CONTEXT due to spec format, FIX THE SPEC in `ralph_backlog.yaml` once and then re-run — each retry requires a spec change to make progress.

5. **RESEARCH tick procedure:**
   a. Read `data/research_neo4j_crawl/neo4j_research_queue.yaml`. Pop **up to 3 items** from the highest-priority non-empty source, provided all items come from the same source AND the handler is WebFetch (yt-transcript-skill handler: cap at 1 item due to rate limits).
      - If only 1 item exists in the top source, pop 1. If 2-3, pop 2-3. Default to 2 if uncertain.
      - Single-item processing is fine — batch items only when they are homogeneous and high-quality.
   b. For each popped item:
      - If handler == "yt-transcript-skill": `python "C:\Users\alika\.claude\skills\yt-transcript-skill\scripts\fetch_transcript.py" <url> --output "data/research_neo4j_crawl/yt_<videoid>.md" --timestamps`. If 429/IPBlocked: re-add to queue and end popping for this tick.
      - Else (WebFetch): **Check `data/research_cache/` first** — Haiku may have pre-fetched. Slug = md5(url)[:12], paths `<slug>.html` + `<slug>.meta.json`. If cache hit, read the HTML locally; otherwise WebFetch.
   c. Extract findings into the source's `findings_file` keyed by URL/ID (one section per item). TL;DR + key takeaways + verdict.
   d. **For each actionable finding: append to `data/proposed_tasks.yaml` under `pending:` (the gate in `data/proposed_tasks.yaml` is the mandatory staging step before any entry reaches `ralph_backlog.yaml`).**
   e. Save the queue YAML back with all popped items removed.
   f. Bump `ralph_state.json` tick_count by 1 (single bump, regardless of items processed).

6. **MAINTENANCE tick (every 6th):** Dedupe / retire / re-rank across all backlogs. Run proposal review first. Commit "ralph maintenance: tick <N>".
   - **Memory hygiene (every MAINT tick).** Run `python scripts/memory_hygiene.py` — handles all of the following automatically:
     - PATTERN promotion: scan `ralph_log.md` for `PATTERN:` lines in recent tick notes, dedupe + append to Codebase Patterns block.
     - SESSION_LOG drift: if top entry is >24h old AND >5 commits landed, Haiku writes a rolling auto-entry.
     - MOC refresh: regenerate the "Backfilled content" section from current vault file inventory (catches new ADRs / architecture / research notes).
     - Architecture drift spot-check (every 4th MAINT tick / every 24th overall): Haiku audits 2 random `architecture/` notes vs underlying source files, flags substantive drift to `data/memory_drift.md`.
   - **ADR-drift detection (every MAINT tick).** Run `git log --since="3 days ago" --oneline` and scan for "decision-class" commits (loop/architecture/agentic/eval changes with strategic implications — not pure bugfixes or research ticks). For each such commit, check whether a corresponding ADR exists in `QKG Obsidian/decisions/`. If not, spawn a Haiku subagent to write one using the existing 0001-0025 Nygard template. Commit ADRs alongside the maintenance commit.
   - **Every 4th MAINT tick (= every 24th tick overall, ~12h)** also do a **SYNTHESIS** sub-step: read all `data/research_neo4j_crawl/*.md` files modified since the last synthesis + new entries in `data/proposed_tasks.yaml` + recent `data/ralph_analysis_*.md`. Produce a cross-cutting insights doc at `data/research_synthesis_<date>.md`. If insights suggest re-prioritizing pending tasks, apply the changes (with one-line reason in the commit message).

7. **End-of-tick housekeeping:** `python scripts/tick_finalize.py` (runs state_snapshot.py + vault_update.py + MORNING_REPORT.md every 12 ticks).

8. **Commit:** single commit with deliverable + state JSON + backlog/queue YAMLs + STATE_SNAPSHOT.md + QKG Obsidian/* + MORNING_REPORT.md (if updated). Push.

## Stop conditions
- `data/RALPH_STOP` exists
- Same task fails 3x (check `state.attempts[task_id]`)
- All queues empty in permitted filters

## If you hit a session/rate cap
Exit cleanly — commit only after a complete, coherent unit of work lands.

## Final reply format
```
Cycle: IMPL|RESEARCH|MAINTENANCE
Task: <id or "review-only" or "queue-emptied">
Status: <DONE|DONE_WITH_CONCERNS|FAILED|HALTED|RATE_LIMITED>
Commit: <short sha or "none">
```
