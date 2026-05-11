---
task_id: from_ai_graph_cohere_rerank_ab_impl
drafted_at: 2026-05-11T18:19:45.073640+00:00
model: claude-sonnet-4-6
purpose: Pre-warmed implementation plan; read by Opus subagent during IMPL tick.
---

# Implementation plan: `from_ai_graph_cohere_rerank_ab_impl`

_Auto-drafted by `scripts/sonnet_prep.py` to reduce cold-discovery cost when the
IMPL tick spawns the Opus subagent. Treat as a starting point, not gospel._

---

# Implementation Plan: `from_ai_graph_cohere_rerank_ab_impl`

## 1. Scope Clarification

**In scope:**
- Write `data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md` — the deliverable is a **plan/design doc + results summary**, not live execution
- Since `COHERE_API_KEY` is flagged as a blocker, the actual A/B run may not be executable; the doc should include the complete eval plan, mock-runnable code sketches, and a results table with placeholder cells if the key is absent
- Document `RERANKER_BACKEND=cohere` branch design for `retrieval_gate.py`
- Document `eval_qrcd_reranker_ab.py` structure

**Out of scope:**
- Actually modifying `retrieval_gate.py` or creating `eval_qrcd_reranker_ab.py` as live files (those are separate impl tasks, unless the acceptance criteria expand)
- Modifying `chat.py` or the agentic loop

**Assumptions:**
- The "detail file" referenced in the task description already exists — likely at `data/` or `QKG Obsidian/` — Opus should locate it before writing
- The QRCD 22-q set and eval_v1 13-q set already exist as eval fixtures
- `retrieval_gate.py` currently only supports the BGE-M3 cross-encoder; Cohere Rerank 4 is an HTTP API call, not a local model

---

## 2. Files to Read

| File | Why |
|------|-----|
| `repo://retrieval_gate.py` | Understand current cross-encoder interface, input/output contract, where to branch |
| `repo://pipeline_config.yaml` | Check if `RERANKER_BACKEND` or similar tunables are declared |
| `repo://chat.py` | Confirm how `retrieval_gate.py` is invoked (call site, passage format) |
| `repo://data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md` | Check if it already partially exists (don't overwrite work) |
| Search `data/` for a detail file matching `*cohere*rerank*` or `*ai_graph_cohere*` | The task says "Plan already written in detail file" |
| `repo://eval_qrcd_reranker_ab.py` (if exists) | May have been partially scaffolded |
| Any existing QRCD eval scripts (e.g., `repo://eval_v1_bucketed.py`, `repo://scripts/`) | Understand eval harness pattern to stay consistent |
| `repo://ralph_backlog.yaml` — the task entry for `from_ai_graph_cohere_rerank_ab_impl` | May contain additional notes or the detail file path |

---

## 3. Files to Modify / Create

| File | Action |
|------|--------|
| `data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md` | **Create** — primary deliverable (≥600 bytes) |

No live code files are modified; this tick produces the design doc.

---

## 4. Sub-Step Breakdown

**Step 1 — Locate the detail file**
Search `data/`, `QKG Obsidian/`, and `ralph_backlog.yaml` for any pre-existing Cohere rerank plan. The task description says one exists. If found, use it as the backbone of the deliverable.

**Step 2 — Read `retrieval_gate.py`**
Map the current cross-encoder path: how passages are scored, how the top-K cutoff is applied, what the function signature looks like. Identify the exact insertion point for a `RERANKER_BACKEND=cohere` branch.

**Step 3 — Draft the `RERANKER_BACKEND=cohere` design**
In the deliverable doc, write pseudocode for the Cohere branch:
```python
if os.getenv("RERANKER_BACKEND") == "cohere":
    import cohere
    co = cohere.Client(os.getenv("COHERE_API_KEY"))
    results = co.rerank(model="rerank-multilingual-v3.0",  # or rerank-v4-pro if available
                        query=query, documents=passages, top_n=top_k)
    # map results.results[i].relevance_score → same output shape as BGE-M3 path
```
Note the model name uncertainty (confirm `rerank-english-v3.0` vs `rerank-multilingual-v3.0` vs `rerank-v4-pro` in Cohere docs).

**Step 4 — Draft `eval_qrcd_reranker_ab.py` structure**
Describe the script: load QRCD 22-q + eval_v1 13-q, run retrieval with `RERANKER_BACKEND=bge` (baseline) and `RERANKER_BACKEND=cohere`, collect hit@10 / MAP@10 / avg-cites per condition, output a comparison table. Mirror the structure of `eval_v1_bucketed.py`.

**Step 5 — Write the results table with placeholders**
Since `COHERE_API_KEY` is a blocker, include a properly structured results table with `[TBD — needs COHERE_API_KEY]` cells. This is honest and still satisfies the acceptance criteria for the doc.

**Step 6 — Add risk register + decision gate**
Include: API latency vs local model, cost-per-call estimate, 32K context limit check against longest passage set, fallback behaviour if key absent. Decision gate: if Cohere MAP@10 > BGE-M3 MAP@10 by ≥2 pts, promote to default.

**Step 7 — Write the doc and verify size**
Assemble all sections into `data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md`. After writing, confirm `wc -c` ≥ 600 bytes.

---

## 5. Risks / Unknowns

- **Detail file location**: If Opus can't find it, write the plan from scratch using the task description — enough signal exists.
- **Cohere model name**: "Rerank 4 Pro" may not yet be in the public API as `rerank-v4-pro`; the doc should note to verify against `cohere.list_models()` or the dashboard.
- **Eval fixture paths**: QRCD 22-q and eval_v1 13-q file locations — confirm in `scripts/` or `data/` before citing paths in the doc.
- **Output shape compatibility**: BGE-M3 returns raw logits; Cohere returns `relevance_score` in [0,1]. The branch must normalise to the same downstream interface.
- **`DONE_WITH_CONCERNS` pattern**: If the COHERE_API_KEY genuinely prevents running anything, mark the tick `DONE_WITH_CONCERNS` and note "run pending COHERE_API_KEY provisioning" in the summary.

---

## 6. Acceptance Check

```
[ ] data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md exists
[ ] File size >= 600 bytes  (run: wc -c data/ralph_agent_from_ai_graph_cohere_rerank_ab_impl.md)
[ ] Contains: retrieval_gate.py branch design (pseudocode)
[ ] Contains: eval_qrcd_reranker_ab.py structure description
[ ] Contains: results table (placeholder cells acceptable if key absent)
[ ] Contains: risk register with COHERE_API_KEY blocker callout
[ ] Contains: decision gate criteria
```
