# Phase 4b — Operator-collaboration prompt draft

This is the prompt skeleton for **Phase 4b: author the 50-question
production eval set**. Phase 4b is OPERATOR-LED — the agent's role is
draft-and-discuss, not decide.

Phase 4b runs AFTER Phase 4a (eval infrastructure) merges to main.
Before that, the schema, runner, judge module, and example questions
exist on main and the operator can read them.

The shape of this session is different from prior prompts:
- Operator drives the question authoring; agent acts as critic + drafter
- Agent doesn't push code; only writes to `data/eval/v2/<bucket>.yaml`
  question files
- Session can run in any direction — chat-driven, not step-by-step
- Output: a 50-question YAML set committed to a branch, with the
  agent's notes on what was tricky to question

Use this prompt when you (the operator) are ready to spend ~2-3 hours
focused on question design. It's not a "spawn and let it run"
prompt — you're in the loop the whole time.

---

## The prompt itself

```
Phase 4b: author the 50-question production eval set for QKG.

This session is OPERATOR-LED. I (the operator) decide what the eval
should test; you draft, critique, refine. You don't push to main and
you don't decide on questions unilaterally.

═══════════════════════════════════════════════════════════════════════
PART A — ORIENT
═══════════════════════════════════════════════════════════════════════

  pwd                                      # confirm QKG repo
  test -f data/RALPH_STOP && echo "loop paused"
  git fetch origin && git checkout main && git pull
  git log --oneline -10

If RALPH_STOP is missing, STOP — loop has been restarted.

Read these files for context:
  docs/EVAL_V2_RUNNER.md            # how the eval runs, what it grades
  data/eval/v2/SCHEMA.md            # the question schema
  data/eval/v2/examples.yaml        # 3 example questions to understand shape
  docs/PHASE_4_EVAL_PLAN.md         # the design + rationale
  docs/QKG_AUDIT.md §1              # why this eval exists

You should be able to summarise in two sentences: what each rubric
dimension grades, and what makes a "good" eval question vs a brittle
one. If you can't, re-read.

═══════════════════════════════════════════════════════════════════════
PART B — BRANCH
═══════════════════════════════════════════════════════════════════════

  git checkout -b phase-4b-eval-questions

Output goes to:
  data/eval/v2/structured.yaml
  data/eval/v2/abstract.yaml
  data/eval/v2/concrete.yaml
  data/eval/v2/broad.yaml
  data/eval/v2/arabic.yaml

10 questions per file. 50 total.

═══════════════════════════════════════════════════════════════════════
PART C — YOUR ROLE THIS SESSION (LISTEN CAREFULLY)
═══════════════════════════════════════════════════════════════════════

You are a research assistant. The operator decides:
  - What each question tests
  - Whether a question survives
  - The exact wording
  - The rubric weights for each question
  - When the session ends

You contribute:
  - Drafts of candidate questions when the operator asks for them
  - Critique of proposed questions (is this brittle? does it test
    the dimension the operator says it tests? would the assertions
    catch confabulation?)
  - Concrete asserts the operator might have missed (e.g. "if the
    answer cites 2:255 but doesn't cite 2:256, that's a sign the
    agent stopped too early — add cites_must_include")
  - Detection of duplicate / near-duplicate questions across buckets
  - Pushing back when a question is too easy, too brittle, or doesn't
    actually exercise its bucket's failure mode

You DON'T:
  - Decide questions on your own
  - Push to main
  - Touch any file outside data/eval/v2/*.yaml
  - Pad the question count with marginal questions to hit 50

The operator may go in any order — bucket by bucket, or jumping
around. Adapt. Track which buckets are complete on a running tally.

═══════════════════════════════════════════════════════════════════════
PART D — BUCKET INTENT (reference for the operator)
═══════════════════════════════════════════════════════════════════════

Each bucket tests a different agent failure mode. The operator and
agent agree on these intents at the start; questions are filtered
against them.

  STRUCTURED (10)
    Forces explicit-ref or Code-19 tools. Failure mode: agent goes
    to semantic_search when it should have done get_verse.
    Examples: "What does verse 2:255 say?",
              "How many times does the letter Qaf appear in Surah Qaf?",
              "What's the surah count of Surah Al-Mulk?"
    Suggested asserts:
      tools_used_must_include: ["get_verse"] or ["get_code19_features"]
      cites_must_include: [<the specific verse(s)>]

  ABSTRACT (10)
    Theme questions with no proper nouns. Failure mode: agent
    semantic-searches on a vague query and misses the keyword
    structure.
    Examples: "What does the Quran say about patience?",
              "How does the Quran discuss humility?",
              "What's the Quran's view on doubt?"
    Suggested asserts:
      tools_used_must_include: ["search_keyword"] OR ["concept_search"]
      tools_used_must_include: ["semantic_search"]   # both, ideally
      cites_must_include: ["3:200"] (or another canonical patience verse)

  CONCRETE (10)
    Named figures / places / events. Failure mode: agent
    semantic-searches when an exact-lemma keyword would have found
    more.
    Examples: "Where is Moses mentioned?",
              "What does the Quran say about the People of the Cave?",
              "What's the story of Yusuf's brothers?"
    Suggested asserts:
      tools_used_must_include: ["search_keyword"]
      cites_must_include: [<a verse the keyword search must hit>]

  BROAD (10)
    Surveys, summaries, theology overviews. Failure mode: agent
    over-uses a single tool instead of cross-referencing.
    Examples: "What's the Quran's view of revelation?",
              "Summarise Surah Al-Fatihah",
              "What does the Quran say about the nature of God?"
    Suggested asserts:
      tools_used_must_include: ["explore_surah" or "traverse_topic"]
      answer_substring_required: [<a canonical phrase that should
        appear in a complete answer>]
      framing_appropriateness weight: 0.4 (broad answers risk
        overclaim or hedge-too-much)

  ARABIC (10)
    Root + morphology + Arabic-text queries. Failure mode: agent uses
    English-keyword tools when it should reach for search_arabic_root
    or lookup_word.
    Examples: "Show all verses with the root k-t-b",
              "What's the pattern of the word رحيم?",
              "How is the root ر-ح-م used across the Quran?"
    Suggested asserts:
      tools_used_must_include: ["search_arabic_root" or "lookup_word"
                                 or "explore_root_family"]
      cites_must_include: [<verses containing the root>]

═══════════════════════════════════════════════════════════════════════
PART E — QUESTION QUALITY TESTS
═══════════════════════════════════════════════════════════════════════

For every candidate question, ask:

  1. Does it have a clear answer the system can / cannot produce?
     If you can't define what success looks like, the question is too
     vague.

  2. Are the cites_must_include verses actually correct?
     Operator's domain expertise required. If unsure, look them up
     in the live app before committing.

  3. Is the tools_used_must_include actually the right tool?
     A STRUCTURED question that doesn't need get_verse shouldn't
     require it. A CONCRETE question that has multiple valid retrieval
     paths shouldn't constrain to one.

  4. Would two different correct answers receive similar judge scores?
     If a judge would split-grade two different "correct" answers
     wildly, the rubric is wrong, not the agent.

  5. Is the question something a real user would ask?
     Synthetic questions test the system; user questions test the
     product. Aim for ~70% user-realistic, ~30% targeted-stress.

  6. Are you testing what the BUCKET says you're testing?
     A STRUCTURED question that's actually testing ABSTRACT
     understanding is misclassified.

  7. Are there duplicates across buckets?
     "What is Surah Al-Fatihah?" could fit STRUCTURED, ABSTRACT, or
     BROAD. Pick one and stick with it.

If a question fails any of these, agent should flag it. Operator
decides whether to revise or drop.

═══════════════════════════════════════════════════════════════════════
PART F — SESSION FLOW (loose)
═══════════════════════════════════════════════════════════════════════

  1. Operator names a bucket to start on (say, STRUCTURED).
  2. Operator either:
     a. Drafts a question themselves, asks agent to critique + suggest
        asserts.
     b. Asks agent to draft N candidate questions, operator picks and
        refines.
  3. Once a question passes the quality tests, agent writes it to
     the appropriate YAML file with full schema fields.
  4. After every 5 questions, agent reads back the bucket and asks
     the operator to verify coverage of the failure mode.
  5. Operator moves to next bucket when current one is satisfying.
  6. Final pass at end: agent reads all 50, flags duplicates or
     mis-bucketed entries.

Don't try to do 50 in one sitting if you're tired. Partial commits
are fine. Branch stays open until 50 are landed.

═══════════════════════════════════════════════════════════════════════
PART G — COMMIT DISCIPLINE
═══════════════════════════════════════════════════════════════════════

Commit per bucket as it completes (5 commits if all in one session,
N commits if spread):

  git add data/eval/v2/structured.yaml
  git commit -m "phase-4b: 10 STRUCTURED questions"

Or commit incrementally:

  git add data/eval/v2/structured.yaml
  git commit -m "phase-4b: 5 STRUCTURED questions (partial)"

Don't push until at least one full bucket is committed (avoids noise
in CI from incomplete YAML).

After at least one bucket pushes, CI fires the informational eval
workflow against the new questions (Phase 4a wired this up). Watch
the workflow output — it surfaces the runner's first contact with
real production questions. Bugs in the runner that the example set
didn't catch will surface here.

═══════════════════════════════════════════════════════════════════════
PART H — STOP CONDITIONS
═══════════════════════════════════════════════════════════════════════

STOP IMMEDIATELY if:
  - data/RALPH_STOP is missing.
  - Operator says "stop" or "done."
  - The agent finds itself wanting to push to main, touch
    production code, or change docs outside data/eval/v2/.
  - Three hours into the session with fewer than 20 questions
    landed. The pace isn't sustainable; finish the current bucket
    and stop. Resume in a future session.

═══════════════════════════════════════════════════════════════════════
PART I — SESSION END
═══════════════════════════════════════════════════════════════════════

Before stopping:
  1. Commit any uncommitted questions.
  2. Push: git push -u origin phase-4b-eval-questions
  3. Report to operator:
     - Per-bucket count (STRUCTURED: 7/10, ABSTRACT: 10/10, etc.)
     - Total committed
     - Questions the agent flagged but the operator overrode (worth
       reviewing later if eval results are weird)
     - Any patterns the agent noticed that might affect Phase 4c
       calibration (e.g., "the BROAD bucket questions are all
       requiring framing_appropriateness weight ≥0.3 — worth
       checking calibration on that dim specifically")

When 50 questions are landed and committed:
  - Operator merges phase-4b-eval-questions to main
  - Next session is Phase 4c (calibration)
```

---

## When to use this prompt

After Phase 4a merges and the operator is ready to spend 2-3 hours
on question authoring. Probably not the next session after 4a — the
operator should sit with the schema for a day before starting.

If Phase 4b stretches across multiple sessions (likely), the prompt
is reusable — just point at the existing branch and resume.

## What this prompt deliberately doesn't do

- **Doesn't have the agent draft all 50 questions and ask the
  operator to approve.** That's the failure mode the audit warned
  about — agent decides, operator absorbs. Inverted here: operator
  decides, agent supports.
- **Doesn't run the eval during authoring.** Phase 4c does that. 4b
  is design, not measurement.
- **Doesn't calibrate the judge during authoring.** Same reason.
- **Doesn't push code.** Only YAML.

## Notes for the operator before Phase 4b starts

1. Have the live QKG app open in a browser. Ask it the question
   you're considering BEFORE committing it as a test case. If the
   live agent gives a defensible answer, the question is testable.
   If the live agent gives a weird answer, decide whether to test
   the current behaviour (regression test) or test the desired
   behaviour (which means the test fails initially — that's fine).
2. Keep a "rejected questions" file alongside. Questions you tried
   but dropped are useful for future sessions to avoid re-treading.
3. Aim for diversity within each bucket. 10 STRUCTURED questions
   shouldn't all be verse lookups; mix in Code-19, surah metadata,
   verse counts.
4. Don't try to test EVERY tool. The eval grades whether the system
   uses the RIGHT tool for the question, not whether every tool is
   exercised. Some tools (lookup_wujuh, search_morphological_pattern)
   are niche enough they may only appear in 1-2 ARABIC questions.
   That's fine.
