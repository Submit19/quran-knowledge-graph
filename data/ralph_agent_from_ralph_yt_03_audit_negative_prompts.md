# from_ralph_yt_03_audit_negative_prompts

## Audit summary

Files audited:
- scripts/CRON_BRIEF.md
- ralph_loop.py (system prompt + LOG_HEADER constant)
- CLAUDE.md
- ralph_backlog.yaml task descriptions

## Findings and rewrites

### scripts/CRON_BRIEF.md (primary target — 7 negative-form instructions rewritten)
1. "never " → "always use  over "
2. "skip this step entirely" → "proceed directly to step 4b"
3. "that's not done/quarantined" → "with status outside {done, quarantined}"
4. "BUT ONLY if... NOT yt-transcript-skill" → "provided... (yt-transcript-skill handler: cap at 1)"
5. "STOP popping more items this tick" → "end popping for this tick"
6. "NOT directly to ralph_backlog.yaml" → "the gate in proposed_tasks.yaml is the mandatory staging step"
7. "Abandon gracefully — no partial commit" → "Exit cleanly — commit only after a complete, coherent unit of work lands"
8. "doesn't exist, fall back" → "Prefer X; if absent, read Y instead"
9. "skip the task" (blocked_on_research) → "defer the task"
10. "retrying an unchanged broken spec wastes tokens without progress" → "each retry requires a spec change to make progress"

### ralph_loop.py (3 fixes)
1. LOG_HEADER: "Append, don't replace" → "Always append; preserve existing entries"
2. Status constant comment: "do NOT mark done" → "keep status as REGRESSION pending investigation"
3. marker write comment: "Don't overwrite if it exists" → "Write only when the marker is absent (preserve existing)"
4. system_prompt: "with no preamble" → "starting with the content"
5. user_prompt: "No commentary" → "Lead with the content"

### CLAUDE.md
- 1 hit: informational "NOT wired" (hipporag_traverse.py description) — not an instruction; left unchanged.

### ralph_backlog.yaml descriptions
- 1 hit: the task being audited itself — no other description negatives found.

## Impact

Jeff's principle: negative phrasing puts the noun in context and the LLM often acts on the noun,
forgetting the negation. Rewrites convert prohibitions to positive actions. Highest-leverage change
is CRON_BRIEF.md (read every tick), followed by ralph_loop.py system_prompt (used for every
agent_creative task execution).
