# yt_priority findings

Source: `data/research_neo4j_crawl/yt_priority_findings.md`
Handler: yt-transcript-skill

---

## kQu5pWKS8GA — Chase AI "The 7 Levels of Claude Code & RAG" (46 min)

Fetched: 2026-05-12. Transcript: 1372 snippets, English auto-generated.

### TL;DR

A tiered framework for memory architecture in Claude Code projects, from auto-memory
(Level 1) through Obsidian-backed markdown vaults (Level 4) up to agentic graph RAG
(Level 7). QKG is already operating at Level 6–7. The video validates our existing
architecture choices and provides no net-new actionable tasks.

### Key takeaways

1. **Context rot is real and the primary anti-pattern at Level 1–2.**
   Filling the context window to 1M instead of clearing sessions compounds costs
   geometrically and degrades output quality measurably (92% → 78% effectiveness by
   end of session in presenter's test). This validates the fresh-subagent orchestrator
   pattern we already run: each cron tick spawns a new agent with no prior context.
   No new task — already solved.

2. **CLAUDE.md must stay lean (high-signal only).**
   A cited study on `agents.md` found bloated rule files *reduce* LLM effectiveness
   by injecting irrelevant noise into every prompt. Rule: if a line isn't relevant to
   virtually every prompt in the project, it doesn't belong in CLAUDE.md. The lean
   `CLAUDE_INDEX.md` (~75 lines) we already use is the right pattern. No new task —
   already solved by `from_ralph_yt_01_tokenize_claudemd` (done).

3. **Obsidian vault as human-readable graph interface (Level 4).**
   Vault → master MOC index → topic articles hierarchy gives Claude Code a clear
   lookup path for hundreds of files without vector search. QKG already has
   `QKG Obsidian/` with `MOC.md`. No new task — already at this level.

4. **Graph RAG is strictly superior to naive vector RAG for relational queries.**
   LightRAG vs naive RAG: ~2–3× improvement in benchmarks (31.6 → 68.4, 24 → 76,
   etc.). QKG's 6,234-verse Neo4j graph with 51K RELATED_TO + 100K MENTIONS_ROOT
   edges already provides this; we're *beyond* LightRAG's capability since we have
   typed edges, semantic domains, morphological patterns, and hybrid BM25+BGE-M3.
   Validated, no new task.

5. **Agentic routing across multiple backends is Level 7.**
   The video describes an AI agent that intelligently routes between graph RAG DB and
   SQL/Postgres depending on question type. QKG already does this: `chat.py` has 21
   tools and the agent picks which to call. The existing tool-use loop is our router.
   Validated, no new task.

6. **Multimodal ingestion (video/image embedding) is the frontier.**
   Gemini Embedding 2 (March 2026) enables embedding video frames. For QKG's Quran
   text domain this is out of scope — there are no video/image documents to index.
   Not applicable.

7. **Data pipeline quality matters most at Level 7.**
   Deduplication, versioning, staleness detection — "the devil is in the data
   ingestion, not the retrieval." Relevant to our answer_cache (already at 1,500
   entries with 0.98 cosine dedup). Already addressed. No new task.

### Verdict

**VALIDATING.** The 7-level framework confirms QKG is at Level 6–7 (graph RAG +
agentic routing). All major architectural decisions align with the presenter's
recommendations. No new backlog tasks proposed from this source.

The one borderline-actionable note: the video emphasises that *measuring* the quality
gap between Obsidian-level and RAG-level is empirical (requires running both). QKG
has the eval harness (`eval_v1.py`) to do this, but `rerun_eval_against_current`
(priority 95, pending) is the correct vehicle — not a new task.
