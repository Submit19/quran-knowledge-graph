# from_neo4j_yt_router_agent — Complexity-Router for QKG

Task ID: `from_neo4j_yt_router_agent` (priority 85, agent_creative, [answer-quality][opus]).

## Problem

Five questions in `data/eval_v1_results.json` underperform the 43.6 cites/q baseline by a wide margin:

| Question                                             | Cites |
|------------------------------------------------------|-------|
| "Tell me about meditation."                          | 13    |
| "Tell me about hypocrites."                          | 19    |
| "Summarize Surah Ar-Rahman (55) and its main insights." | 19 |
| "Summarize Surah Al-Fatihah (1) and its main insights." | 26 |
| "Tell me about reverence."                           | 27    |

Working questions (>40 cites): "common themes" (167), "Surah Yasin" (63), "hell" (44), "Sin" (38). The pattern is clear — abstract single-word concepts (meditation, reverence, hypocrites) and short surahs whose vocabulary is highly idiomatic (Ar-Rahman, Al-Fatihah) all under-fire because the planner reaches for `semantic_search` first. Dense retrieval on abstract concepts returns thematically adjacent but loosely cited verses; the answer formatter then drops them as off-topic.

Two NODES AI 2026 talks independently identify the fix:
- **EventKernel** (`https://www.youtube.com/watch?v=sUysPxT9YCk`, `[23:41]`) — router agent + two sub-agents, complexity classifier dispatches abstract queries away from dense retrieval.
- **Agentic GraphRAG** (`https://www.youtube.com/watch?v=fiFERKjcAXs`, `[27:06]`) — concept/keyword entry-point tool finds anchors before traversal; documented as the cure for the abstract-cluster failure mode.

Source: `data/research_neo4j_crawl/06a_yt_agentic_graphrag.md`.

## Routing rubric (the 3 buckets)

The planner classifies each query and dispatches to one of three lanes.

### 1. STRUCTURED — explicit refs, roots, or Code-19
Triggers (any one):
- Verse reference detectable by `ref_resolver.resolve_refs` (e.g. `[2:255]`, `Quran 2:255`, `Surah Al-Baqarah verse 286`, `Ayat al-Kursi`).
- Explicit Arabic root mention — three-letter root in Latin or Arabic, "root k-t-b", "ر-ح-م".
- Mathematical-miracle / Code-19 / mysterious-letters / letter-count language.

Order: `get_verse` -> `explore_surah` -> `search_arabic_root` -> `get_code19_features`. Then optional `semantic_search` for context.

### 2. ABSTRACT — concept queries (the failure mode)
Triggers (no verse ref, no root, query terms are abstract concepts): faith, meditation, reverence, hypocrisy/hypocrites, charity, prayer, patience, gratitude, repentance, mercy, justice, humility, piety, sincerity, deeds, sin, salvation, guidance, doubt, fear, hope, love, forgiveness, oppression, accountability. Surah-summary questions for short, theme-dense surahs (Al-Fatihah 1, Ikhlas 112, Ar-Rahman 55) also count — their vocabulary is idiomatic and `semantic_search` mis-fires.

Order: `concept_search` FIRST (canonical-form ER expands "patience" -> "patient"/"patiently"; see `chat.py:1023`), then `traverse_topic` (multi-keyword + 1-2 hop), then `semantic_search` only as fallback.

NEVER `semantic_search` first for abstract queries — it returns thematically adjacent but uncited verses that the answer formatter drops. The 13-27 cite cluster is exactly this.

For surah summaries always also call `explore_surah(surah_number)` early.

### 3. CONCRETE — proper nouns, narratives, events
Triggers (no verse ref but specific named entities): Moses, Pharaoh, Lot's people, Mary, the Cave, the Trumpet, Abraham, Joseph, Solomon, the Ark, Jonah, Babylon, Bani Israel, Children of Adam, the Day, hell, paradise.

Order: `search_keyword` + `hybrid_search` (BM25 catches names cleanly, dense fills gaps), then `traverse_topic`. `concept_search` may help if the name has English-stem variants ("hell" -> "hellfire").

## System prompt diff

A "Query routing rubric" block was added to both `prompts/system_prompt_free.txt` and `prompts/system_prompt.txt` immediately before the existing "EXHAUSTIVE SEARCH MANDATE" / tool-list sections. Text added (final line count 22 in free, 18 in legacy):

```
═══ QUERY ROUTING RUBRIC — read this BEFORE you pick the first tool ═══

Classify the user's question into ONE of three buckets. Pick the first tool from
that bucket's order. After 1-2 calls in the chosen lane you may broaden.

A. STRUCTURED — query has [S:V] refs, "Surah X verse Y", "Quran 2:255", an
   Arabic root, OR Code-19 / mysterious-letters / letter-count language.
   Order: get_verse, explore_surah, search_arabic_root, get_code19_features.

B. ABSTRACT — no verse ref, no root, query terms are abstract concepts
   (faith, meditation, reverence, hypocrites, patience, charity, repentance,
   mercy, sincerity, deeds, salvation, guidance, etc.) OR a short
   theme-dense surah summary (Al-Fatihah 1, Ar-Rahman 55, Ikhlas 112).
   Order: concept_search FIRST -> traverse_topic -> semantic_search LAST.
   NEVER call semantic_search first on an abstract query — dense retrieval
   on abstract concepts returns thematically adjacent but uncited verses
   that get dropped by the citation gate. concept_search expands surface
   variants via Porter-stem ER and reaches the canonical Concept layer.
   For surah summaries also call explore_surah(N) early.

C. CONCRETE — proper nouns, narratives, named events (Moses, Pharaoh,
   Mary, the Cave, the Trumpet, hell, paradise).
   Order: search_keyword + hybrid_search -> traverse_topic.
```

## Code changes

| File                            | Change |
|--------------------------------|--------|
| `prompts/system_prompt_free.txt` | Added "QUERY ROUTING RUBRIC" block above the existing TOOL CATALOGUE section (~22 lines). |
| `prompts/system_prompt.txt`     | Added a shorter rubric block above the tool list for the legacy Anthropic-paid variant (~18 lines). |
| `chat.py`                       | Added `classify_query(query: str) -> str` helper above `tool_concept_search` (returns `'structured'|'abstract'|'concrete'`). Pure function, not auto-wired into the loop — exposed for callers/tests/future hint injection. No existing code path is modified. |

No tool functions are touched. No dispatch logic changes. The system prompt drives routing; the helper is available if a caller wants to inject a classification hint as additional system context.

## Test plan

1. Smoke import: `python -c "import chat; print('chat ok')"` must pass.
2. Manual eval (recommended) — re-run `python eval_v1.py` against the 13-question set with `SEMANTIC_SEARCH_INDEX=verse_embedding_m3 RERANKER_MODEL=BAAI/bge-reranker-v2-m3`. Expected: the 5 weak abstract questions move from 13-27 cites toward 35+; the 4 working questions remain >=40.
3. Unit-style sanity for `classify_query`: meditation/hypocrites/reverence -> 'abstract'; "[2:255]" / "Surah 36 verse 5" / "count of Q in Surah 50" -> 'structured'; "Moses and Pharaoh" / "the Trumpet" -> 'concrete'.
4. Inspect a fresh trace via `app_free.py`: ask "Tell me about meditation." and confirm the first tool call is `concept_search`, not `semantic_search`.

## Risks

- **Behavior shift not enforced.** System prompts are guidance; the planner can ignore the rubric. Mitigation: rubric uses imperative language ("NEVER call semantic_search first"), placed above the tool list so it's read first.
- **Routing miscalls.** A query like "Tell me about hell" is borderline abstract/concrete; rubric labels it concrete. If `search_keyword`/`hybrid_search` over-fires it could lose the existing 44-cite baseline. Mitigation: rubric only changes ORDER, all tools still available; a 2nd-call broadening is explicitly allowed.
- **Token cost.** ~25 extra prompt lines per turn; ~5% input-token uplift. Acceptable given prompt cache.
- **Surah summary regression risk.** Working surahs (Yasin 36, Ikhlas 112) currently use semantic_search successfully; rubric still keeps `explore_surah` early which preserves their behavior.

## Rollback plan

System prompt changes are isolated in two files. To revert:
```
git checkout HEAD -- prompts/system_prompt_free.txt prompts/system_prompt.txt chat.py
```
The `classify_query` helper is a pure function with no callers in the existing code; removing it has no side effects.

## Acceptance check

- [x] `data/ralph_agent_from_neo4j_yt_router_agent.md` exists and is over 800 bytes.
- [x] `prompts/system_prompt_free.txt` updated with routing rubric.
- [x] `prompts/system_prompt.txt` updated with routing rubric.
- [x] `chat.py` exports `classify_query()` helper.
- [x] `python -c "import chat; print('chat ok')"` succeeds.
