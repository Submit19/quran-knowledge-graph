# scripts/ — operational housekeeping

Small Python utilities the Ralph cron loop and human operators run to keep state visible and the Obsidian vault current.

## Files

| Script | What it does | Idempotent? |
|--------|--------------|-------------|
| `state_snapshot.py` | Overwrites `STATE_SNAPSHOT.md` (and mirrors to `QKG Obsidian/CURRENT STATE.md`). Loop status, backlog health, top pending, recent ticks, recent commits, working tree. | yes |
| `vault_update.py` | Append today's commits to the vault's daily note (`QKG Obsidian/daily/YYYY-MM-DD.md`); create stub research notes for any `data/research_*.md` that doesn't yet have a vault entry (source-aware — skips if a richer note already references the source). | yes |
| `haiku_prep.py` | End-of-tick prep work via Haiku (Anthropic API). Three jobs: (1) `validate_specs` — auto-fix `value:`→`min:`, warn on cypher_analysis tasks missing query/script; (2) `precache_research` — pre-fetch next 2 WebFetch-handler URLs to `data/research_cache/<slug>.html`; (3) `preclassify_proposals` — Haiku annotates each pending entry in `data/proposed_tasks.yaml` with `haiku_notes: {classification, duplicate_of, relates_to, note}`. Each job is failure-safe. Disable with `HAIKU_PREP_DISABLED=1`. Override model with `HAIKU_PREP_MODEL=<id>`. | yes |
| `tick_finalize.py` | Single end-of-tick entry point. Calls `state_snapshot.py` + `vault_update.py` + `haiku_prep.py`; refreshes `MORNING_REPORT.md` every 12 ticks (and mirrors to vault). | yes |

## Usage

End of each tick — the cron orchestrator's subagent runs:

```
python scripts/tick_finalize.py
```

…then commits everything (deliverable + state files + vault diffs) in a single `ralph tick: <id>` or `research tick: <short>` commit.

By hand any time:
```
python scripts/state_snapshot.py   # refresh the snapshot file only
python scripts/vault_update.py     # update vault daily note + research stubs
python scripts/tick_finalize.py    # all of the above + maybe morning report
```

## State files

`scripts/.vault_update_state.json` (auto-created, gitignored) — tracks the last commit `vault_update.py` saw, so it doesn't re-process old commits on every run.

## Adding a new housekeeping script

1. Write `scripts/<name>.py` — must be idempotent and safe to call from a fresh subagent context.
2. Add a `run("<name>.py")` line to `tick_finalize.py`.
3. Document above.
