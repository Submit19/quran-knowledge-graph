---
task_id: from_ai_graph_reflexion_pattern
drafted_at: 2026-05-11T15:46:48.023348+00:00
model: claude-sonnet-4-6
purpose: Pre-warmed implementation plan; read by Opus subagent during IMPL tick.
---

# Implementation plan: `from_ai_graph_reflexion_pattern`

_Auto-drafted by `scripts/sonnet_prep.py` to reduce cold-discovery cost when the
IMPL tick spawns the Opus subagent. Treat as a starting point, not gospel._

---

# Implementation Plan: `from_ai_graph_reflexion_pattern`

## Scope Clarification

**In scope:**
- Producing `data/ralph_agent_from_ai_graph_reflexion_pattern.md` — a design/proposal document describing how Reflexion would be implemented in QKG (this is an `agent_creative` task, acceptance criteria only requires the markdown file)
- The doc should cover: memo generation hook, storage schema, retrieval injection, expected impact on the weak-question cluster

**Out of scope:**
- Actual code changes to `chat.py` or any other `.py` file (this tick delivers a *proposal*, not production code)
- Running evals or measuring lift

**Assumptions:**
- This is a *design proposal* task (type `agent_creative`, acceptance criteria = markdown file ≥ 800 bytes). The Opus subagent should write a thorough design doc, not implement the code.
- The existing `tool_recall_similar_query` tool in `chat.py` is the injection point for prior memos — Opus should verify its signature.
- `reasoning_memory.py` already writes `(:ReasoningTrace)` nodes — Reflexion memos can piggyback on or extend this schema.

---

## Files to Read

1. `repo://chat.py` — understand the 21 tools, especially `tool_recall_similar_query` signature and the agent loop end-of-turn logic; look for where a post-turn hook could be inserted
2. `repo://reasoning_memory.py` — existing Neo4j schema for `(:ReasoningTrace)-[:HAS_STEP]->(:ToolCall)-[:RETRIEVED]->(:Verse)`; understand how memos would extend or parallel this
3. `repo://data/eval_v1_baseline_rerank_on.md` — locate the weak-question cluster (meditation/reverence/Surah 55, 13-27 cites) to concretely anchor the hypothesis
4. `repo://pipeline_config.yaml` — check for any existing reflexion/memo config keys; understand tunables pattern for any new knobs
5. `repo://SESSION_LOG.md` (top entry only) — confirm no in-flight work that overlaps

---

## Files to Produce

| Path | Description |
|---|---|
| `data/ralph_agent_from_ai_graph_reflexion_pattern.md` | Primary deliverable: design proposal for Reflexion in QKG |

No existing files are modified this tick.

---

## Sub-Step Breakdown

### Step 1 — Read & extract current end-of-turn structure (5 min)
Open `repo://chat.py`. Find: (a) where the agent loop terminates per user query, (b) `tool_recall_similar_query` — its inputs, outputs, and how it injects context into the planner prompt. Note any existing "memory" or "reflection" hooks.

### Step 2 — Read reasoning_memory schema (3 min)
Open `repo://reasoning_memory.py`. Record the exact node labels and relationship types. Determine whether a new `(:ReflexionMemo)` node should be a child of `(:ReasoningTrace)` or a standalone node linked to `(:Query)`.

### Step 3 — Read the eval weak-question data (3 min)
Open `repo://data/eval_v1_baseline_rerank_on.md`. Find the 13-27 cite cluster. Note 3-5 specific query examples that the Reflexion memos are hypothesised to help — these go into the proposal as concrete motivation.

### Step 4 — Draft the proposal document
Write `data/ralph_agent_from_ai_graph_reflexion_pattern.md` with the following sections:

- **Motivation** — Reflexion (Shinn 2023) summary in 3 sentences; the weak-question cluster as evidence of repeated bad tool sequences
- **Proposed Neo4j schema extension** — `(:ReflexionMemo {memo_text, query_embedding, created_at, query_hash})` linked via `(:Query)-[:HAS_MEMO]->(:ReflexionMemo)`; explain why this is separate from `(:ReasoningTrace)` (memos are cross-session, traces are per-session)
- **Memo generation hook** — where in `chat.py` to call a new `generate_reflexion_memo(query, tool_sequence, answer)` function; propose a one-sentence LLM prompt: *"In one sentence, what would you do differently to answer '{query}' given the tool sequence used?"*
- **Injection into planner** — how `tool_recall_similar_query` (or a new `tool_recall_reflexion_memos`) retrieves top-K memos by cosine similarity on `query_embedding` and prepends them to the system prompt as a `<prior_reflections>` block
- **Config knobs** — `reflexion_enabled: bool`, `reflexion_top_k: int` (default 3), `reflexion_similarity_threshold: float` (default 0.82) — addable to `pipeline_config.yaml`
- **Expected impact** — hypothesis: memos for Surah 55/meditation queries will encode "don't rely on semantic search alone — use `get_code19_features` + `concept_search`", steering agent away from the bad sequence on next similar hit
- **Risks & mitigations** — memo staleness if pipeline changes; embedding drift; LLM generating low-signal memos (mitigate: filter memos where answer quality score < threshold)
- **Implementation sequencing** — Phase 1: schema + memo writer; Phase 2: retrieval injection; Phase 3: eval on weak-question cluster; estimated 2-3 IMPL ticks
- **Decision gate** — ship only if weak-cluster MAP@10 improves ≥ 5 pts vs baseline

### Step 5 — Verify file size
Count bytes in the written file. Target ≥ 1500 bytes (well above the 800-byte minimum). If under 800, expand the risks or implementation sequencing section.

### Step 6 — Commit
```
git add data/ralph_agent_from_ai_graph_reflexion_pattern.md
git commit -m "ralph tick: from_ai_graph_reflexion_pattern — Reflexion design proposal; memo schema, injection hook, weak-cluster hypothesis; tick N IMPL"
git push
```

---

## Risks / Unknowns

- **`tool_recall_similar_query` may not exist yet** — if the tool is missing from `chat.py`, the proposal should note this as a prerequisite and suggest it be implemented alongside Phase 2, not Phase 1.
- **Schema collision** — if `reasoning_memory.py` already has a memo-like structure, the proposal must reconcile rather than duplicate.
- **Weak-question eval data may be in a different file** — if `eval_v1_baseline_rerank_on.md` doesn't have the meditation/Surah 55 cluster, check `data/verse_analysis/` or `ralph_log.md`.
- **`agent_creative` ≠ code** — Opus must not spend time writing Python; the deliverable is pure markdown prose + schema/pseudocode snippets only.

---

## Acceptance Check

1. `ls -la data/ralph_agent_from_ai_graph_reflexion_pattern.md` — file exists
2. `wc -c data/ralph_agent_from_ai_graph_reflexion_pattern.md` — output ≥ 800 (target 1500+)
3. Skim: does it contain sections on memo generation, Neo4j schema, injection, and weak-cluster hypothesis? If yes, criteria satisfied.
