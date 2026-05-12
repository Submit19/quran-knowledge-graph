# GraphAcademy Findings — QKG Research Loop

Findings extracted from GraphAcademy courses. Keyed by URL. See `neo4j_research_queue.yaml` for queue state.

---

## https://graphacademy.neo4j.com/courses/workshop-genai/

**Fetched:** 2026-05-12 (from cache `001a76fb20f4`)
**Title:** Neo4j and Generative AI Workshop (3 hrs, Workshops category)

### TL;DR
A 3-hour end-to-end GraphRAG workshop. Covers knowledge graph construction from unstructured PDFs (entity extraction + relationship mapping), vector indexes + similarity search, and building retrievers using `neo4j-graphrag` Python package + LangChain agent. Pitched at beginners.

### Key takeaways
- Uses `neo4j-graphrag` package for retriever construction (vector + cypher, text-to-cypher, vector+cypher combined). **QKG explicitly chose NOT to use this** (ADR on file) — all hand-rolled. No new decision needed.
- "Build knowledge graphs from unstructured PDF documents using entity extraction and relationship mapping" — QKG already does this for Quran verses via `build_concepts.py` (Porter-stem ER → Concept nodes). No delta.
- "Enrich knowledge graphs with structured data" — QKG does this extensively (morphology, wujuh, semantic domains, Code-19 features).
- Three retriever types shown: vector-only, vector+cypher (graph traversal post-vector), text-to-Cypher. QKG has all three via `hybrid_search`, `traverse_topic`, and `run_cypher` tools.
- LangChain-based agent pattern. QKG uses direct Anthropic API tool-use loop — more control, no framework overhead.

### Verdict
**VALIDATING.** QKG architecture is more advanced than this workshop on every dimension. No actionable gaps. Confirms existing decisions.

---

## https://graphacademy.neo4j.com/courses/genai-integration-langchain/

**Fetched:** 2026-05-12 (from cache `5349be6e8245`)
**Title:** Using Neo4j with LangChain (2 hrs, GenAI category)

### TL;DR
A 2-hour course on `langchain_neo4j` package integration: RAG/GraphRAG retrievers, text-to-Cypher retriever, and a simple LangChain agent. 10 lessons, 5 quizzes, 2 optional challenges. Uses OpenAI models.

### Key takeaways
- **`langchain_neo4j` package** — provides `Neo4jGraph`, vector retriever, graph retriever, text-to-Cypher retriever. QKG hand-rolls all of these with direct `neo4j` Python driver. The LangChain wrapper is a convenience layer we don't need (and have actively avoided per ADR).
- **Text-to-Cypher retriever pattern** — course covers schema-aware Cypher generation + few-shot examples. QKG's `run_cypher` tool is a read-only escape hatch, not a full text-to-Cypher pipeline. This is a gap we've flagged but deprioritized (no structured task exists for it yet). The few-shot examples approach for Cypher generation could improve `run_cypher` success rate if we want to expand that tool.
- **Graph retrieval module** — "Additional Data" lesson (optional) suggests enriching vector results with graph traversal. QKG's `hybrid_search` already does this via RRF + RELATED_TO traversal.
- Module 3 (Text to Cypher) includes `CypherQAChain`, schema injection, and Cypher generation tuning. These patterns are LangChain-specific but the underlying ideas (schema + few-shots → reliable Cypher) are framework-agnostic.

### Verdict
**VALIDATING with one minor note.** All architectural patterns are covered or deliberately skipped. The one transferable idea — few-shot Cypher examples to improve `run_cypher` reliability — is low priority given `run_cypher` is an escape hatch, not a primary tool. No new task proposed.

---

## https://graphacademy.neo4j.com/courses/llm-chatbot-python/

**Fetched:** 2026-05-12 (live fetch)
**Title:** Build a Neo4j-backed Chatbot using Python (2 hrs, 5 lessons + 5 challenges)

### TL;DR
Movie recommendation chatbot using GPT-3.5-Turbo, Neo4j, LangChain, and Streamlit. Covers vector retrieval tool, text-to-Cypher tool, few-shot Cypher examples for query tuning, and agent tool orchestration.

### Key takeaways
- **Few-shot Cypher examples pattern** — explicitly called out as a technique for "fine-tuning" the Cypher generation. QKG doesn't do this in `run_cypher`. Low-cost improvement: add 3-5 QKG-specific Cypher examples to the `run_cypher` system prompt context to reduce hallucinated property names / relationships.
- **LangChain Agent tool orchestration** — same framework pattern as the workshop. QKG replaces this with the Anthropic tool-use loop (20+ tools, up to 15 turns). No gap here.
- **Streamlit UI** — QKG uses custom FastAPI + Three.js SPA instead. No gap.
- **Neo4j Retriever Tool** — vector-based. QKG's `semantic_search` is the analog.
- **Text-to-Cypher Tool** — separate from the vector retriever. QKG collapses this into `run_cypher` escape hatch.

### Verdict
**VALIDATING with one minor idea.** The few-shot Cypher examples pattern for `run_cypher` is worth a small task. Proposing `from_graphacademy_cypher_fewshots` at priority 45 (low — run_cypher is rarely used, escape hatch only).

### Proposed task
```yaml
id: from_graphacademy_cypher_fewshots
priority: 45
type: cleanup
description: >
  Add 5-8 QKG-specific few-shot Cypher examples to the run_cypher tool description
  in chat.py. Examples should cover common patterns: verse lookup by ID,
  root traversal, RELATED_TO neighbors, semantic domain membership,
  morphological pattern search. Reduces hallucinated property names
  when the LLM tries to use run_cypher as an escape hatch.
  Pattern sourced from GraphAcademy llm-chatbot-python course (few-shot Cypher tuning).
acceptance:
  file_min_bytes:
    path: chat.py
    min: 1
```
