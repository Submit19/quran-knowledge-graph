# QRCD Benchmark Evaluation Report

*Computed 2026-04-28. See `data/qrcd_retrieval_results.json` for raw numbers.*

## Setup

- **Benchmark**: QRCD v1.1 test split (`qrcd_v1.1_test_gold.jsonl` from
  GitLab `bigirqu/quranqa`). 238 question-passage items, 22 unique
  Arabic questions, 1,218 total gold verses across all questions.
  Median passages per question: 4. Max: 142.
- **Mode evaluated here**: pure retrieval (no agent loop, no reranking, no
  query rewriting). Each Arabic question is embedded once; top-100 verses
  are retrieved from a Neo4j vector index; metrics computed against the
  union of all gold passages for that question.
- **Question style**: Arabic (e.g. "من هم الملائكة المذكورون في القرآن؟").
- **Gold verses**: union of every passage span across all items sharing a
  question (e.g. for question 241, gold = 2:87–88 ∪ 2:97–101 ∪ 2:102–103
  ∪ 2:253–254 ∪ 5:110–113 = 16 verses).

## Results

| Metric | MiniLM<br>(verse_embedding) | **BGE-M3-EN**<br>(verse_embedding_m3) | BGE-M3-AR<br>(verse_embedding_m3_ar) |
|---|---|---|---|
| hit@5      | 0.091 |  **0.545** | 0.455 |
| hit@10     | 0.091 |  **0.636** | 0.545 |
| recall@10  | 0.001 |  **0.132** | 0.085 |
| map@10     | 0.028 |  **0.139** | 0.108 |
| mrr        | 0.073 |  **0.418** | 0.346 |

(N=22 unique questions. K-thresholds = 5/10/20/50/100 in the raw JSON.)

## Headline findings

1. **BGE-M3-EN is 5–94× better than MiniLM on every metric.** MiniLM is
   English-only, so Arabic queries land in essentially random spots in the
   embedding space. This single result confirms the research-report claim
   that `all-MiniLM-L6-v2` was the wrong default.

2. **BGE-M3-EN beats BGE-M3-AR.** Counter-intuitive at first — the Arabic
   index queries Arabic-vs-Arabic, which feels more apples-to-apples — but
   the Khalifa English text is a much *fuller* expression of the verses'
   meaning than the bare Arabic Hafs text we have. Khalifa's translation
   includes parenthetical clarifications and alternate phrasings that
   bridge the lexical gap to questions phrased in classical Arabic.
   (BGE-M3 is multilingual enough to map Arabic queries to English
   verse-text representations effectively.)

3. **Comparison to published baselines.** The Mostafa et al. paper
   ([arXiv:2412.11431](https://arxiv.org/abs/2412.11431)) reports AraBERT-base
   at MAP@10 ≈ 0.36 on the official Quran-QA passage-retrieval (PRT)
   subtask. Our BGE-M3-EN sits at 0.139. We're **roughly 38% of the AraBERT
   baseline at the retrieval layer alone**. Worth noting that AraBERT was
   fine-tuned on QRCD, while BGE-M3 is fully off-the-shelf.

4. **The headroom is enormous.** Adding cross-encoder reranking
   (`bge-reranker-v2-m3` from the research report) should push MAP@10 by
   another 0.05–0.10. Adding the full agent loop should add more. Adding
   a Quran-tuned fine-tune (post-train BGE-M3 on QRCD train) could push
   us past AraBERT.

## Caveats

- This is **retrieval-only** — no claim that we've beat AraBERT on the
  full passage-retrieval task. The agent loop adds latency but should
  also add accuracy when it works (it sometimes runs away with too many
  tool calls — see pilot below).
- We evaluate union-of-gold per question because our system produces
  free-form citations, not passage spans. This is the right framing for
  open-domain Quran exploration; it's a *different* framing than the
  original QRCD passage-extraction task.
- 22 unique questions is small. Statistical confidence is limited.
  Should re-run on the larger QRCD-v3 (Quran-QA 2023) test set when time
  permits.

## Pilot of the full-agent loop (5 items)

We ran a small pilot of the full agent (`/chat` endpoint, BGE-M3 active)
on the first 5 items of `qrcd_test.jsonl`. Result: **0/5 hit@10**.

Diagnosis from the pilot:
- All 5 items shared the same question (about angels). The agent gave
  semantically-relevant verse citations (2:97, 5:110, 66:4 — all about
  angels) but missed the specific gold spans (2:87–88, 2:97–101, etc).
  This is partly a function of the per-passage QRCD framing.
- One item ran away with 368 tool calls in 381s before hitting our
  output cap. Agent-loop guard rails need work.
- Two items returned 0 cites despite running for ~70-90s. The Arabic-input
  path through the English-trained system prompt seems to confuse
  the model into producing answers without `[X:Y]` format citations.

For the full-agent eval to be useful we'd need:
1. **Translate Arabic question → English** before sending (works around
   the Arabic-prompt issue)
2. **Tighter tool-call cap** (currently MAX_TOOL_TURNS=8 but each turn
   can call many tools in parallel)
3. **Group by question** so we evaluate union retrieval, matching what
   we did for retrieval-only

## Comparable numbers from the literature (reference)

| System | MAP@10 (QRCD) | Notes |
|---|---|---|
| BM25 baseline (Mostafa et al. 2024) | 0.18 | over Arabic verses, expanded |
| AraBERT-base + BM25 fusion | 0.36 | best result in arXiv:2412.11431 |
| Multilingual SBERT off-the-shelf | ~0.10 | reported in same paper |
| **QKG BGE-M3-EN (this run)** | **0.139** | off-the-shelf, no fine-tune |
| **QKG MiniLM (legacy)** | 0.028 | what we had before this week |

## Next steps

1. Add `bge-reranker-v2-m3` cross-encoder reranking on top of BGE-M3 retrieval
2. Fix the agent loop's runaway tool-call behavior; cap parallel tool
   calls per turn
3. Translate Arabic questions to English for the agent path; re-run
4. Try fine-tuning BGE-M3 on QRCD train (710 q-p pairs) → should beat
   AraBERT
5. Wire `/chat` to expose `[X:Y]`-format citations even when the model
   returns prose without them — fall back to raw vector hits
