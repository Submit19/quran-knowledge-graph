---
type: decision
adr: 0036
status: accepted
date: 2026-05-12
tags: [decision, agentic, loop, architecture, retrieval]
supersedes: none
---

# ADR-0036 — 3-way in-loop sufficiency gate (sufficient / hop_more / replan)

## Status
Accepted (2026-05-12). Spec shipped in commit `8363735`, tick 89 IMPL.

## Context
Task `from_neo4j_yt_sufficiency_gate` (p68) replaced the hard-coded 15-turn loop cap
with an evaluative gate that runs after each tool-call batch.

The original blunt cap ("stop at turn 15") discarded useful in-progress work on complex
abstract queries while still running unnecessary turns on simpler queries. Research from
the Neo4j YT deep crawl identified sufficiency-gate patterns as a key principle for
agentic retrieval loops.

## Decision
After each tool-call batch, the agent injects a short evaluator prompt asking:

> Is the information gathered sufficient to answer the question?
> Reply ONLY with: `sufficient`, `hop_more`, or `replan`.

The three outcomes drive distinct loop actions:

| Outcome | Action |
|---------|--------|
| `sufficient` | Return current answer, terminate loop |
| `hop_more` | Continue current plan; next batch of tool calls runs |
| `replan` | Abort current plan; reset concept-search sub-pipeline; start fresh plan |

A `MAX_REPLAN=2` cap prevents infinite replan cycles. The gate is env-gated via
`SUFFICIENCY_GATE=0` (default off) to allow staged rollout and A/B comparison against
the baseline 15-turn cap.

Both GraphReader and EventKernel components are specified to use this pattern.

The spec (`data/ralph_agent_from_neo4j_yt_sufficiency_gate.md`) is DONE_WITH_CONCERNS —
human review required before wiring into `app_free.py`.

## Consequences
- **Positive:** Early termination on simpler queries reduces token spend and latency.
- **Positive:** Replan path handles abstract queries that exhaust their initial retrieval
  plan, rather than timing out mid-work.
- **Positive:** Env gate (`SUFFICIENCY_GATE=0`) allows zero-risk A/B comparison.
- **Negative:** Evaluator prompt adds ~1 LLM call per tool-call batch (cost overhead).
  Mitigate: use a small/fast model for the evaluator, or gate to every N batches.
- **Negative:** Spec-only at tick 89 — requires a follow-up IMPL tick to integrate into
  `app_free.py`'s agent loop. DONE_WITH_CONCERNS flag must be reviewed first.
- **Neutral:** `replan` semantics (what "reset concept-search" means exactly) need
  clarification during the implementation tick.

## Cross-references
- Source: commit `8363735`, deliverable `data/ralph_agent_from_neo4j_yt_sufficiency_gate.md`
- Related: `app_free.py` agent loop, `chat.py` tool dispatch
- Proposed by: ralph IMPL tick 89
