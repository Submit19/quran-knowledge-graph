# Phase 4 — Behaviour-Asserted Eval Plan

Companion to `docs/QKG_RETROFIT_PLAN.md` items 15–17 (replacing `eval_v1.py`'s n=13 existence-test with a real correctness eval). Cross-reference: `docs/QKG_AUDIT.md` §1 (the IR scientist's critique).

---

## Goal

Replace the citation-count metric with a behaviour-asserted eval that:

1. **Defines correctness explicitly** for each question, before any answer is graded.
2. **Returns a continuous quality score** per question (not pass/fail) so the Ralph loop has a real gradient to optimise against.
3. **Publishes confidence intervals** so claimed lifts don't collapse under scrutiny.
4. **Runs in CI** on every PR against `main`, with a diff-vs-baseline comment.

Headline metric becomes `mean_rubric_score` with 95% bootstrap CIs. `avg_unique_cites_per_q` is retired as a primary signal; kept only as a diagnostic.

## Starting state

The Ralph loop already produced two artefacts that get adopted forward:

- `eval_v1_bucketed.py` + `data/eval_v1_50q_bucketed.yaml` — 50 questions across 5 buckets (STRUCTURED / ABSTRACT / CONCRETE / BROAD / ARABIC × 10). Hand-curated. Each question has expected behaviour notes but no formal rubric yet.
- `eval_common.py` — shared helpers (expand_verse_range, hit_at_k, recall_at_k, average_precision_at_k) extracted from older eval scripts.

Phase 4 extends these into a behaviour-assertion eval; it does not start from scratch.

## Question schema

Each question is a YAML entry in `data/eval/v2/<bucket>.yaml`:

```yaml
- id: structured-001
  bucket: STRUCTURED
  question: "What does verse 2:255 say?"
  asserts:
    cites_must_include: ["2:255"]
    cites_must_not_include: []
    tools_used_must_include: ["get_verse"]
    tools_used_must_not_include: []
    answer_substring_required: []
    answer_substring_forbidden: []
  rubric_weights:
    citation_accuracy: 0.4
    answer_completeness: 0.3
    tool_path_correctness: 0.2
    framing_appropriateness: 0.1
  notes: "Direct verse lookup. Expects get_verse(2:255) called and the verse text in the answer."
  added: 2026-05-13
  added_by: operator
```

Field semantics:

- **`asserts`** — hard constraints. Failing any of these zeroes the rubric score for that dimension. Examples of *what to assert*:
   - `cites_must_include` — verse(s) the answer is required to cite (case insensitive on bracket form `[2:255]`).
   - `cites_must_not_include` — verse(s) that would indicate confabulation if cited.
   - `tools_used_must_include` — agent loop must invoke this tool at least once. Catches "wrong tool path" bugs.
   - `tools_used_must_not_include` — agent must NOT invoke this tool. Catches the `EXHAUSTIVE SEARCH MANDATE` over-call problem.
   - `answer_substring_required` / `answer_substring_forbidden` — coarse content checks (avoid; prefer rubric for nuance).

- **`rubric_weights`** — 4-dimensional rubric, weights sum to 1.0:
   - **citation_accuracy** — every cited verse exists; every cited verse is relevant to the claim it supports (LLM-as-judge).
   - **answer_completeness** — does the answer address the question? (LLM-as-judge against the question text.)
   - **tool_path_correctness** — did the agent take a sensible path? Not "minimum tools" but "right tools in a sensible order" (LLM-as-judge against the trajectory log).
   - **framing_appropriateness** — does the answer hedge correctly when uncertain? Avoid theological overclaim where the data is silent (LLM-as-judge).

   Per-question weights let some questions emphasise tool path (e.g. STRUCTURED), others emphasise framing (e.g. ABSTRACT).

## LLM-as-judge

Single judge call per (question, dimension, response):

- **Judge model:** Claude Opus 4.x (or Sonnet 4.x as a cost-down option).
- **Judge prompt:** specifies the rubric dimension precisely, includes the question, the model's answer, the trajectory (tool calls + results), and the assertions. Asks for a 0–5 integer score and a one-sentence justification.
- **Aggregation:** weighted sum of dimension scores → 0–5 question score → mean across questions per bucket and overall.
- **Output:** structured JSON, persisted per run to `data/eval/v2/runs/<timestamp>.json`.

Why a single judge call per dimension and not a single all-dimensions call: dimension-isolated scoring reduces the judge's anchoring bias. The cost is 4× judge calls per (question, response); at 50 questions × 4 dimensions = 200 judge calls per eval run, which at Opus rates is ~$2–5. Acceptable for a CI-gating eval.

## Calibration

Before the LLM-as-judge results are trusted, calibrate against ~30 human-rated samples:

1. Pick 30 questions stratified across buckets (6 per bucket).
2. Operator hand-rates each on the 4 dimensions, 0–5 integer.
3. Run the LLM judge on the same 30.
4. Compute Pearson correlation per dimension. Acceptable: ≥0.7 per dimension, ≥0.8 overall.
5. If a dimension's correlation is low, iterate the judge prompt for that dimension until correlation is acceptable.
6. Record the calibration baseline in `data/eval/v2/calibration_2026-MM-DD.json` so future judge-prompt changes can be re-validated.

This is one-time work, ~2 hours of operator attention. Worth it: without calibration the judge scores are vibes, not measurement.

## CI integration

`.github/workflows/eval.yml`:

- **Trigger:** push to any `phase-*` or `claude/*` branch + PR to main.
- **Steps:**
   1. Spin up a Neo4j container (using the `neo4j-migrations`-managed schema once Phase 9 lands; until then, restore from a small fixture dump).
   2. Run `python -m eval.v2 run --branch=$BRANCH --output=data/eval/v2/runs/<sha>.json`.
   3. Diff against the latest `main` baseline; post a comment to the PR with: per-bucket score deltas, overall delta, list of questions whose score moved >0.5.
   4. Block merge if overall regression >0.3 (configurable per branch via `eval.regression_threshold` in pipeline_config.yaml).

Cost: ~$2–5 per run × ~5 runs/day in active development = ~$10–25/day. Within budget for a serious project.

## Bucket rationale (existing, kept)

| Bucket | What it tests | Example question |
|---|---|---|
| STRUCTURED | Direct lookups, Code-19, explicit refs | "What does 2:255 say?" |
| ABSTRACT | Theme questions with no proper nouns | "What does the Quran say about patience?" |
| CONCRETE | Named events, prophets, places | "Where is Moses mentioned?" |
| BROAD | Surveys, summaries, theology overviews | "What is the Quran's view of revelation?" |
| ARABIC | Root + morphology + Arabic-text queries | "Show all verses with the root k-t-b" |

10 questions per bucket = 50 total. Stratified scoring makes regressions visible per-class.

## Migration

1. **Day 1:** schema lands in `data/eval/v2/`. Hand-author 50 questions (operator-led; LLM-assist OK but operator owns final wording). Lift from `data/eval_v1_50q_bucketed.yaml` where possible.
2. **Day 2:** judge prompts written; calibration on 30 samples; iterate until correlations acceptable.
3. **Day 3:** runner script (`eval.v2.run`) wired up; CI workflow added.
4. **Day 4:** baseline run on current main. Publish baseline numbers + CIs. Retire `avg_unique_cites_per_q` from `ralph_backlog.yaml::default_baseline_metric`.
5. **Day 5:** first PR through the new gate. Old `eval_v1.py` stays as legacy diagnostic (no longer gating).

## Out of scope for Phase 4

- **Property-based tests** (Hypothesis) — augmenting tools item #1, lands separately.
- **Adversarial eval** — augmenting tools item #4, Phase 6 work.
- **User feedback signal** (`:UserRating` node) — augmenting tools item #6, Phase 8 work.
- **Snapshot regression** for full answer text — augmenting tools item #7, can ride alongside Phase 4 but not gating.
- **Differential / shadow testing** — augmenting tools item #3, Phase 3a refactor support.

## Acceptance criteria for Phase 4 complete

- 50-question eval set in `data/eval/v2/` with rubric weights per question.
- LLM judge calibrated against ≥30 human ratings; correlations recorded.
- CI workflow live; first PR gated on the new metric.
- Baseline numbers + 95% bootstrap CIs published in `docs/EVAL_V2_BASELINE.md`.
- `eval_v1.py` marked legacy in its docstring; not deleted.
- `ralph_backlog.yaml::default_baseline_metric` updated.

## Open questions for the operator

1. **Judge model choice.** Opus vs Sonnet — Opus is more reliable but ~5× cost. Recommend Opus during calibration (where rigor matters most), Sonnet for ongoing CI runs.
2. **Question authorship.** Operator-led with LLM-assist, or operator-only? LLM-assist is faster but risks the eval testing what the LLM thinks is testable rather than what the operator cares about.
3. **Regression threshold for CI block.** 0.3 overall is conservative; could be tighter (0.2) or looser (0.5). Calibrate after first month of usage.
4. **Per-bucket gates.** Should a 0.5 regression in ARABIC alone block a PR even if overall is +0.4? Argues for per-bucket gates (more sensitive) vs only-overall (less noise).
