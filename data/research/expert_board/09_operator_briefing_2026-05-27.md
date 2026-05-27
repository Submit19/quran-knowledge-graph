# Expert Board — Operator Briefing (2026-05-27)

*One-page summary. Full critiques: [01-PM](01_product_manager_2026-05-27.md),
[02-Architect](02_software_architect_2026-05-27.md),
[03-ML](03_ml_retrieval_engineer_2026-05-27.md),
[04-UX](04_ux_designer_2026-05-27.md),
[05-Domain](05_domain_expert_2026-05-27.md),
[06-EM](06_engineering_manager_2026-05-27.md).
[Synthesis](07_synthesis_2026-05-27.md). [Task list](08_task_list_2026-05-27.md).*

## Collective letter grade: **C+ (weighted) / B− (unweighted mean)**

Six independent expert lenses, six grades: PM **D+**, Architect **B−**,
ML **B**, UX **C−**, Domain **B−**, EM **C+**. The unweighted mean is
B−; the weighted view drops to C+ because three of the six experts
named the same load-bearing user-visible failure (Khalifa disclosure)
as BLOCKING. The substrate has improved real-and-measurably since the
2026-05-13 audit; the *visible-from-outside* surface has not, and that
gap has now become the dominant grade-driver.

## Three BLOCKING findings

1. **The Khalifa disclosure is still not in the UI three weeks after
   the audit said it must be.** Five lines of HTML, one paragraph of
   README. The doctrinal audit (94.7% aligned, 0% drifted) is the
   proof-of-concept that the content can stand behind the disclosure.
   Hiding it makes the project look like it is pretending to be
   non-denominational; shipping it rewards the content discipline with
   the credibility it has earned. *Three experts (PM, UX, Domain)
   name this BLOCKING.*

2. **No defined audience.** Until you name *which* of "Submitter
   study tool / academic researcher tool / agent-tooling reference"
   this project is, every subsequent decision (3D viz primary or
   secondary, translation toggle, rubric weights, deployment shape,
   thumbs-up/down) gets relitigated. One paragraph, 30 minutes,
   half the open retrofit items answer themselves. *Four experts
   raise this from different angles.*

3. **The v2 eval is built but not running against the current cache.**
   The framework exists with hard assertions, four-dim judge,
   bootstrap CIs, CI workflow. The headline number has not been
   published. Until it is, the past two weeks of cache work is
   unfalsified; the original audit's "one real number" critique is
   answered with infrastructure but not yet with a number. *Three
   experts raise this; ML calls it the loop the project is built
   around but not yet closed.*

## Three things the project is doing *well*

1. **Phase 3a/3b refactor was textbook execution.** Four near-duplicate
   apps → `shared_agent.py` + thin wrappers with trajectory-baselined
   before/after capture. Four bug-A-through-D regression-test-first
   fixes. Pytest from near-zero to 209+1. The original audit's
   "biggest tech-debt item" is *resolved well*. (Architect, EM, ML.)

2. **Cache content discipline went from unknown to demonstrably good.**
   The doctrinal audit (377 entries, 94.7% aligned, 0% drifted) is a
   real engineering achievement. The capable-model baseline JSONL is
   consistently hedged on Khalifa-distinctive positions, names
   mainstream tafsir where it differs, preserves [9:128]–[9:129]
   exclusion correctly, uses Submitter terminology dominantly, has
   zero PBUH formulae and zero post-Muhammad-prophet affirmations.
   The system is *doctrinally trustworthy* inside its declared frame.
   (Domain, PM-in-grade-defence.)

3. **The orchestration pattern (advisor + fresh-local + operator-merge-
   gate) is publishable engineering practice.** The session-handoff
   snapshot discipline is better than most production-team conventions.
   The branch convention (`claude/*` agent-pushable, `feat/*` /
   `phase/*` / `docs/*` operator-merged) is the right shape for AI-
   orchestrated solo work. This is the project's strongest engineering-
   management feature. (EM F9, F10.)

## One uncomfortable truth

**The project has done the hard internal engineering and skipped the
easy external work. Most of the last 14 days' commits are
internal-artifact work that improves the operator's *model* of the
project; very little has shipped to outside-visible surface.** A
fresh outside reviewer in 21 days will land on the same `index.html`
they did on 2026-05-13: same header, same 3D galaxy, no Khalifa
disclosure, same example prompts. The engineering inside has changed
enormously. The shop window has not. That ratio is correct in the
early phases of a complex project; it inverts at some point, and the
board's judgement is that the inversion point has passed. The next
unit of operator attention has higher marginal return spent on
visible-from-outside than on invisible-from-outside. (Synthesis meta-
observation.)

## Three open questions for the operator to decide before acting

1. **Which audience?** *Submitter study tool* / *academic researcher
   tool* / *agent-tooling reference architecture* / *personal study
   tool (research artifact, not product)*. Each implies a different
   set of next-30-day tasks; the same task list cannot serve all four.
   The synthesis voice does not recommend a particular pick — that is
   the operator's call — but does recommend that the pick happen this
   week.

2. **Ralph loop: retire (Path B) or restart-with-Phase-5-trim (Path
   A)?** Either is acceptable; chronic deferral (Path C, the current
   state) is not. The EM recommends retirement; the design plan
   survives in git history. The architecture audit's item 30 cannot
   close until this decision lands.

3. **Is the eval-as-gate worth Phase 4d this month, or is it deferred?**
   Phase 4d (judge calibration + dimension-specific zeroing) turns
   the eval from a number into a real merge gate. Without it,
   arbitrary regressions can still land. Estimated 1-2 sessions of
   focused work plus ~20 hand-rated calibration samples per dimension.
   Worth pulling forward; this is what makes the eval a *use*, not a
   *display*.

## Recommended next 30 days (4 tasks, ~8 hours operator time)

- **Week 1:** Ship the Khalifa banner (1 hour) + run the v2 eval
  baseline (3 hours) + fix mobile citation tooltip (1 hour).
- **Week 2:** Audience pick (2 hours) + delete the 6 dead modules
  (1 hour).
- **Week 3-4:** Ralph decision (30 min), then either retirement or
  Phase 5 start.

End-state at day 30: every BLOCKING item closed; the eval is a gate;
the project has an audience; the UI tells visitors what it is; the
3D viz has been demoted; the 6 dead modules are gone. The remaining
backlog is *compounding engineering work* on a project whose
strategic position is settled. From C+ today to B+ in 30 days is a
tractable trajectory; the work is identified, sequenced, and small.
