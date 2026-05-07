# Eval v1 → v2 — System Prompt Update Impact

Both runs use the same 13 questions (`eval_v1.py`), same backend (OpenRouter
`gpt-oss-120b:free`), same env (`SEMANTIC_SEARCH_INDEX=verse_embedding_m3`,
`RERANKER_MODEL=BAAI/bge-reranker-v2-m3`). The only thing that changed
between runs was `prompts/system_prompt_free.txt`:

- **v1 (baseline)**: described 5 tools (`search_keyword`, `semantic_search`,
  `traverse_topic`, `get_verse`, `explore_surah`).
- **v2**: describes all 10 lean-schema tools with precedence rules, including
  the 5 new ones (`concept_search`, `hybrid_search`, `recall_similar_query`,
  `run_cypher`, `get_code19_features`).

## Headline numbers

| | v1 | v2 | Δ |
|---|---|---|---|
| Avg tool calls / question | 5.7 | 6.6 | +0.9 (+15%) |
| **Avg unique citations / question** | **33.5** | **43.6** | **+10.2 (+30%)** |
| Avg chars / question | 8,532 | 9,981 | +1,449 (+17%) |
| Avg time / question | 211s | 259s | +49s (+23%) |
| Total unique cites (13q) | 435 | 567 | +132 |

## Tool usage shift

| Tool | v1 calls | v2 calls | Δ |
|---|---|---|---|
| **concept_search** | **1** | **11** | **+10** ✅ |
| Searching keywords | 19 | 12 | −7 |
| Reasoning memory (SSE) | 7 | 13 | +6 (now every question) |
| Exploring surah | 3 | 5 (all surah qs) | +2 |
| Semantic search | 13 | 14 | +1 |
| Traversing topic | 4 | 5 | +1 |
| Citation check (post) | 2 | 0 | −2 |
| **hybrid_search** | 0 | 0 | 0 |
| **run_cypher** | 0 | 0 | 0 |
| **get_code19_features** | 0 | 0 | 0 |
| **recall_similar_query** | 0 | 0 | 0 |

## Reading

**The substitution is real.** Tool usage shifted from default-keyword to
concept-aware: agents now reach for `concept_search` first on thematic
English questions (the case Eifrem flagged: "forgiveness" should match
`forgive`/`forgiver`/`forgiveness` in one call). `Searching keywords` calls
dropped from 19 to 12, exactly because `concept_search` subsumes most of
those.

**Citation density rose 30%** despite only +0.9 tool calls / question.
Per-call yield went up because the new tools surface more relevant verses
in fewer calls.

**hybrid_search / run_cypher / get_code19_features still don't fire** —
which is the *right* outcome for this question set. They're situational:
- `hybrid_search` is for rare-lexical / proper-name queries. None of the
  13 questions have that shape.
- `run_cypher` is for aggregation / long-tail. None of the 13 require it.
- `get_code19_features` is for arithmetic / mathematical-miracle claims.
  None of the 13 are about Code-19.

To validate those tools, the next eval needs question types that match
their use cases — e.g. "How many verses mention Abraham?", "What are the
counts of Q in Surahs 50 and 42?", "Give me verses that contain the word
'kawthar'" (rare term).

## Time cost analysis

+49s/question (+23%) for +30% citations is a strong trade. Concretely
that's ~10 minutes more wall clock for the 13-question batch. The extra
time comes from:
- `concept_search` doing more work per call (joins through the
  NORMALIZES_TO -> Concept layer, fans out to all surface variants)
- More tool calls per question (5.7 → 6.6)
- More text generated (8.5K → 10K chars per answer)

If latency matters more than completeness in some context, the prompt
could nudge toward fewer tools — but for a research-style answer that's
the user's stated goal, this is a clean win.

## What v2 didn't fix (work to do)

1. **No measurement of citation correctness.** We're up 30% on citation
   *count*, but are those 10 extra citations actually relevant? Need to
   run NLI or MiniCheck verification on a sample of v2 answers and
   compare to v1.
2. **Cache hit rate didn't improve.** Almost every question still goes
   through full retrieval. The 1,500-entry cache was built on the old
   pipeline and the embeddings + cache thresholds may need refresh.
3. **Per-tool quality unmeasured.** We see `concept_search` being chosen
   more often, but we don't know whether the verses it surfaces are
   better than what `search_keyword` would have returned for the same
   question.
4. **Cited verses haven't been graded.** A small hand-grade pass (5/5,
   3/5, 1/5) on the 13×2 = 26 answers would tell us whether quality
   actually moved.

## Files

- `data/eval_v1_baseline.{json,md}` — v1 (5-tool prompt)
- `data/eval_v1_results.{json,md}` — v2 (10-tool prompt)
- `prompts/system_prompt_free.txt` — current (v2) prompt
- `eval_v1.py` — the runner

## Next steps suggested

In order of expected ROI:

1. **Hand-grade the 26 answers** (5 minutes per pair, 2 hours total). Tells
   us whether the +30% citations are signal or noise.
2. **Add 5 questions that target the unused tools** to the eval set:
   - 1 Code-19 question → tests `get_code19_features`
   - 1 aggregation question → tests `run_cypher`
   - 1 rare-Arabic-term question → tests `hybrid_search`
   - 2 follow-up questions → tests `recall_similar_query`
3. **Refresh the answer cache** by re-embedding past Q&A with BGE-M3 and
   re-running the highest-impact 100 entries through the new agent.
