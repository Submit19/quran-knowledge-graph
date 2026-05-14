# Eval v2 Question Schema

This document is the canonical reference for the YAML question format
used by `eval/v2/runner.py`. See also `docs/EVAL_V2_RUNNER.md` for the
operator-facing guide (how to author questions, run locally, interpret
output).

## File layout

```
data/eval/v2/
  SCHEMA.md            # this file
  examples.yaml        # 3 example questions exercising the runner
  <bucket>.yaml        # Phase 4b: one file per bucket (operator-authored)
  runs/                # gitignored — JSON output from each eval run
  calibration/         # Phase 4c — 30 hand-rated samples
```

Each YAML file is a flat list of question entries. One question per
list item.

## Canonical question structure

```yaml
- id: structured-001
  bucket: STRUCTURED | ABSTRACT | CONCRETE | BROAD | ARABIC
  question: "What does verse 2:255 say?"

  # Hard assertions. Each is OPTIONAL; default is an empty list.
  # Failing ANY assert zeroes every dimension's score for this question.
  asserts:
    cites_must_include: ["2:255"]              # verse_ids the answer must cite
    cites_must_not_include: []                 # verse_ids that would indicate confabulation
    tools_used_must_include: ["get_verse"]     # tools the agent must call
    tools_used_must_not_include: []            # tools the agent must NOT call (catches over-call)
    answer_substring_required: []              # substrings that must appear in the answer (case-insensitive)
    answer_substring_forbidden: []             # substrings that must NOT appear (case-insensitive)

  # 4-dimensional rubric. Weights sum to 1.0. Per-question — some
  # questions weight framing higher, some weight tool path higher.
  rubric_weights:
    citation_accuracy: 0.4
    answer_completeness: 0.3
    tool_path_correctness: 0.2
    framing_appropriateness: 0.1

  notes: "Direct verse lookup. Expects get_verse(2:255) and the
          verse text in the answer."
  added: 2026-05-15
  added_by: operator
```

## Field semantics

### `id` (required)

Stable identifier. Convention: `<bucket-lowercase>-<3-digit-index>`,
e.g. `structured-001`, `arabic-007`. Used in run output JSON and in CI
comments — keep it short and grep-able.

### `bucket` (required)

One of: `STRUCTURED`, `ABSTRACT`, `CONCRETE`, `BROAD`, `ARABIC`.

Buckets cluster questions by retrieval failure mode (see
`docs/QKG_AUDIT.md` §1 and `docs/EVAL_V2_RUNNER.md`). Aggregated
results report per-bucket means so regressions in one class don't hide
behind overall averages.

### `question` (required)

The natural-language prompt sent to the agent. UTF-8; Arabic is fine.

### `asserts` (optional)

Hard constraints. If any assert fails, every dimension's score for this
question is zeroed (most conservative — Phase 4d may refine to
dimension-specific zeroing).

All six assert types are list-valued. Empty list = no constraint. The
checker is case-insensitive for substring asserts and exact-match
for verse_id / tool_name asserts.

| Field                          | Meaning                                                        |
|--------------------------------|----------------------------------------------------------------|
| `cites_must_include`           | every listed verse_id must appear in the answer's citations    |
| `cites_must_not_include`       | none of the listed verse_ids may appear                        |
| `tools_used_must_include`      | every listed tool name must be called at least once            |
| `tools_used_must_not_include`  | none of the listed tools may be called (catches over-call)     |
| `answer_substring_required`    | every listed substring must appear in the answer text          |
| `answer_substring_forbidden`   | none of the listed substrings may appear in the answer text    |

Verse_ids use `surah:verse` form (e.g. `2:255`). The runner extracts
citations from the answer text via the `[surah:verse]` bracket pattern
emitted by the agent.

### `rubric_weights` (required)

Weights for the 4 LLM-as-judge dimensions. Must sum to 1.0 (the runner
validates this and raises if it doesn't, within float tolerance).

| Dimension                  | Scores 0–5: …                                                   |
|----------------------------|-----------------------------------------------------------------|
| `citation_accuracy`        | how accurately do the cited verses support the claims?         |
| `answer_completeness`      | does the answer fully address the question?                    |
| `tool_path_correctness`    | did the agent take a sensible retrieval path?                  |
| `framing_appropriateness`  | does the answer hedge correctly when uncertain?                |

Default weights (`0.4 / 0.3 / 0.2 / 0.1`) bias toward citation
accuracy — the headline failure mode under the v1 eval. Per-question
overrides are encouraged; see authoring guidance in
`docs/EVAL_V2_RUNNER.md`.

### `notes` (optional but recommended)

Free-form. Captures *why* this question is in the set. Helps the next
operator understand the intent when the question's behaviour changes
months later.

### `added`, `added_by` (optional)

Provenance. ISO date + author handle. Useful for archaeology when a
question starts failing.

## Schema versioning

Schema breaking changes get a new top-level key (`schema_version: 2`)
on the YAML file. Until then, all question files are implicitly
`schema_version: 1`. The runner pins to v1 and rejects unknown keys
on each question entry.
