# Task Plan — Autonomous Run from 2026-04-27

Six engineering tasks identified by the deep-research agent (RESEARCH_2026-04-27.md),
ordered by risk/effort. Status as of plan creation: 1, 2 done; 3 running.

## Task 4 — Run system against QRCD benchmark

**Why:** Move QIS from "internal 218 questions" to a scholarly benchmark. The
QRCD (Quran-QA 2022) and QurSim datasets are the standard. This gives us a
shareable number that compares to AraBERT-base MAP@10 of 0.36 reported in
[arXiv:2412.11431](https://arxiv.org/abs/2412.11431).

**Plan:**

1. Download the QRCD dataset from the Quran-QA 2022 shared task. Format is JSON
   per-question with answer spans referencing verse passages.
   Source: https://sites.google.com/view/quran-qa-2022/dataset
   Expected files: `qrcd_v1.2_train.jsonl` and `qrcd_v1.2_test.jsonl`.

2. Build `eval_qrcd.py`:
   - Load QRCD test set
   - For each question, run via the `/chat` endpoint of `app_free.py`
   - Parse `[X:Y]` citations from response
   - Compare to gold answer-passage verse spans
   - Compute MAP@10, MRR, Recall@10, exact-match accuracy
   - Output `data/qrcd_results.json`

3. Run a sample batch of 30 questions first (for ~1h pace), then full set.

4. Write `EVAL_REPORT.md` summarising metrics + comparison to published baselines.

**Risk:** medium. QRCD is in Arabic; our agent is bilingual but optimized for
English queries. May need translation of questions to English first; or might
work directly if BGE-M3 cross-lingual is in place by the time we run.

**Acceptance:**
- Sample run produces a valid metrics JSON
- Report compares our numbers to published baselines (AraBERT 0.36 MAP@10)
- If we beat baseline at all, that's a publishable claim

## Task 5 — Sefaria-inspired Quranic citation NER / ref-resolver

**Why:** Sefaria's "Linker" auto-resolves Hebrew text-citations on third-party
sites. We can do the same for Arabic + English Quranic citations. This is
the highest-external-utility task — third-party blogs/tafsir sites quoting
verses could auto-link to our KG.

**Plan:**

1. Two-mode implementation:
   - **Regex-first** for the easy cases:
     - `[X:Y]` and `[X:Y, X:Y, ...]` brackets
     - `Quran X:Y`, `Surah X verse Y`, `(X:Y)`, etc.
     - `Surah Al-Baqarah verse 255`, `Ayat al-Kursi`, etc. (named verses)
   - **NER-style** for fuzzier cases: spaCy or a small fine-tuned model that
     spots "verse 255 of Al-Baqarah" or partial matches.

2. Build `ref_resolver.py` exposing:
   ```python
   def resolve_refs(text: str) -> list[Match]:
       # Returns [{start, end, raw, canonical_id, verse_id, confidence}, ...]
   ```

3. Build a JS widget `quran_linker.js` (single-file bundle) that:
   - Takes a webpage's text content
   - Highlights detected citations as `<a class="quran-ref" data-verse="X:Y">`
   - On click, opens a tooltip with the verse text fetched from our `/api/verse/X:Y`
   - Configurable target URL

4. Add `/api/verse/<verseId>` endpoint to `app_free.py` (read-only, 1 verse).

5. Test on a sample of 20 known tafsir blog posts.

**Risk:** medium. Named-verse coverage is fuzzy; we'll start with high-precision
regex and add NER later.

**Acceptance:**
- Resolver achieves >95% precision on a curated test set of 50 sentences
- Widget loads and highlights on a static HTML page
- API endpoint serves verses correctly

## Task 6 — HippoRAG-style Personalized PageRank traversal

**Why:** Our reasoning-memory graph already has the topology (Query →
ReasoningTrace → ToolCall). HippoRAG (OSU-NLP-Group) uses PPR over a similar
structure for cheap multi-hop retrieval. Could meaningfully improve answers
on multi-step questions.

**Plan:**

1. Build `hipporag_traverse.py`:
   - Take a user query, find the top-k similar past Query nodes via vector index
   - Build a small subgraph of those queries + their ToolCalls + the verses they retrieved
   - Run Personalized PageRank seeded at the matching queries
   - Return the top-K verses by PPR score
   - Compare to plain semantic_search top-K

2. Wire as a new tool: `tool_traverse_past_reasoning(query)` — gated on cache
   already containing similar queries.

3. Run an ablation:
   - Same 30 QRCD-style questions
   - Compare semantic_search-only vs semantic_search + PPR-traversal

4. If PPR adds measurable lift (>5% on Recall@10 or MAP@10), wire it as a
   default for queries where similar past queries exist.

**Risk:** medium. PPR is well-studied but we don't have a big enough reasoning
graph yet (1500 cached entries, ~1500 queries). May not have signal. If so, we
defer to when the graph is bigger.

**Acceptance:**
- Tool runs cleanly on a sample query
- Ablation produces a clear yes/no on whether PPR helps
- If yes, wire it in; if no, keep code as a feature flag and document why

## Phase 2 — Source re-exploration (after 6 tasks)

For each high-value source in RESEARCH_2026-04-27.md, do a deeper read and pull
out anything new that could become a task:

1. **Sefaria-Project repo** — read schema.json, look at the topic ontology,
   the linker module, the export format. Pull out 2-3 architectural patterns.

2. **MiniCheck repo + LLM-AggreFact paper** — see what claim decomposition
   strategies they use. Our regex-based decomposition is crude.

3. **HippoRAG repo** — read implementation. Understand exactly how PPR
   personalization vector is constructed.

4. **GraphRAG / LightRAG / LazyGraphRAG comparison paper** — extract the
   decision tree for "when does graph-RAG actually help."

5. **Tarteel QUL** — look at what data they expose, see if we can use
   their crowdsourced topic tags.

6. **Doha Historical Dictionary RAG** — read the diachronic methodology
   for our etymology layer.

Output: `RESEARCH_2026-04-27_DEEP.md` with new task candidates.

## Phase 3 — Implement the new tasks

Plan and execute the new tasks discovered in Phase 2. Same sequential pattern.

---

## Working principles for this autonomous run

- Commit + push after each task lands cleanly
- If a task fails or is too risky to land overnight, write a deferred note
  and move to the next
- Never break the live cache (1500 entries) or the live `embedding` property
  (the agent depends on it)
- Add new things in parallel rather than mutating in place
- Stay env-gated where possible so user can A/B test on return
