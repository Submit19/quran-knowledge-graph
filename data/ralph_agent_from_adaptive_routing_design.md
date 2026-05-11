# Adaptive Query-Conditional Retrieval Architecture
### Task: `from_adaptive_routing_design` | Tick 51 | 2026-05-12

_Design doc produced inline (no pre-warmed plan available). Evidence basis:
`data/ralph_analysis_from_ai_graph_disable_reranker_baseline.md`,
`data/eval_v1_baseline_rerank_on.json`, `chat.py:classify_query()`._

---

## Executive Summary

QKG's current pipeline applies a single uniform retrieval config to every query
(BGE-M3-EN + bge-reranker-v2-m3, MAX_TOOL_TURNS=8). QRCD ablation and eval_v1
data reveal a clear opportunity: **the reranker that helps BROAD/theme queries
actively hurts CONCRETE/ABSTRACT queries** (hit@10 0.636 → 0.318 on Arabic
after reranking). A 2-profile spike is the minimum-viable first step; the full
3-layer architecture described here is the target state.

**Headline metric target:** avg_cites/q 43.6 → 52+ on the 50-question bucketed
eval once all three layers are live.

---

## 1. Five Profile Definitions

| Profile | Label | Characteristics | Size in eval_v1 (13q) | Baseline avg cites |
|---------|-------|-----------------|----------------------|--------------------|
| **BROAD** | `broad` | Multi-concept ("common themes"), synthesis ("compare X and Y"), long free-form | 1 | 167 |
| **CONCRETE** | `concrete` | Named entities (paradise, Moses, hell, charity), events | 5 | 38.5 |
| **ABSTRACT** | `abstract` | Single-word concepts (meditation, reverence, hypocrisy) | 2 | 20.0 |
| **STRUCTURED** | `structured` | Verse refs [2:255], Arabic roots, Code-19 | 0 in eval_v1 | ~60 (est) |
| **ARABIC** | `arabic` | Arabic-script input, Arabic-name queries | 0 in eval_v1 | unknown |

> Note: current `classify_query()` in `chat.py` (lines 1075–1147) handles
> `structured`, `concrete`, `abstract` but has **no BROAD class** — everything
> that doesn't match concrete/structured defaults to `abstract`. This is the
> primary gap; BROAD queries (multi-concept, theme synthesis) land in the
> `abstract` bucket and share its config.

### Evidence basis for profile separation

- QRCD ablation (`data/qrcd_ablation.json`): reranker destroys Arabic hit@10
  (0.636 → 0.318). CONCRETE and ABSTRACT queries are precisely the
  Arabic-sensitive cluster.
- eval_v1 cluster analysis: "common themes" (BROAD) averages 167 cites/q with
  reranker on — it is already at ceiling; reranker may be helping here by
  filtering keyword noise in a multi-topic query.
- "meditation", "reverence" (ABSTRACT): 13–27 cites — worst performers, most
  sensitive to retrieval order.

---

## 2. Layer 1 — Per-Profile Retrieval Config

| Profile | Reranker | RRF k | Embedding index | max_tool_turns | Citation verifier |
|---------|----------|-------|-----------------|----------------|-------------------|
| **BROAD** | ON (bge-reranker-v2-m3) | 60 | verse_embedding_m3 | 8 | NLI (full) |
| **CONCRETE** | **OFF** | 60 | verse_embedding_m3 | 6 | NLI (fast) |
| **ABSTRACT** | **OFF** | 60 | verse_embedding_m3 | 8 | NLI (full) |
| **STRUCTURED** | OFF | 60 | verse_embedding_m3 | 4 | skip |
| **ARABIC** | OFF | 60 | **verse_embedding_m3_ar** | 6 | NLI (fast) |

**Rationale for reranker OFF on CONCRETE/ABSTRACT/STRUCTURED/ARABIC:**
The QRCD ablation is unambiguous. For non-BROAD queries, BGE-M3-EN vector order
is already optimal; reranking harms recall. BROAD queries benefit from reranker's
noise filtering over a wide multi-topic result set.

**Implementation surface in `retrieval_gate.py`:**
```python
# retrieval_gate.py — proposed patch
def rerank_verses(query, verses, top_k=20, profile: str = "abstract"):
    """profile is passed from chat.py per-request."""
    _RERANK_PROFILES = {"broad"}   # only BROAD gets reranker
    if RERANK_DISABLED or profile not in _RERANK_PROFILES:
        return verses[:top_k]
    model = _get_reranker()
    ...
```

**Integration point in `chat.py`:**
1. `classify_query(query)` returns profile string.
2. Profile is passed through to `tool_semantic_search`, `tool_hybrid_search`,
   etc., which forward it to `retrieval_gate.rerank_verses(...)`.
3. `MAX_TOOL_TURNS` is read from a per-profile dict at the top of the agentic
   loop in `app_free.py`.

---

## 3. Layer 2 — Per-Profile Agent Shape

| Profile | Agent strategy | Rationale |
|---------|---------------|-----------|
| **BROAD** | Reflexion loop (up to 2 self-critique passes) | Multi-concept queries need iterative refinement; single-pass ReAct misses coverage |
| **CONCRETE** | Linear ReAct (no self-critique) | Named-entity queries have a definitive answer; Reflexion adds latency without gain |
| **ABSTRACT** | Linear ReAct + forced concept_search first | Abstract tokens map poorly to keyword search; concept_search with Porter expansion is the right first tool |
| **STRUCTURED** | Direct lookup shortcut (get_verse / search_arabic_root) | Structured queries have a known answer shape; full ReAct loop is waste |
| **ARABIC** | Linear ReAct with embedding_m3_ar first | Arabic script queries need Arabic embedding space, not English BGE-M3-EN |

**Implementation surface in `app_free.py`:**
```python
# app_free.py — proposed system prompt injection per profile
_PROFILE_SYSTEM_HINTS = {
    "broad": "This is a synthesis / multi-concept query. Use traverse_topic and concept_search broadly. After your first answer draft, review coverage and make 1-2 additional targeted tool calls if major themes are missing.",
    "concrete": "This is a concrete entity / event query. Use semantic_search and search_keyword. Cite specific verses. Do not over-search.",
    "abstract": "This is an abstract concept query. Call concept_search FIRST (expands surface forms). Then semantic_search. Aim for breadth of citation.",
    "structured": "This is a structured reference query. Use get_verse or search_arabic_root directly. Do not explore unless explicitly asked.",
    "arabic": "This query contains Arabic. Use semantic_search with the Arabic embedding index path. Call search_arabic_root if roots are mentioned.",
}
```

**Note on MoA (Mixture-of-Agents) sub-agent decomp:**  
MoA for BROAD queries is a phase-2 consideration (requires spawning 2-3 parallel
subagents and merging). The Reflexion loop is a lower-risk first step that can be
validated on the 50-question bucketed eval before committing to MoA.

---

## 4. Layer 3 — Per-Profile Model Routing

| Profile | Primary model | Fallback | Rationale |
|---------|--------------|----------|-----------|
| **BROAD** | Opus (deep synthesis) | Sonnet | Multi-concept synthesis needs broad reasoning |
| **CONCRETE** | Sonnet (default) | Sonnet | Fast concrete lookup; Sonnet is sufficient |
| **ABSTRACT** | Sonnet | Sonnet | Abstract concepts benefit from Sonnet reasoning; Opus adds marginal gain vs cost |
| **STRUCTURED** | Haiku | Sonnet | Deterministic lookup; Haiku is fast + cheap |
| **ARABIC** | Sonnet | Sonnet | Arabic morphology reasoning needs Sonnet minimum |

**Cost note:** Opus is ~15× more expensive than Haiku. BROAD queries are ~7% of
eval_v1 traffic (1/13). Model routing to Opus only for BROAD caps cost exposure.

**Implementation surface:** `app_free.py` `deep_dive` flag + model selection block
(lines ~638–641). Extend to read profile from classify_query() and map to model.

---

## 5. Classifier Extension Plan

### Current `classify_query()` gaps

1. **No BROAD class.** Queries like "common themes", "what does the Quran say
   about X and Y", "compare X with Z" default to `abstract`. Fix: add BROAD
   detection before the CONCRETE check.
2. **No ARABIC class.** Arabic-script input is not detected; it hits `abstract`
   and uses English embedding. Fix: detect Unicode Arabic range `[؀-ۿ]` at the
   top of classify_query().
3. **CONCRETE includes "hell" and "paradise"** — these are high-frequency Quranic
   concepts with large verse sets; routing them to CONCRETE (reranker OFF) is
   correct per ablation data. No change needed.

### Proposed additions to `classify_query()` in `chat.py`

```python
def classify_query(query: str) -> str:
    ...
    # 0. ARABIC — any Arabic script input
    if re.search(r'[؀-ۿ]', query):
        return "arabic"

    ...existing STRUCTURED check...

    # 1.5 BROAD — multi-concept synthesis (new, before CONCRETE)
    _BROAD_SIGNALS = [
        r'\bcommon themes?\b', r'\bwhat does the quran (say|teach)\b',
        r'\bcompare\b.+\band\b', r'\boverview\b', r'\ball (?:the )?(?:mentions|verses) of\b',
        r'\bsummarize (?:the )?(quran|entire|all)\b',
    ]
    if any(re.search(pat, q) for pat in _BROAD_SIGNALS):
        return "broad"
    # Multi-concept heuristic: 4+ content words with no concrete match
    content_words = [t for t in tokens if len(t) > 3]
    if len(content_words) >= 4 and not (tokens & {t for t in _CONCRETE_TOKENS if " " not in t}):
        return "broad"

    ...existing CONCRETE, ABSTRACT checks...
```

---

## 6. Misclassification Cost Analysis

| Mis-class | From → To | Impact | Severity |
|-----------|-----------|--------|----------|
| BROAD classified as ABSTRACT | common themes → abstract | Reranker OFF on a multi-topic query; slight recall loss | Low (vector order already good) |
| CONCRETE classified as ABSTRACT | paradise → abstract | Reranker OFF; no regression since OFF is better | Neutral/positive |
| ABSTRACT classified as BROAD | meditation → broad | Reranker ON; ablation shows −50% hit@10 for Arabic | **High** |
| STRUCTURED classified as ABSTRACT | [2:255] → abstract | Wrong agent shape; still resolves via ReAct | Low |
| ARABIC classified as CONCRETE/ABSTRACT | Arabic query → English path | Wrong embedding index; retrieval quality degrades | **High** |

**Key insight:** The high-severity cases are (a) ABSTRACT landing in BROAD
(reranker turns on incorrectly) and (b) ARABIC not being detected. Both are
addressed by the classifier additions above.

**Mitigation:** Log profile classification with every request in `reasoning_memory.py`
as a `ToolCall` property. This gives an audit trail for misclassification debugging
without requiring a separate eval.

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| 50q bucketed eval shows no per-profile lift | Medium | Invalidates Layer 1 hypothesis | Fall back to uniform config; log findings |
| BROAD detector false-positives (triggers on short multi-word queries) | Medium | Reranker ON unnecessarily | Conservative regex patterns; tune on 50q set |
| Reflexion loop for BROAD adds >5s latency | Medium | User-facing regression | Cap at 1 self-critique pass; measure before enabling |
| Model routing to Opus for BROAD exceeds API cost budget | Low | Cost spike | Gate Opus routing behind `DEEP_DIVE_MODEL_ROUTING=1` env var |
| Per-profile system-prompt hints confuse the model | Low | Answer quality regression | A/B test hints vs no-hints on 50q eval before committing |
| classify_query() regex false-negatives on mixed-language queries | Low | Wrong profile | Fall back to ABSTRACT (neutral/safe default) |

---

## 8. Sequencing

### Phase 0 (current tick): Design doc (this file)

### Phase 1: 2-Profile Spike — BROAD / NOT-BROAD (→ `from_adaptive_routing_2profile_spike`)

- **Single axis:** BROAD = reranker ON, NOT-BROAD = reranker OFF.
- Wire: `classify_query()` → `retrieval_gate.rerank_verses(..., profile=profile)`.
- Eval on 50-question bucketed set (→ `from_adaptive_routing_50q_bucketed_eval`).
- Decision gate: if NOT-BROAD queries show +5% avg_cites without BROAD regression,
  proceed to Phase 2.
- Estimated effort: 1 IMPL tick (cleanup type, ~40 lines diff).

### Phase 2: ARABIC profile

- Add Arabic Unicode detector to `classify_query()`.
- Switch embedding index to `verse_embedding_m3_ar` for ARABIC queries.
- Requires `eval_arabic.py` harness (or extend 50q set with 10 Arabic questions).

### Phase 3: Full 5-profile + Layer 2 agent shapes

- Add CONCRETE/ABSTRACT/STRUCTURED system-prompt hints.
- Reflexion loop for BROAD.
- Eval on full 50-question set per-bucket.

### Phase 4: Layer 3 model routing

- Gate Opus routing behind env var.
- Eval cost/quality tradeoff on BROAD cluster only.

---

## 9. Implementation Estimates

| Phase | Files changed | LOC delta | Estimated tick count |
|-------|--------------|-----------|---------------------|
| Phase 1 (2-profile spike) | `chat.py`, `retrieval_gate.py`, `app_free.py` | +40 / −5 | 1 IMPL tick |
| Phase 2 (ARABIC) | `chat.py` | +15 | 1 IMPL tick |
| Phase 3 (5-profile + Layer 2) | `chat.py`, `app_free.py` | +80 | 1–2 IMPL ticks |
| Phase 4 (Layer 3 model routing) | `app_free.py` | +30 | 1 IMPL tick |

---

## 10. Open Questions / Dependencies

1. **50-question bucketed eval set** (`from_adaptive_routing_50q_bucketed_eval`) must
   be built before any phase can be empirically validated. Design can proceed in
   parallel.
2. **Current `classify_query()` has no test coverage.** Before extending, add a
   `test_classify_query.py` with at least 20 examples (one new task: ~20 lines).
3. **Reflexion loop design**: not yet implemented in `app_free.py`. The self-critique
   pass would re-enter the agentic loop with a "review your answer for missing
   themes" system message. Needs its own spike task.

---

_Produced by tick 51 orchestrator (Sonnet) as inline agent_creative. Review before implementing._
