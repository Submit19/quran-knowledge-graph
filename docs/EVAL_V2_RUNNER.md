# Eval V2 Runner

Operator-facing guide for the behaviour-asserted eval pipeline that
replaces `eval_v1.py`'s citation-count metric. Cross-reference:
`docs/QKG_AUDIT.md` §1 (the IR scientist's critique that triggered
this rewrite) and `docs/PHASE_4_EVAL_PLAN.md` (the full plan).

## What v2 eval measures

The v1 eval scored answers by counting unique citations (a question
"passed" if the agent produced ≥10 unique `[S:V]` references).
`docs/QKG_AUDIT.md` §1 calls this out directly:

> The "77% strong (≥10 cites)" framing has been retired — citation
> count measures output volume, not output quality.

v2 replaces that existence test with **behaviour assertions** (failing
any zeroes the question) plus a **4-dimensional rubric** scored by an
LLM judge. Headline metric: `overall.mean` (0–5 weighted score) with
95% bootstrap CIs, plus per-bucket and per-dimension breakdowns.

The four rubric dimensions:

| Dimension                 | What 0–5 captures                                          |
|---------------------------|------------------------------------------------------------|
| `citation_accuracy`       | every cited verse supports the claim it appears next to    |
| `answer_completeness`     | answer addresses the explicit + obvious implicit scope     |
| `tool_path_correctness`   | sensible tools in a sensible order, no wasted calls        |
| `framing_appropriateness` | hedging matches the evidence (commit when clear)           |

Hard assertions catch what the judge tends to miss: subtly wrong
answers that read well but cite the wrong verse, skip a required tool,
or use the `run_cypher` escape hatch on a trivial lookup.

## Question format (full schema reference)

The canonical schema reference is `data/eval/v2/SCHEMA.md`. Quoted
here for convenience:

```yaml
- id: structured-001
  bucket: STRUCTURED | ABSTRACT | CONCRETE | BROAD | ARABIC
  question: "What does verse 2:255 say?"

  # Hard assertions — failing any zeroes EVERY dimension's score.
  asserts:
    cites_must_include: ["2:255"]
    cites_must_not_include: []
    tools_used_must_include: ["get_verse"]
    tools_used_must_not_include: []
    answer_substring_required: []
    answer_substring_forbidden: []

  # 4-dim rubric. Weights MUST sum to 1.0.
  rubric_weights:
    citation_accuracy: 0.4
    answer_completeness: 0.3
    tool_path_correctness: 0.2
    framing_appropriateness: 0.1

  notes: "Direct verse lookup. Expects get_verse(2:255)."
  added: 2026-05-15
  added_by: operator
```

## Authoring guidance for Phase 4b (operator brief)

Phase 4b authors the production set: **50 questions, 10 per bucket**,
in five files at `data/eval/v2/<bucket>.yaml`. The examples at
`data/eval/v2/examples.yaml` exist to validate the runner — they are
**not** the production set.

### Per-bucket failure modes (what to test)

| Bucket       | What it stresses                                          | Tools that should appear in `tools_used_must_include`                |
|--------------|-----------------------------------------------------------|----------------------------------------------------------------------|
| `STRUCTURED` | Code-19 features, explicit-reference lookups, structural queries | `get_verse`, `explore_surah`, `get_code19_features`           |
| `ABSTRACT`   | Theme questions, semantic + concept retrieval             | `semantic_search`, `concept_search`                                  |
| `CONCRETE`   | Named figures, proper nouns, keyword retrieval            | `search_keyword`, `traverse_topic`                                   |
| `BROAD`      | Surveys across surahs, breadth-not-depth                  | `search_keyword`, `hybrid_search`                                    |
| `ARABIC`     | Root + morphology + Arabic-text queries                   | `search_arabic_root`, `lookup_word`, `compare_arabic_usage`          |

### Per-question rubric weight guidance

Default weights (`0.4 / 0.3 / 0.2 / 0.1`) bias toward citation
accuracy. Override when the question's failure mode is different:

* **STRUCTURED with explicit reference** → boost `tool_path_correctness`
  (the right path is `get_verse(explicit_id)`; any deviation is wrong).
* **ABSTRACT theme questions** → boost `framing_appropriateness`
  (over-claiming on themes is the failure mode).
* **CONCRETE survey questions** → boost `answer_completeness`
  (one citation when the question implies breadth is wrong).
* **ARABIC queries** → boost `citation_accuracy` and
  `tool_path_correctness` (specialised tools must be invoked).

### When to add `cites_must_include`

* Always for STRUCTURED questions with an explicit `[S:V]` in the
  question text.
* Often for CONCRETE questions where one or two pinpoint verses are
  obviously expected (e.g. "the verse about Solomon's army of jinn"
  → `27:39`).
* Rarely for ABSTRACT/BROAD — there's no single "correct" verse.

### When to add `tools_used_must_not_include`

* Add `run_cypher` to almost every question. The escape-hatch tool
  exists for emergencies; firing it on a simple lookup is a regression.
* Add `semantic_search` to questions where an explicit reference is
  given — using semantic search when the verse is named is wasted
  effort.

## Running locally

```bash
# Make sure Neo4j is up + .env populated (ANTHROPIC_API_KEY,
# NEO4J_PASSWORD, etc).

python scripts/eval_v2.py \
    --questions data/eval/v2/examples.yaml \
    --app app_free \
    --output data/eval/v2/runs/local_$(date +%Y%m%dT%H%M%S).json

# Skip the judge (e.g. for a structural-only smoke):
python scripts/eval_v2.py \
    --questions data/eval/v2/examples.yaml \
    --judge-backend stub \
    --output data/eval/v2/runs/struct_only.json
```

Cost: at 50q production × 4 dimensions = 200 judge calls. On Opus
4.7 (~$15/1M output tokens, ~256 tokens per judge response):
~$0.80 per full run. Sonnet 4.6 is ~5× cheaper if cost matters.

## Interpreting output

The runner writes a JSON file shaped:

```json
{
  "results": [
    {
      "question_id": "structured-001",
      "bucket": "STRUCTURED",
      "trajectory": {"answer_text": "...", "tool_calls": [...], "citations": [...]},
      "asserts": {"passed": [...], "failed": [], "all_passed": true},
      "rubric": {"citation_accuracy": {"score": 5, "justification": "..."}, ...},
      "weighted_score": 4.7
    }
  ],
  "aggregated": {
    "overall": {"mean": 3.8, "ci_lower": 3.4, "ci_upper": 4.2, "n": 50},
    "by_bucket": {"STRUCTURED": {"mean": ...}, ...},
    "by_dimension": {"citation_accuracy": {"mean": ...}, ...},
    "hard_assert_pass_rate": 0.94
  }
}
```

What each metric means:

* **`hard_assert_pass_rate`** — fraction of questions where every
  assertion passed. Should approach 1.0 (asserts are *contracts*,
  not aspirations). A score of 0.6 means 40% of questions failed a
  hard check; investigate before reading the rubric numbers.
* **`overall.mean`** — headline 0–5 weighted score across all
  questions. Post-calibration target: **≥3.5**. Below 3.0 is failing.
* **`overall.ci_lower / ci_upper`** — 95% bootstrap CI bounds.
  A move from 3.5 → 3.7 is meaningless if the CIs overlap; it's
  signal if they don't.
* **`by_bucket`** — per-class means. Regressions hide in single
  buckets (e.g. ARABIC drops 2 points while overall moves 0.4); this
  surface catches them.
* **`by_dimension`** — surfaces *which kind* of failure dominates.
  A run with high completeness but low citation_accuracy tells you
  the agent is verbose-but-wrong; the fix is in retrieval, not
  generation.

## Calibration (Phase 4c preview)

LLM judges are not free of bias and not free from noise. Before
trusting the judge scores for gating decisions, Phase 4c calibrates
against human ratings:

1. Operator hand-rates 30 question-answers from a real eval run on
   each of the 4 dimensions.
2. Compute Pearson correlation between human ratings and judge
   scores per dimension.
3. Iterate on the judge prompt until **Pearson ≥ 0.7 per dimension
   and ≥ 0.8 overall**.
4. Persist the human-rated set to `data/eval/v2/calibration/` so
   future prompt edits can re-validate without spending more human
   time.

Until calibration is done, the eval workflow is informational only.

## Roadmap to Phase 4d (going live)

| Phase | Owner    | Deliverable                                                                    |
|-------|----------|--------------------------------------------------------------------------------|
| 4a    | Claude   | Runner + judge + assertions + aggregator + CI smoke + this doc (**done**)      |
| 4b    | Operator | Author 50q production set across the 5 bucket files                            |
| 4c    | Operator | Hand-rate 30 samples + iterate judge prompts to Pearson ≥ 0.7/0.8              |
| 4d    | Claude   | Flip CI to gate on `overall.mean` + per-bucket regression; retire `avg_unique_cites_per_q` |

## Where things live

| Path                                  | What                                              |
|---------------------------------------|---------------------------------------------------|
| `eval/v2/runner.py`                   | Orchestration entry — `run_eval(...)`             |
| `eval/v2/agent_caller.py`             | Drives `_agent_stream` → `TrajectoryResult`       |
| `eval/v2/judge.py`                    | 4 dimension prompts + Anthropic-backed scorer     |
| `eval/v2/assertions.py`               | Hard-assert checker                               |
| `eval/v2/aggregate.py`                | Bootstrap CIs + per-bucket / per-dim means        |
| `scripts/eval_v2.py`                  | CLI entry point                                   |
| `data/eval/v2/SCHEMA.md`              | Question YAML schema reference                    |
| `data/eval/v2/examples.yaml`          | 3 example questions for the runner smoke         |
| `data/eval/v2/runs/`                  | Gitignored — per-run JSON output                  |
| `data/eval/v2/calibration/`           | Phase 4c — hand-rated human samples              |
| `tests/test_eval_v2_*.py`             | 39 mocked tests (no real LLM tokens consumed)    |
| `.github/workflows/eval_v2.yml`       | CI smoke (informational in Phase 4a)              |

## FAQ

**Why per-question rubric weights instead of one global weight set?**
STRUCTURED questions have a single correct path; framing barely
matters. ABSTRACT theme questions have many valid framings; tool
path is less interesting. A fixed global weight either over-rewards
framing on STRUCTURED or under-rewards it on ABSTRACT. Per-question
weights are the fix.

**Why four separate judge calls instead of one combined?** Anchoring
bias — once the judge commits to a high score on one dimension, it
tends to lift adjacent dimensions. Isolated dimension calls keep each
verdict honest. Cost is 4× per question (200 calls per 50q run); on
Opus that's ~$0.80, well under the threshold where cost should
constrain design.

**Why bootstrap CIs instead of analytical CIs?** The score
distribution is unknown and likely non-normal (scores cluster at 0
and 5). Bootstrap doesn't assume a distribution. With 1,000 resamples
the CI bounds are stable to ±0.02 — well below the decision threshold.

**What happens if the agent times out or errors?** `agent_caller`
returns a `TrajectoryResult` with `error` populated. The runner
proceeds; hard assertions will likely fail (no citations, no tools
called), zeroing the score. This is the conservative-but-honest
outcome: errors look like failures, which is what they are.
