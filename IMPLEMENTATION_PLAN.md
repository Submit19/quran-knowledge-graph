# Implementation Plan: Hallucination Reduction + Arabic Text

**Status:** Planning (not yet implemented)
**Phases:** 6 phases, each independently deployable

---

## Overview

Upgrade the Quran Knowledge Graph from a proof-of-concept to a production-grade, citation-verified system with 4-layer hallucination defense and bilingual Arabic+English support.

```
                  User Question
                       |
              [Layer 1: Retrieval Gate]
              Cross-encoder reranking +
              Corrective RAG fallback
                       |
              [Layer 2: KG Grounding]
              Typed edges (SUPPORTS, QUALIFIES, etc.)
              surfaced through tools
                       |
              [Claude Agentic Loop]
              Tools query Neo4j, stream via SSE
                       |
              [Layer 3: Citation Verification]
              NLI entailment check on every
              [sura:verse] citation
                       |
              [Layer 4: Constrained Output]
              Citation density enforcement +
              re-generation trigger
                       |
                  Verified Response
                  (Arabic + English)
```

---

## Phase 1: Wire Typed Edges into Tools (Layer 2)

**Impact:** High | **Effort:** Low | **Risk:** None
**Dependencies:** None — typed edges already exist in Neo4j

### 1.1 New tool: `query_typed_edges`

**File:** `chat.py`

Add 7th tool that lets Claude query by relationship type:

```python
def tool_typed_edges(session, verse_id: str, edge_type: str = None) -> dict:
    """Query verses connected by a specific relationship type."""
    if edge_type:
        rows = session.run("""
            MATCH (v:Verse {verseId: $id})-[r:""" + edge_type + """]-(other:Verse)
            RETURN other.verseId AS otherId, other.surahName AS surahName,
                   other.text AS text, r.score AS score,
                   r.confidence AS confidence
            ORDER BY r.score DESC LIMIT 12
        """, id=verse_id)
    else:
        # Return all typed edges grouped by type
        rows = session.run("""
            MATCH (v:Verse {verseId: $id})-[r]-(other:Verse)
            WHERE type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']
            RETURN other.verseId AS otherId, type(r) AS relType,
                   other.text AS text, r.score AS score
            ORDER BY r.score DESC LIMIT 20
        """, id=verse_id)
```

Tool schema:
```json
{
  "name": "query_typed_edges",
  "description": "Find verses connected by a specific relationship type: SUPPORTS (evidence), ELABORATES (expands detail), QUALIFIES (adds condition/exception), CONTRASTS (complementary perspective), REPEATS (near-verbatim). Use this after get_verse to understand HOW verses relate.",
  "input_schema": {
    "properties": {
      "verse_id": {"type": "string", "description": "Verse reference e.g. '2:255'"},
      "edge_type": {"type": "string", "enum": ["SUPPORTS","ELABORATES","QUALIFIES","CONTRASTS","REPEATS"], "description": "Optional: filter to one type. Omit to get all typed edges."}
    },
    "required": ["verse_id"]
  }
}
```

### 1.2 Enrich `get_verse` results with typed edge info

**File:** `chat.py`, function `tool_get_verse`

After the existing RELATED_TO neighbour query, add:

```python
typed_rows = session.run("""
    MATCH (v:Verse {verseId: $id})-[r]-(other:Verse)
    WHERE type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']
    RETURN other.verseId AS otherId, type(r) AS relType, r.confidence AS confidence
""", id=verse_id)
typed_map = {}
for tr in typed_rows:
    typed_map.setdefault(tr["otherId"], []).append(tr["relType"])
```

Merge into the `connected` list: each neighbour gets a `"relationship_types"` field.

### 1.3 Update system prompt

**File:** `chat.py`, `SYSTEM_PROMPT`

Add after the tool list:

```
The graph has typed relationships between verses:
- SUPPORTS: verse provides independent evidence for another's claim
- ELABORATES: verse expands on another with more detail
- QUALIFIES: verse adds a condition or exception to another
- CONTRASTS: verses present complementary perspectives on the same topic
- REPEATS: near-verbatim repetition across surahs

Use query_typed_edges after get_verse to understand HOW verses relate.
When citing, note the relationship: "[5:6] elaborates the ablution rules in [4:43]"
"[16:115] qualifies the food prohibition in [2:173] with a duress exception"
```

### 1.4 Frontend: color-coded link types

**File:** `app.py` (`_graph_for_tool`), `index.html`

In `_graph_for_tool`, when typed edge data is in tool results, pass type through:
```python
link(v1, v2, "supports")   # instead of always "related"
```

In `index.html`, update link colors:
```javascript
const LINK_COLORS = {
  related:    '#164e63',
  mentions:   '#78350f',
  supports:   '#10b981',   // green
  elaborates: '#6366f1',   // indigo
  qualifies:  '#f59e0b',   // amber
  repeats:    '#64748b',   // slate
  contrasts:  '#ef4444',   // red
};
```

Add legend entries for each type.

---

## Phase 2: Retrieval Quality Gating (Layer 1)

**Impact:** High | **Effort:** Medium | **Risk:** Low
**Dependencies:** None

### 2.1 Create `retrieval_gate.py`

New file with cross-encoder reranking:

```python
from sentence_transformers import CrossEncoder

_reranker = None
def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    return _reranker

def rerank_verses(query: str, verses: list[dict], top_k: int = 20) -> list[dict]:
    """Rerank verses by cross-encoder relevance to the query."""
    model = _get_reranker()
    pairs = [(query, v.get("text", "") or v.get("english", "")) for v in verses]
    scores = model.predict(pairs)
    for v, s in zip(verses, scores):
        v["relevance_score"] = float(s)
    verses.sort(key=lambda v: v["relevance_score"], reverse=True)
    return verses[:top_k]

def assess_retrieval_quality(verses: list[dict], threshold: float = 0.3) -> str:
    """Return 'good', 'marginal', or 'poor' based on top scores."""
    if not verses:
        return "poor"
    top_score = max(v.get("relevance_score", 0) for v in verses)
    if top_score >= threshold:
        return "good"
    elif top_score >= 0.1:
        return "marginal"
    return "poor"
```

Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~80MB, fast CPU inference).

### 2.2 Wire into tool dispatch with Corrective RAG

**File:** `chat.py`, `dispatch_tool`

Wrap tool results through the reranker. If quality is "poor", trigger fallback:

```python
def dispatch_tool(session, tool_name, tool_input, user_query=None):
    result = _call_tool(session, tool_name, tool_input)

    if user_query and tool_name in ("search_keyword", "semantic_search"):
        verses = _extract_verses_from_result(result)
        if verses:
            reranked = rerank_verses(user_query, verses)
            quality = assess_retrieval_quality(reranked)

            if quality == "poor" and tool_name == "search_keyword":
                # Corrective RAG: fall back to semantic search
                fallback = _call_tool(session, "semantic_search", {"query": user_query})
                result["fallback_results"] = fallback
                result["retrieval_note"] = "Keyword search had low relevance. Semantic search results appended."

    return result
```

**Key:** Pass `user_query` through the streaming pipeline so `dispatch_tool` can access it.

### 2.3 Thread user query through the pipeline

**File:** `app.py`, `_agent_stream`

The user's original message is available in `_agent_stream(message, history)`. Pass it to `dispatch_tool`:

```python
tool_result = dispatch_tool(session, tool_name, tool_input, user_query=message)
```

---

## Phase 3: Citation Verification (Layer 3)

**Impact:** Very High | **Effort:** High | **Risk:** Medium (latency)
**Dependencies:** Benefits from Phase 2 reranker

### 3.1 Create `citation_verifier.py`

New file with three functions:

**Claim decomposition** (uses Haiku for speed):
```python
def decompose_claims(text: str, client) -> list[dict]:
    """Decompose response into atomic claims with their cited verses."""
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": f"""
Decompose this text into atomic claims. For each claim, list any [sura:verse] citations.
Return JSON array: [{{"claim": "...", "citations": ["2:255", "3:18"]}}]
Only include factual/theological claims, not transitions or questions.

Text: {text}
"""}]
    )
    return json.loads(resp.content[0].text)
```

**NLI verification** (uses cross-encoder):
```python
from sentence_transformers import CrossEncoder

_nli_model = None
def _get_nli():
    global _nli_model
    if _nli_model is None:
        _nli_model = CrossEncoder('cross-encoder/nli-deberta-v3-xsmall')
    return _nli_model

def verify_citation(claim: str, verse_text: str) -> dict:
    """Check if verse_text entails the claim. Returns {label, score}."""
    model = _get_nli()
    scores = model.predict([(verse_text, claim)])
    # deberta NLI outputs [contradiction, neutral, entailment]
    labels = ["contradiction", "neutral", "entailment"]
    idx = scores[0].argmax()
    return {"label": labels[idx], "score": float(scores[0][idx])}
```

**Full response verification:**
```python
def verify_response(text: str, verse_texts: dict, client) -> dict:
    claims = decompose_claims(text, client)
    results = []
    for c in claims:
        verified_citations = []
        for ref in c["citations"]:
            vtext = verse_texts.get(ref, "")
            if vtext:
                nli = verify_citation(c["claim"], vtext)
                verified_citations.append({"ref": ref, **nli})
        results.append({
            "claim": c["claim"],
            "citations": verified_citations,
            "has_citation": len(c["citations"]) > 0,
            "supported": any(vc["label"] == "entailment" for vc in verified_citations),
        })

    total = len(results)
    cited = sum(1 for r in results if r["has_citation"])
    supported = sum(1 for r in results if r["supported"])

    return {
        "citation_recall": cited / total if total else 1.0,
        "citation_precision": supported / cited if cited else 1.0,
        "total_claims": total,
        "flagged": [r for r in results if r["has_citation"] and not r["supported"]],
        "uncited": [r for r in results if not r["has_citation"]],
    }
```

### 3.2 Wire into SSE pipeline

**File:** `app.py`, `_agent_stream` function

After the agentic loop completes and `full_text` is assembled:

```python
# Existing: fetch verse texts for tooltips
refs = set(_BRACKET_REF.findall(full_text))
verses = _fetch_verses(session, refs)

# NEW: verify citations
from citation_verifier import verify_response
verification = verify_response(full_text, verses, ai)

# Send verification as new SSE event
q.put({"t": "verification", "d": verification})

# Then send done event as before
q.put({"t": "done", "verses": verses})
```

### 3.3 Frontend verification badge

**File:** `index.html`

Handle `verification` event in the SSE reader:

```javascript
if (ev.t === 'verification') {
    const v = ev.d;
    const badge = document.createElement('div');
    badge.className = 'verification-badge';
    if (v.citation_precision >= 0.9 && v.citation_recall >= 0.9) {
        badge.innerHTML = 'Citations verified';
        badge.classList.add('verified-good');
    } else {
        badge.innerHTML = `${v.flagged.length} citation(s) need review`;
        badge.classList.add('verified-warn');
    }
    currentBubble.appendChild(badge);
}
```

CSS:
```css
.verification-badge {
    font-size: 0.7em; padding: 2px 8px; border-radius: 10px;
    margin-top: 6px; display: inline-block;
}
.verified-good { background: rgba(16,185,129,0.15); color: #10b981; }
.verified-warn { background: rgba(245,158,11,0.15); color: #f59e0b; }
```

---

## Phase 4: Constrained Output (Layer 4)

**Impact:** Medium | **Effort:** Low | **Risk:** Low
**Dependencies:** Phase 3 (citation extraction logic)

### 4.1 Citation density check

**File:** `app.py`

After the agentic loop, before verification:

```python
def _check_citation_density(text):
    paragraphs = [p for p in text.split('\n\n') if len(p.strip()) > 50]
    uncited = [p for p in paragraphs if not _BRACKET_REF.search(p)]
    return uncited, len(paragraphs)

uncited, total = _check_citation_density(full_text)
citation_rate = 1 - len(uncited) / total if total else 1.0
```

### 4.2 Re-generation trigger

If more than 30% of substantive paragraphs lack citations, trigger one retry:

```python
if citation_rate < 0.7 and not retried:
    retried = True
    msgs.append({"role": "assistant", "content": full_text})
    msgs.append({"role": "user", "content":
        "Your response has paragraphs without [sura:verse] citations. "
        "Add citations to every claim, or remove unsupported claims."
    })
    # Re-enter agentic loop (same code, one more pass)
    ...
```

Cap at 1 retry. If still uncited after retry, emit warning event and proceed.

### 4.3 Warning event

```python
if uncited:
    q.put({"t": "warning", "d": f"{len(uncited)} paragraph(s) lack verse citations"})
```

---

## Phase 5: Arabic Text Integration

**Impact:** High | **Effort:** Medium | **Risk:** Low
**Dependencies:** None — fully independent, parallelize with Phases 1-4

### 5.1 Source and load Arabic text

**New file:** `load_arabic.py`

Source: tanzil.net Uthmani script (public domain, widely accepted).

```python
def load_arabic():
    """Download and parse Arabic Quran text, update Neo4j."""
    # Parse tanzil.net format: sura|verse|text
    # Match to existing verseId format
    # SET v.arabic = arabic_text for each verse
```

Skip 9:128-129 (excluded in Khalifa translation).

### 5.2 Generate Arabic embeddings

**New file:** `embed_arabic.py`

Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dim, supports Arabic + English cross-lingual).

```python
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# Encode arabic text -> store as v.arabic_embedding
# Create vector index: verse_arabic_embedding
```

### 5.3 Update tools to return Arabic

**File:** `chat.py` — all 6 tool functions

Add `v.arabic AS arabic` to every Cypher RETURN clause. Include in result dicts.

### 5.4 Add bilingual semantic search

**File:** `chat.py`

Extend `semantic_search` with `language` parameter:
- `"english"` (default): uses existing `verse_embedding` index
- `"arabic"`: uses new `verse_arabic_embedding` index
- `"auto"`: detect query language, use appropriate index

### 5.5 Arabic keyword search

**New file:** `build_arabic_keywords.py`

Use `pyarabic` for Arabic root extraction. Create `ArabicKeyword` nodes or extend existing `Keyword` nodes with `arabic_form` property.

### 5.6 Frontend: bilingual display

**File:** `index.html`, `app.py`

Update `_fetch_verses` to return both texts:
```python
RETURN v.reference AS id, v.text AS text, v.arabic AS arabic
```

Update `done` event payload:
```json
{"verses": {"2:255": {"text": "English...", "arabic": "Arabic..."}}}
```

Update tooltip rendering:
```html
<div class="tooltip-arabic" dir="rtl" style="font-family:'Amiri',serif;">
  Arabic text here
</div>
<div class="tooltip-english">English text here</div>
```

Add Amiri font from Google Fonts CDN for proper Arabic rendering.

---

## Phase 6: System Prompt Refinement

**Impact:** Medium | **Effort:** Low | **Risk:** None
**Dependencies:** After all other phases

Update `SYSTEM_PROMPT` to:
- Document all new tools (typed edges, Arabic search)
- Strengthen citation mandate with verification awareness
- Add typed-edge language guidance
- Add Arabic text display instructions
- Add note about retrieval confidence levels

---

## Implementation Order

```
Week 1:  Phase 1 (typed edges) + Phase 5.1-5.2 (Arabic data load)
Week 2:  Phase 2 (retrieval gate) + Phase 5.3-5.4 (Arabic in tools)
Week 3:  Phase 3 (citation verification)
Week 4:  Phase 4 (constrained output) + Phase 5.5-5.6 (Arabic frontend)
Week 5:  Phase 6 (prompt refinement) + testing + tuning
```

Phases 1+5 can run in parallel. Phases 2+5 can overlap. Phase 3 before Phase 4.

---

## New Files

| File | Phase | Purpose |
|------|-------|---------|
| `retrieval_gate.py` | 2 | Cross-encoder reranking + CRAG fallback |
| `citation_verifier.py` | 3 | NLI-based citation verification |
| `load_arabic.py` | 5 | Arabic text sourcing + Neo4j loading |
| `embed_arabic.py` | 5 | Arabic embedding generation |
| `build_arabic_keywords.py` | 5 | Arabic root keyword extraction |

## Modified Files

| File | Phases | Changes |
|------|--------|---------|
| `chat.py` | 1,2,5,6 | New tool, typed edge enrichment, Arabic in tools, prompt update |
| `app.py` | 1,3,4,5 | Link types in graph_update, verification SSE event, citation check, Arabic in tooltips |
| `index.html` | 1,3,4,5 | Link colors, verification badge, warning banner, Arabic tooltip display |

## New Dependencies

| Package | Phase | Size | Purpose |
|---------|-------|------|---------|
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | 2 | ~80MB | Retrieval reranking |
| `cross-encoder/nli-deberta-v3-xsmall` | 3 | ~180MB | Citation entailment |
| `paraphrase-multilingual-MiniLM-L12-v2` | 5 | ~500MB | Arabic embeddings |
| `pyarabic` | 5 | ~5MB | Arabic root extraction |
