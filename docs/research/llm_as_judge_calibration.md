# LLM-as-judge calibration — reference for Phase 4c

Written 2026-05-15, overnight research for QKG retrofit. Reference
material for Phase 4c (calibrating the v2 eval's judge against human
ratings). Pairs with `docs/PHASE_4_EVAL_PLAN.md`.

This doc is opinionated. It's not a literature survey; it's an
operator-grade brief on what to do, what to avoid, and where the
known pitfalls are.

---

## Why we calibrate

The Phase 4 eval uses a 4-dimension LLM rubric (citation accuracy,
answer completeness, tool path correctness, framing appropriateness).
Without calibration, the judge's scores are **vibes, not measurement** —
you can't claim a Phase 5 retrofit improved quality by +0.3 points
if you don't know the judge's noise floor.

Calibration is the act of validating that the judge's scores correlate
with human judgement well enough that the scores are trustworthy as
the eval's gating signal.

## The calibration procedure (recommended)

1. **Hand-rate a stratified sample.** ~30 samples is the minimum
   useful sample size for Pearson correlation; ~50 is safer if you can
   afford it.
   - Stratify across buckets so each of the 5 buckets has 6-10 samples.
   - For each sample: a single human (the operator) rates all four
     dimensions on the same 0–5 integer scale the judge uses.
   - Record each rating with a one-sentence justification (same shape
     as the judge's output). The justifications help when you tune
     the judge prompt and need to ask "did the judge miss what I saw?"

2. **Run the judge against the same samples.** Same prompts, same
   model, same temperature. Capture the judge's score + justification
   per (sample, dimension).

3. **Compute correlations.**
   - Per-dimension Pearson correlation across all samples.
   - Overall Pearson correlation across all (sample, dimension) pairs.
   - Acceptance thresholds (recommended defaults, tune to your risk
     tolerance):
     - **Per-dimension: ≥ 0.7** (strong correlation)
     - **Overall: ≥ 0.8**

4. **Iterate the judge prompt for any dimension below threshold.**
   The judge's score is its prompt's score. If `framing_appropriateness`
   correlates poorly, the prompt for that dimension is wrong. Read the
   judge's justifications, find where it diverged from yours, and
   rewrite the prompt.

5. **Record the final calibration state** in
   `data/eval/v2/calibration/calibration_<date>.json`:
   - Sample IDs used
   - Human ratings + justifications
   - Judge ratings + justifications
   - Final correlations
   - Judge prompt versions used
   - Model + temperature used

   This is the audit trail. If a future Phase 7 audit asks "are these
   scores real," you point at this file.

## Pitfalls to avoid

### Anchoring bias from the judge prompt

Most LLM-as-judge prompts include in-context examples ("here's a score
of 0, here's a score of 5"). These anchor the scale. **They also poison
calibration if they're bad anchors.** If your "score 5" example in the
prompt is a 4 by your standards, the judge will rate borderline 4s
as 5s.

Mitigation: anchor examples should be **clear extremes**, not
borderline cases. The dimension's prompt should make a 5 obviously
better than a 4 to a human reader.

### Single-dimension scoring without isolation

If you ask the judge "rate citation_accuracy and answer_completeness
in one call," the dimensions correlate spuriously. The judge will
rate them together — high citation accuracy answers tend to be high
completeness too, in the judge's response, regardless of whether
they actually are.

Mitigation: **one call per (sample, dimension)**. 4x the API cost
for 50 samples = 200 calls, ~$10-40 at Opus prices. Acceptable.
The Phase 4 plan already specifies this.

### Judging against the wrong model

If you calibrate the judge against Claude Sonnet but run production
evals against Claude Opus, the correlations don't transfer.

Mitigation: **calibrate against the same model you'll use for
ongoing evals.** Opus is more reliable for calibration but expensive
for ongoing CI runs (200 calls × $0.05 = $10 per eval run × 5 runs/day
= $50/day). Two reasonable patterns:

- **Calibrate with Opus, run with Opus.** Same model throughout.
  Predictable correlations, predictable cost. ~$50/day in active dev.
- **Calibrate with Opus, run with Sonnet.** Cheaper ongoing but
  requires a second calibration run to validate that Sonnet's
  correlations are also ≥0.7. ~$10/day in active dev.

Picking is an operator decision. Recommend Opus throughout for the
first calibration pass; switch to Sonnet if cost matters and the
re-calibration validates.

### Temperature drift between calibration and ongoing runs

Calibrate at temperature=0.0 (deterministic, judge produces the same
output for the same input). Then if ongoing runs use temperature=0.3,
the judge's scores will vary more than calibration suggests they will.

Mitigation: **calibrate at the temperature you'll use in production.**
For LLM-as-judge, temperature=0.0 is usually fine for both calibration
and production — you want the judge to be a deterministic measuring
device, not a creative rater. (Temperature variance in the THING being
judged is different and orthogonal.)

### Reverse-causation in test design

If you author questions AFTER seeing the judge's prompts, you'll
unconsciously author questions the judge handles well, and your
correlations will be artificially high.

Mitigation: **author all 50 questions before drafting the judge
prompts.** If you must iterate, treat any question you change in
response to a judge result as a calibration sample, not a production
question.

### Aggregation cherry-picking

If you compute "overall Pearson correlation" across only the dimensions
that passed and exclude the failing one, you've gamed the metric.

Mitigation: **publish all four per-dimension correlations alongside
the overall.** If `framing_appropriateness` is 0.5 and you ship anyway,
note it explicitly and treat that dimension's scores with extra
caution.

### Human-rater drift

A single human rater (the operator) will drift over a 30-sample
calibration session. Question 30 gets rated differently than question 1
because you've learned what "matters" by question 15.

Mitigation: rate in **random order** (don't go bucket-by-bucket); take
breaks; consider re-rating the first 5 samples at the end to measure
your own drift. If your self-correlation across the re-rated subset is
< 0.9, your ratings are too noisy to calibrate against.

## What "good" calibration looks like

After calibration, you should be able to claim:

- "Our judge has Pearson r = 0.82 with human ratings across 50 samples,
  stratified across 5 buckets. Per-dimension correlations: citation
  accuracy 0.85, answer completeness 0.78, tool path correctness 0.80,
  framing appropriateness 0.75. Calibrated against Claude Opus at
  temperature=0.0."

That's a defensible quality signal. Anything that produces a 0.3-point
movement in mean rubric score across 50 questions is meaningfully real
under this calibration. Anything < 0.1 is noise.

## What "uncalibrated" failure looks like

Without calibration:

- Claim: "We improved the eval score from 3.2 to 3.5."
- Reality: judge variance per sample is ±0.4. The "improvement" is
  inside the noise band.
- Audit blowback: same as the original audit's #1 — overclaiming a
  metric the methodology doesn't support.

## Phase 4c timeline (rough)

If you allocate dedicated time:

- 30 minutes: re-read this doc, the judge prompts, the example questions
- 90 minutes: hand-rate 30 stratified samples
- 30 minutes: run the judge, compute correlations
- 60 minutes (if needed): iterate one or two judge prompts, re-run
- 30 minutes: write up the calibration record

≈ 4 hours of focused operator attention. The 4-hour total assumes
correlations pass on the first or second iteration. Pessimistic case:
8 hours if multiple dimensions need iteration.

Plan it as a single half-day, not chunked sessions. The drift risk
goes up if you split rating across days.

## Tools that could help (deferred from current scope)

- **Inspect AI** (UK AISI) — built-in LLM-as-judge framework with
  calibration helpers. Could replace our hand-rolled runner if Phase
  4c reveals the runner needs heavy iteration. Tracked in the
  retrofit's "augmenting tools" list.
- **Langfuse / Phoenix (Arize)** — observability for the judge's
  responses + scores over time. Helps spot model-drift in the judge
  itself (Opus 4.7 today, Opus 5.x in 6 months may rate differently).
- **G-Eval paper** (Liu et al., 2023) — the academic predecessor of
  the calibration pattern; useful if you want to cite a reference.

## Open questions for Phase 4c (operator decides)

1. **Calibrate against Opus or Sonnet** for ongoing eval runs?
   Cost-vs-rigor tradeoff. Default recommendation: Opus throughout for
   the first pass; switch to Sonnet if cost demands and a second
   calibration confirms.
2. **Question count for calibration sample**: 30 minimum or 50 for
   safety? Recommend 50 if your time budget allows.
3. **What's the regression-block threshold** for the CI gate going
   live in Phase 4d? Suggested: 0.3 overall regression blocks; 0.5
   per-bucket regression blocks. Tunable after first month of usage.
4. **Per-bucket gating** in addition to overall? A −0.5 in ARABIC
   while overall is +0.4 should probably block. Argues for per-bucket
   gates alongside overall.

These should land in Phase 4c's commit messages so the calibration
state is defensible.

---

This doc is preparation for Phase 4c, not Phase 4c itself. When that
phase lands, treat this as the operating manual + reference, not the
plan.
