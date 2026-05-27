# Expert 3 — ML / Retrieval Engineer

*Quran Knowledge Graph board critique, 2026-05-27. Reference baseline:
[docs/QKG_AUDIT.md](../../../docs/QKG_AUDIT.md) §1 (Information Retrieval
Scientist, B+ retrieval engineering, C eval rigor).*

## Who I am, and what I'm evaluating from

Eight years building retrieval systems — three at a search company, three
on RAG infra at a foundation-model lab, two consulting for enterprise RAG
deployments. I've shipped cross-encoders to production, fine-tuned BGE
checkpoints on domain corpora, and graded enough A/B sweeps to know that
"the model is better" is one of the most-falsified hypotheses in the
practice. My evaluation is on top of CLAUDE.md's headline numbers,
[answer_cache.py](../../../answer_cache.py), [retrieval_gate.py](../../../retrieval_gate.py),
[chat.py:638](../../../chat.py) (semantic_search), the v2 eval pipeline
(`eval/v2/*.py`), the QRCD reports (`EVAL_QRCD_REPORT.md`,
`HIPPORAG_REPORT.md`), and the cache audit
([cache_quality_audit_2026-05-21.md](../../cache_quality_audit_2026-05-21.md)).

## TL;DR grade: **B**

Retrieval engineering went from B+ (audit) to B in real terms because the
substrate is solid but the eval discipline that should be ratifying it is
not yet load-bearing. The good: BGE-M3 swap, multilingual reranker swap,
hybrid_search via BM25+BGE-M3+RRF, the QRCD ablation that *measured* the
legacy-reranker regression, the v2 eval with four-dimensional LLM-as-judge
and bootstrap CIs, behaviour-asserted hard checks, profile-aware reranking,
cache reranking. The bad: nearly every change in the last 14 days has
been input-side (cache content) rather than retrieval-side; the v2 eval
has not yet been *run* with the new cache; HippoRAG / PPR result was
correctly buried but the related infrastructure remains in the repo; and
the cache itself is now large enough to be a retrieval system in its own
right, but is evaluated only on input-side metrics (quality_score,
cite_validity) rather than on whether it actually *helps* downstream
answers.

## Findings

### F1 — The v2 eval has been *built* but not *run* against the baseline-injected cache. **SERIOUS.**

The eval/v2 framework ships: schema, runner, agent_caller, judge,
assertions, aggregator with 95% bootstrap CIs, CI workflow. The 62
capable-model baseline answers are now cache-injected. The v2 eval has
not yet produced a published number against the current cache state.
That means the entire premise of the last two weeks of work — "we
improved the cache content, the v2 eval will show it" — is unfalsified.

This is the discipline gap the audit (§1, IR Scientist) was complaining
about, surfacing in a new shape. The previous shape was "13 questions
isn't a number." The new shape is "62 questions and a framework that
isn't being run." Both reduce to: *we ship interventions, we do not
ship measurements of those interventions*.

Action: book one session this week. Run `eval/v2/runner.py` over the 62
baseline questions with the current cache state. Publish the headline
number with its bootstrap 95% CI and per-bucket means. Without it, the
operator is acting on faith.

### F2 — Hard-assertion zeroing on any failed check is too aggressive. **SERIOUS.**

[eval/v2/runner.py:72-81](../../../eval/v2/runner.py) treats a single
failed assertion (citation missing, substring forbidden, tool over-call)
as "every rubric dimension scores 0." That is the most-conservative
interpretation; the SCHEMA acknowledges this is provisional and "Phase
4d may refine to dimension-specific zeroing." Today it produces signal
that is over-correlated with assertions and under-correlated with the
four-dimensional judge. The state snapshot reports tools (invoked-honest
reading) of 2/57 (4%) versus tools (agent-equivalent reading) at 47/57
(82%) — that means the strict-reading scoring is throwing away almost
all of the judge's signal because the agent used `run_cypher` directly
instead of the curated tool name.

This matters because the v2 eval is supposed to be the *attractor* the
project converges on (Beck's frame from the retrofit plan). An attractor
that scores everything 0 because the agent took a sensible-but-uncurated
path is going to push the agent toward path-conformance rather than
answer-quality. That is precisely the failure mode the audit (§3, agentic
systems) called "classifier-as-prompt."

Action: implement Phase 4d's dimension-specific zeroing. citation-missing
zeroes citation_accuracy only. tool over-call zeroes tool_path_correctness
only. substring-forbidden zeroes framing only. Sum still flows through
the per-question weights.

### F3 — The reranker A/B story is now three separate findings that need a clean re-run. **SERIOUS.**

The narrative as it stands:

- **Pre-audit:** "reranker drops hit@10 50%" — measured on the *English-
  only* `ms-marco-MiniLM-L-6-v2` against QRCD Arabic queries.
- **Post-audit (CLAUDE.md):** "Multilingual reranker: hit@10 0.32 → 0.55
  vs legacy English-only on QRCD" — measured *only* on the swap, not on
  reranker-vs-no-rerank.
- **Profile-aware code** at [retrieval_gate.py:65-70](../../../retrieval_gate.py)
  cites a different finding: *"bge-reranker-v2-m3 drops hit@10 from
  0.6364 to 0.3182 on CONCRETE/ARABIC queries; it is only beneficial on
  BROAD multi-concept synthesis queries."*

So we have three claims: (a) legacy reranker hurts; (b) BGE-M3-reranker
helps; (c) BGE-M3-reranker hurts on CONCRETE/ARABIC and helps on BROAD.
Claims (b) and (c) are not obviously consistent. The profile-aware code
is *the actual production behaviour today*, but it is justified by an
internal-only ablation note rather than a published table with CIs.

Action: rerun the QRCD eval with three configurations (no rerank,
profile-blind rerank, profile-aware rerank) in one session. Publish a
table with hit@5, hit@10, MAP@10, and bootstrap CIs for each. n=22 is
small; report the CI honestly. Either the profile-aware code is validated
or it is replaced.

### F4 — The cache is now a retrieval system, but is evaluated as an output store. **SERIOUS.**

`data/answer_cache.json` is 1,607 entries / 90 MB. It has cosine
pre-filter + BGE-reranker-v2-m3 rerank at search time
([answer_cache.py:182-214](../../../answer_cache.py)). Every chat
request triggers a cache lookup and injects up to 3 entries into the
system prompt. That is a retrieval system.

Its quality is measured on:

- quality_score (per-entry heuristic over citation count, length,
  repetition flag)
- cite_validity (do the cited verseIds resolve in Neo4j)
- repetition flag
- has_arabic flag
- coverage (surah / prophet hit at least once)

None of those measure the thing that matters: *when this cache hit gets
injected into the system prompt, does the agent's answer improve?*
That is a downstream eval, and it has not been run. The cache rerank
test (`tests/test_answer_cache_rerank.py`) verifies the *mechanism*
works; it does not verify that the mechanism produces better answers.

Concretely: a top-1 retrieved cache hit at cosine 0.62 might be on a
genuinely-similar question, OR it might be the same root word at a
different semantic depth, OR it might be a question that triggers a
distracting older Khalifa-misframed answer. The 5,518/6,505 = 84.83%
cite-validity finding suggests there *is* still mis-framing in the
cache — the architecture audit's `state_2026-05-21.md` notes "older
models hallucinated impossible verseIds like `[110:9]` when surah 110
has 3 verses."

Action: design a cache-injection A/B inside eval/v2. Same 62 questions,
same agent, two runs: (a) cache enabled, (b) cache disabled
(CACHE_RERANK_DISABLED=1 + threshold=1.01). Publish weighted-rubric
deltas with CIs. If the delta is small or negative on some buckets, the
cache is doing less work than its 90 MB suggests.

### F5 — RRF in hybrid_search is reasonable, but k=60 is a literature default not a measurement. **MODERATE.**

[chat.py:1353](../../../chat.py) tool_hybrid_search combines BM25 (English
+ Arabic) + BGE-M3-EN + BGE-M3-AR via Reciprocal Rank Fusion. The default
k for RRF is conventionally 60 (from Cormack/Clarke/Buettcher 2009); the
QRCD ablation in `data/qrcd_hybrid_compare.json` should have a sweep
over k. Without that sweep, the RRF is producing reasonable output for
the wrong reason: not because k=60 is best for this corpus, but because
RRF is robust to most k choices.

The bigger concern: hybrid_search uses four ranked lists (BM25-EN,
BM25-AR, BGE-M3-EN, BGE-M3-AR) but the weights are uniform — each
contributes `1/(k+rank)`. There is no learning of which signal is
stronger for which query class. The audit's hint at "adaptive routing
prediction" (Phase 6 item 24) was supposed to validate this; it hasn't
shipped.

Action: include a k-sweep + per-signal weight sweep in the next QRCD
eval. Optuna is overkill; grid k ∈ {30, 60, 120}, weights ∈ {uniform,
2x-dense, 2x-Arabic} is 9 configurations and takes an hour.

### F6 — The HippoRAG negative result is documented; the code stays. **MODERATE.**

[hipporag_traverse.py](../../../hipporag_traverse.py) is in the repo;
`HIPPORAG_REPORT.md` is the negative-result writeup. The code is not
wired into the agent (`hipporag_search` is "full PPR retrieval, NOT
wired" per CLAUDE.md). `ppr_rerank()` is "available as helper" but I
can't find a caller.

This is the honest research move — preserve the apparatus for the next
time the question comes up. Two concerns: (a) the next contributor will
spend an hour figuring out why it is there if it is not labelled
"experimental, kept for reference, see HIPPORAG_REPORT.md"; (b) the
PageRank infrastructure inside it (`networkx.pagerank`) is a real
dependency for one demonstrably-negative experiment.

Action: add a 10-line module docstring labelling the file as "preserved
negative result, not wired, see HIPPORAG_REPORT.md." Move the file to
`scripts/experiments/` if and only if the architecture audit's package
extraction (F1 from Expert 2) lands. Otherwise leave in place.

### F7 — Cite-validity is the only end-to-end quality signal and it sits at 84.83%. **MODERATE.**

The cache quality audit found that 5,518/6,505 unique cited verseIds
resolve in Neo4j. That is the *only* measured end-to-end quality signal
on the cache content. The other metrics (citation count, length,
repetition) are heuristics over output shape.

15% of cited verses don't resolve. The audit attributed it to "cache rot
from older models hallucinating impossible verseIds." That is a valid
diagnosis but it is also one the *current* citation_verifier should
prevent. [citation_verifier.py](../../../citation_verifier.py) exists
(317 LOC), is env-gated (`ENABLE_CITATION_VERIFY=1`), uses NLI +
MiniCheck + FActScore-style atomic decomposition. The architecture
audit reports it at 0% test coverage. CLAUDE.md says it is "post-response
and env-gated." So:

- The mechanism exists.
- It is gated off by default.
- It has no tests.
- The downstream signal (cite-validity) is at 85%.

This is the same shape as F1: built but not running. The post-response
verifier should be on by default in `app_full.py` at minimum, with the
results either written to `:CitationCheck` nodes or surfaced as a
verification SSE event (per the README's SSE event protocol section, it
already has the event type defined).

Action: enable `ENABLE_CITATION_VERIFY=1` in the `app_full.py` defaults;
add a regression test against a known-bad fixture (a cited verseId
that doesn't resolve); surface the verdict in the SSE stream.

### F8 — The cache injection is a 1,500-character truncated string concatenation. **MODERATE.**

[answer_cache.py:236-244](../../../answer_cache.py) builds the cache
context by truncating any answer over 1,500 characters. The baseline
answers are 5,000–15,000 characters; the average answer length in the
cache (per the audit) is in the 3,000–7,000 range. So in practice the
cache context is *almost always* truncated.

The truncation is at character 1,500 with `"... [truncated]"`. There is
no awareness of section structure (headers, bullet points), no awareness
of which verses are cited (a truncation that drops the last 5 citations
silently weakens the cache hit), and no awareness of which paragraph is
likely most relevant to the *current* question.

Action: instead of truncate-at-char, summarise-or-chunk. Either (a) keep
the first paragraph + the citations list, or (b) at injection time, do a
second pass with the same reranker against question + paragraphs of the
hit, picking the top 2 paragraphs. (b) is the better long-term shape;
(a) is a 20-line change.

### F9 — Tool semantic_search has no per-query embedding cache. **MINOR.**

Every call to `tool_semantic_search` encodes the query via BGE-M3 (or
MiniLM if the legacy index is selected). The same query in a 15-turn
agent loop may pass through `semantic_search` multiple times via the
tool-cache, but if the *args* are slightly different ("Tell me about
charity" vs "Quran on charity"), the tool-cache misses and the embed
happens again. BGE-M3 is ~250ms on CPU per encode. Five encodes per
agent turn × 6 turns = ~7.5s of pure embed time.

Action: add a 30s-TTL query-embedding cache keyed on the raw query
string. Same pattern as the tool-result cache. ~20 lines in
`model_registry.py`.

### F10 — Cross-encoder loaded lazily, but loaded twice in worst case. **MINOR.**

[retrieval_gate.py:35-44](../../../retrieval_gate.py) and
[answer_cache.py:32-48](../../../answer_cache.py) both have a `_get_reranker`
function. The cache-side delegates to the gate-side via try/except, so
they share an instance — but the architecture audit's item 7 still flags
this as "three reranker entrypoints" because `model_registry.get_reranker`
also exists. If anyone calls `model_registry.get_reranker()` directly
the singleton is *not* shared.

In practice, today, the shared path works. Tomorrow, when someone adds
a fourth caller, the bug fires silently and ML RAM doubles. The
architecture audit's item 7 is the right fix.

## If you fix nothing else, fix this

Run the v2 eval against the current cache state and publish the headline
number. Without it, the project is steering on instruments it has built
but not calibrated. The headline failure mode of the original audit —
"one real number; the rest don't survive scrutiny" — has been answered
with a beautiful eval framework, a careful 62-question set, hard
assertions, bootstrap CIs, and a four-dimensional judge. None of that
matters until the eval runs. One session, one number, with the per-
bucket means and the 95% CI. After that the operator can defend "the
project is X% better than 2026-05-13" with evidence rather than vibes.

## Defending the B grade

The substrate engineering is genuinely good. BGE-M3, multilingual
reranker, hybrid retrieval, profile-aware adaptive routing, cross-
encoder cache rerank, hard-asserted eval, four-dim judge with CIs —
each individually is the right choice. The B (not B+) reflects that the
*measurement loop is open*: every retrieval-side decision since 2026-05-13
has been justified by *internal-only* ablations (the legacy reranker
note, the profile-aware reranker note), small-n results (QRCD's n=22
without re-published CIs), or by *future tense* claims ("the v2 eval
will show it"). The mechanism is there to close the loop in a single
session. Close it.
