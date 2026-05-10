---
type: research
status: done
priority: 65
tags: [research/ralph-loop, research/agent-harness, research/context-management]
source: data/research_neo4j_crawl/05_ralph_yt_extract.md
date_added: 2026-05-10
---

# Ralph Loop Best Practices (Jeff Huntley / HumanLayer YT)

## TL;DR
- Our `ralph_backlog.yaml` + `ralph_tick.py` single-task-per-tick architecture exactly matches Jeff's "one context window, one activity, one goal" rule. We are on-pattern.
- CLAUDE.md is dangerously long: Jeff says ~60 lines / ~3K tokens max; ours runs several hundred lines. This eats into the ~176K usable window (200K - 16K harness overhead) before any work starts.
- Filter test runner output to failing cases only — verbose output wastes tokens and can scroll past errors.
- Negative-phrasing anti-pattern: "do not X" puts X in context; model forgets the negation. Rewrite as positive action instructions.
- The official Anthropic Ralph plugin uses auto-compaction internally — compaction can silently drop specs and goals. Our bash-harness + fresh subprocess per tick is structurally superior.

## Key findings
- **Deliberate context allocation** ("mallocing"): Jeff reserves a fixed ~5K token block at loop start as a compact index (hyperlinks to spec files, not full specs). Our full CLAUDE.md injection every tick is heavier than this; `CLAUDE_INDEX.md` is the right direction.
- **Acceptance-criteria gate**: Jeff's accept / `git reset --hard` / retry taxonomy aligns with our `DONE_WITH_CONCERNS` / `QUARANTINED` / `FAILED` / 3-strikes taxonomy — we have this.
- **Git commit outside the context window**: commits and pushes should be deterministic harness actions, not left to model judgment. `ralph_tick.py` already does this correctly.
- **Parallel worktrees**: run a cache-seeding loop and a graph-enrichment loop simultaneously in separate git worktrees, then merge. Avoids context-pollution between unrelated tasks.
- **Auto-compaction is the enemy of determinism**: the plugin uses it; our bash approach avoids it. Our "Codebase Patterns" block and status taxonomy must survive the full tick duration — compaction threatens them.
- **"Treat it like a Twitch stream"**: best learnings come from watching the loop run and asking "why did it do that?" then tuning. Passive unattended runs yield worse outcomes.

## Action verdict
- ✅ Adopt — tokenize CLAUDE.md (cl100k_base); if > 3K tokens, create `CLAUDE_INDEX.md` ≤ 80 lines and switch ralph_tick.py to use it.
  **Promoted as:** `from_ralph_yt_01_tokenize_claudemd` (high)
- ✅ Adopt — wrap `eval_v1.py` with output filter: suppress PASS, emit only FAIL + summary count.
  **Promoted as:** `from_ralph_yt_02_filter_test_output` (medium)
- ✅ Adopt — audit `ralph_tick.py` system prompt and `ralph_backlog.yaml` for negative-form instructions; rewrite as positive.
  **Promoted as:** `from_ralph_yt_03_audit_negative_prompts` (low)
- ❌ Skip — Anthropic Ralph plugin. Our architecture is superior due to no auto-compaction.
- 🔬 Research deeper — parallel worktree spike for concurrent cache-seeding + graph-enrichment loops.
  **Promoted as:** `from_ralph_yt_04_parallel_worktree_spike` (low)

## Cross-references
- [[agentic-graphrag-yt-patterns]] — agent loop architectural patterns (router, sufficiency gate)
- Source: `repo://data/research_neo4j_crawl/05_ralph_yt_extract.md`
