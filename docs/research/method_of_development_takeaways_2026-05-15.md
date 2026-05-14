# AIE Miami + Europe — Method-of-Development Takeaways

Date: 2026-05-15
Companion to:
- per-video docs `docs/research/yt_*.md`
- synthesis `docs/research/aie_miami_synthesis_2026-05-15.md`
- proposed tasks `data/proposed_tasks_from_yt_2026-05-15.yaml`

**Purpose.** The other research outputs ask "what should QKG *build*?"
This doc asks "what should we change about *how we work*?" — process,
harness configuration, dotfiles, code review, skills, parallel-agent
patterns, documentation discipline. None of these directly map onto a
QKG product feature; all of them could change the next 50 ticks of
operator + agent collaboration if adopted.

Each section ends with a **for QKG** translation and a concrete
**operator action** that costs <30 minutes to try.

---

## 1. Harness engineering: minimal beats baroque

**Source.** Pi (AIE Europe Day 1, ~61:21-69:00). Member of the
OpenClaw / Codex community who got fed up with Cloud Code's "context
isn't your context" problem and built Pi — a minimal coding-agent
harness with 4 tools (read, edit, bash, plan), a 1-line system prompt,
and the ability to modify itself by editing its own TypeScript
extensions.

**The empirical claim that lands hardest.** Terminal-Bench leaderboard
(Dec 2025): a minimal harness that gives the model nothing but
`send keystrokes to tmux` + `read tmux output` outperforms most
native harnesses (Cloud Code included). "Irrespective of model
family, terminal scores higher than the native harness of that model."

**Pi's design choices.**
- 1-line system prompt: "models are reinforcement-trained up the wazoo;
  they know what a coding agent is because that's what they're being
  trained on. You don't need 10,000 tokens to tell them."
- 4 tools, minimal definitions. (Compare: Cloud Code has ~20-30.)
- YOLO by default: "the approval dialog every time you call bash is
  not smart security; give the user rope to build their own."

**Pi's critique of mainstream harnesses (instructive even if you
disagree).**
- Cloud Code: system prompt changes every release; tools added/removed;
  inserts "system reminders that may or may not be relevant" into
  context; zero observability.
- OpenCode: prunes tool output after a minimum-token threshold ("that
  basically lobotomizes the model"); LSP-error injection after every
  edit ("confuses the model — humans don't check errors after every
  line, they finish the work then check").

### For QKG

QKG's harness *is* the Claude Code session the operator runs in, plus
`shared_agent.py`'s tool definitions and system prompt for the
production agent. Both are large by 2026 minimalist standards.

The "system reminder" pattern Pi complains about is exactly what fires
in this conversation every few turns. It is not always relevant. The
inverse case — the operator's CLAUDE.md instructions getting blended
with model-side post-training opinions — is the same hazard at a
different layer.

### Operator action

- Try one tick with `shared_agent.py` configured to a **5-tool subset**
  (`get_verse`, `semantic_search`, `hybrid_search`, `find_path`,
  `run_cypher`) and the EXHAUSTIVE SEARCH MANDATE stripped. Compare
  trajectory + answer quality on a single eval question to the full
  21-tool baseline. Cost: 15 minutes. Not a permanent change — a
  diagnostic.

---

## 2. Independent verification layer beats self-review

**Source.** Honor / Kodto (AIE Miami Keynote, ~167:30-180:00). Founding
engineer at Kodto; built a code-review platform on top of Claude
Code + Codex.

**The argument.** "You need an independent verification layer because
of bias from LLMs and because the systems for coding agents are
optimized for autocomplete on steroids — optimizing for actually
completing code as quickly as possible. You need a completely
independent system that comes in with an adversarial architecture."

**Three-step framework she pushes.**
1. **Define** what code quality means *for your project* — different
   from generic "best practice."
2. **Codify** the standards in a centralized context plane — agent.md
   files plus a rules system, categorized by correctness / reliability
   / quality and severity per repo / per PR.
3. **Design** the verification layer at every touch point in your
   workflow: IDE, CLI, git providers, CI/CD.

**The empirical claim.** She tested it on a deliberately too-large
1,900-LOC PR. One bug surfaced. Said this is proof the upstream
process is working — local-review-before-PR + automated PR-stage
review + adversarial agent each catch a different class of issue.

**The 400-LOC threshold she cites.** Cognitive load of effective code
review "degrades dramatically after about 400 lines of code change."

### For QKG

QKG has Claude Code reviewing Claude Code's commits all day. There is
no independent verification layer for code (only for *answers* — that's
what `citation_verifier.py` does). The pre-commit hook (pytest + ruff)
is deterministic, not adversarial. The Ralph loop's `python_test_passes`
gate (Phase 2 item 8) catches behaviour regressions but not "this is
slop."

The Phase 4 v2 eval is QKG's planned answer-quality verification layer.
There is no equivalent code-quality verification layer. Adding one
without enterprise-grade tooling (Kodto, CodeRabbit, Sourcery) is
hard — but a much cheaper version is "second-pass review by a model
different from the one that wrote the code."

### Operator action

- Pick a PR with >400 lines of code change from the past two weeks
  (there were several during Phase 3a refactors). Run Claude Code in a
  *fresh session* with no prior context, give it just the PR diff and
  the project's CLAUDE.md, and ask "find every concern: correctness,
  security, performance, maintainability." Compare what it surfaces
  against what the author already shipped. Cost: 20 minutes per PR.

---

## 3. "Implementation isn't the scarce resource"

**Source.** Ryan Leopollo (OpenAI, AIE Europe Day 1, ~66:37-78:00).
Member of technical staff at OpenAI; "banned my team from touching
their editors — work through the models only" for 9 months.

**The core claim.** "Code is free. We have an abundance of code to
solve the problems that we come across in our day-to-day. Hiring the
hands on the keyboards as part of our teams is only constrained by GPU
capacity and token budgets."

**Scarce resources Ryan names.** Human time. Human + model attention.
Model context window. That's it.

**The reframe.** "In a world where human time is scarce and required
to produce code, we have a stack rank — P0s, P1s, P2s, those P3s will
never get done. In a world where code is free and infinitely abundant,
all those P3s get kicked off immediately, maybe 4× in parallel."

**The 500-decisions point.** "To do a single patch well probably
requires 500 little decisions along the way around the underspecified
non-functional requirements that go into producing good code. The
agents have seen trillions of lines of code that make every possible
choice. So it's our job to specify those non-functional requirements
to write them down in a way the agents can see this is what it is to
do a good acceptable job."

**Concrete artefacts he names that make non-functional requirements
legible to agents.** ADRs. Persona-oriented documentation around "what
a good job looks like." Historical logs of tickets and code reviews.
Agent.md files with autocompaction.

### For QKG

QKG has plenty of artefacts (CLAUDE.md, QKG_AUDIT.md, QKG_RETROFIT_PLAN.md,
PHASE_*_PLAN.md, ADRs in `QKG Obsidian/decisions/`). The audit notes
ADRs 0013–0032 were LLM-generated from commit messages and should be
downgraded to "decision logs" — exactly Ryan's "persona-oriented
documentation" warning. Generated docs the agent then reads back as
authoritative becomes a hall of mirrors.

The audit's "What QKG is" framing is short on **non-functional
requirements**. Things like: "answers should hedge when uncertain
rather than confabulate," "Khalifa-specific positions should be
disclosed without being foregrounded," "cited verses must exist and
must support the claim." Phase 4's rubric captures these as
*measurements*; not as *agent-facing instructions* the way Ryan means.

### Operator action

- Add a short `docs/QKG_NON_FUNCTIONAL_REQUIREMENTS.md` listing the
  five-ten things QKG should never do (overclaim, confabulate citations,
  hide the Khalifa disclosure, etc.) — operator-authored, not LLM-
  generated. Link it from CLAUDE.md. Cost: 30 minutes. Becomes the
  reference doc the Phase 4 LLM-judge's "framing_appropriateness"
  dimension grades against.

---

## 4. Workflow as artefacts: plan in markdown, not in chat

**Source.** Dexter / Dax (AIE Miami Keynote, ~42:48-52:36). Coined
"context engineering"; OpenCode founder.

**The pattern.** CRISPY = Questions / Research / Structure-outline /
Plan / Implement. Each phase produces a markdown artefact. The agent
writes it; the human bot-checks it ("save the deep review for the
actual code"); both refer back to it in later turns.

**Why this works (Dexter's framing).**
- "Models absolutely freaking love horizontal plans" — DB layer →
  service layer → API layer → frontend → 1,200 lines before any
  check. Build vertically instead.
- "Do not outsource the thing. You want to give the agent every
  single opportunity to show you what it's thinking, to brain dump
  its entire understanding of the problem and what it thinks you
  want the solution to look like. And you say, *okay, why do we
  need humans in the loop at this point?* Basically: because you
  can't RL a model on architecture. The cost function of bad
  architecture is measured in months and years, not five-minute
  unit-test cycles."
- "Models love these horizontal plans — that's how you end up with
  1,200 lines of code and something is broken and the surface of
  stuff you might have to debug is quite large."

**The honest disclaimer.** "There is no magic prompt. We actually
don't publish the CRISPY prompts because the core of this is:
understand context engineering and instruction budgeting. Break it
down into smaller workflows."

### For QKG

The Phase plans (PHASE_3A_PLAN, PHASE_4_EVAL_PLAN,
PHASE_5_LOOP_TAMING_PLAN) already follow CRISPY-shape: questions ("what
problem?"), research (audit + retrofit plan), structure outline (item-
numbered plan), implementation (per-tick work). The discipline is
there for *meta-decisions*. It is mostly absent for *per-task work* —
Ralph ticks today often jump from a backlog entry directly to an
implementation patch with no intermediate planning artefact.

Phase 5 item 32 forbids "speculative abstraction without two failing
tests." Dexter's pattern adds an earlier check: "speculative
implementation without an explicit plan artefact that the operator
bot-checked."

### Operator action

- Pick one open backlog task. Before the tick runs, ask the agent to
  produce a 200-line markdown plan artefact (current state, desired
  end state, patterns to follow, design choices to call out). Bot-
  check it. Then start the tick. Compare the resulting PR to what the
  same task without a plan artefact would have looked like. Cost: one
  tick. Decide whether to make this a permanent loop-shape.

---

## 5. Parallel-agent workflows: swim lanes, not free-for-all

**Source.** Liam Hapton (OpenClaw maintainer, AIE Europe Day 2,
~177:00-191:30) and Honor Solaz (Tex Cortex, AIE Europe Day 1,
~341:00-360:00).

**Liam's swim-lane model.** Each lane is a tracked agent session;
lanes are typed by attention-budget needed:
- Lanes 1-2: low-attention refactors / test-fixing. "Just commit, just
  push them through."
- Lanes 3-4: features / bug investigations. Conversational with the
  agent; the agent reports back.
- Lane 5: P0/P1 triage on new incoming work, runs alongside an agent
  posting in a Discord channel.

"Tokens are no longer the problem. What ends up becoming the problem
is just raw compute and my brain space in order to keep an eye on all
of these sessions."

**Honor's Discord-driven development.** 1-5 active agents per channel;
channel bound to a Codex instance via ACP (Agent Client Protocol).
"Coding on the go" — pulled out a doc-to-PDF script while flying.

**Liam's git-worktree warning** (already documented in the proposed
task `from_yt_openclaw_phase5_worktree_isolation_revision`). 70-80
active worktrees = "hell" with a heavy test harness. He moved to
clone-N-times for isolation.

### For QKG

The Ralph loop runs one tick at a time today. Operator interaction is
mostly serial: review STATE_SNAPSHOT, pick a task, run the tick, watch
it. There is currently no swim-lane discipline because there is
currently no need — parallelism is one agent at a time.

But the operator is doing parallel work *across sessions*: this
research session runs in parallel with the Phase 4a eval-infrastructure
session, on different branches, on different content. That **is** a
swim-lane setup, just an informal one. The lesson from Liam is to
*name* the lanes (which one is low-attention, which one needs
operator conversational time) and to limit total concurrency.

### Operator action

- Adopt a simple swim-lane convention for parallel sessions:
  - Lane A (long horizon, low attention): the Ralph loop when it
    resumes. Just commits and pushes.
  - Lane B (medium horizon, periodic check-in): research sessions like
    this one.
  - Lane C (high attention): the active Phase work running interactively
    with the operator.
  Cap total simultaneous lanes at 3. Document the convention in
  CLAUDE_INDEX.md. Cost: 10 minutes. Pays back when the loop resumes
  alongside research sessions.

---

## 6. Skills + dotfiles as agent-legibility infrastructure

**Source.** Liam Hapton (AIE Europe Day 2, ~188:24-189:25); David Sora
Par (AIE Europe Day 1, ~47:19-47:50 — "skills over MCP" coming June);
multiple speakers across both conferences.

**Liam's setup.** Public `.skills` + `.dotfiles` repos on GitHub. Skills
include writing-technical-documentation, code-review checklist,
TDD/BDD enforcement. He runs Codex through skill-development sessions:
"Go through the codex sessions, read the logs, make improvements to
the skill." Deploys via Vercel skills.sh as the loop mechanism.

**The maintenance discipline.** "There's a process to how I manage and
maintain my skills as an engineer." Skills aren't write-once; they're
versioned, iterated, evaluated against real work.

**The skills-gym pattern.** Liam contributes to "Aga," a skills gym.
Honor (Kodto) collects skills "like Yu-Gi-Oh cards." Both treat skills
as a curated discipline, not a list of one-off prompts.

### For QKG

Claude Code skills are already available in this project (see the
system-reminder list in this very conversation: `simplify`, `diagnose`,
`tdd`, `grill-me`, `caveman`, etc.). Most are generic. There's no
QKG-specific skill — no `qkg-eval-question-add`, `qkg-tool-add`,
`qkg-cypher-review`, `qkg-phase-plan-draft`, `qkg-research-task-from-yt`.

The operator's home directory has `~/.claude/skills/` with the
yt-transcript-skill the operator used. The project's `.claude/`
already has worktree machinery. The piece missing is a project-local
skill folder that travels with the repo — for QKG-specific procedures
like "add a behaviour-asserted eval question," "audit a Cypher
denylist regression test," "draft a Phase-N plan amendment."

### Operator action

- Create `.claude/skills/` in the QKG repo with one skill: `add-eval-question`
  (procedure: read existing `data/eval/v2/<bucket>.yaml`, pick a bucket,
  draft the schema fields, link to operator's Phase 4 doc).
  Cost: 30 minutes. If it pays off, add a second skill the same way.
  Stops the "every conversation re-explains the eval schema" tax.

---

## 7. Incremental adoption: one step back, one step forward

**Source.** Radik (OpenClaw maintainer, AIE Europe Day 2, ~194:00-200:30).
Gave OpenClaw access to his email, notes, files, calendars, OS
automation, and a 3,000-page Obsidian vault — but did it in atomic
steps over months.

**The discipline.** "I see the need, I solve it in a very simple way,
and then I add more steps to it. This is also why I usually don't
have big issues that people have. If something breaks I take one small
step back, fix it, see what doesn't work, understand why it didn't
work, have a setup that it never happens again, and just take one
step further again."

**The non-discipline.** "I never did any big change but when I encounter
different Twitter threads, YouTube videos, or talking to other people
how they have it set up, I see that my setup has everything they have,
more on top of that, and also more sophisticated than what I see out
there — which was really surprising to me because I felt that it's
just one small step at a time."

### For QKG

The audit's Phase 0–11 plan IS incremental adoption. The pause-the-Ralph-loop
decision is the explicit "one small step back when something breaks"
discipline. The retrofit document's enumeration of 40 items is the
explicit "one step further again." This is independent confirmation of
the retrofit's shape, not a new pattern.

The thing Radik does well that the audit doesn't explicitly do:
**"have a setup that it never happens again."** A regression test for
each fix is the code-side version of this. The audit's Phase 1 item 10
("regression_tests/") is exactly that. Phase 5 item 21 ("forbid
speculative abstraction") is the prevention version.

### Operator action

- Each time the Ralph loop's `python_test_passes` gate (when it
  lands in Phase 2) catches a regression, before fixing, write a
  one-line note in `docs/REGRESSION_LOG.md`: *what broke, what setup
  prevents it.* This is Radik's discipline made explicit. Cost: 30
  seconds per regression. Compounds.

---

## 8. Treat evals as tests, not metrics

**Source.** Lori Voss (Arize AI, AIE Miami Day 2, ~438:00-447:30) +
Liam Hapton (AIE Europe Day 2, ~190:24-191:18) + Dexter (AIE Miami
Keynote, ~51:48-52:36).

**The reframe.** Lori: "I don't know why the eval industry decided
we were going to call these things 'eval' words from the ML industry
rather than logs and tests, which is what they are."

**Why this matters operationally.** Tests run in CI on every commit;
metrics are reported in dashboards. Tests block; metrics inform.
Phase 4 of the QKG retrofit gates landings on the v2 eval — that
is the tests-not-metrics stance. The conference content reinforces
the same stance with three independent voices.

**The leftover practice gap.** Tests have *characterisation* — when a
test fails, you know what to fix. Metrics have *reporting* — when a
metric regresses, you debate cause. Phase 4's LLM-judge with
explanations (Lori's lead diagnostic) sits in the middle: the score
behaves like a metric, the explanation behaves like a test message.
That asymmetry is operationally important — aggregate the scores for
trends, *act on* the explanations for fixes.

### For QKG

Already in Phase 4's plan. The operational discipline is:
- Use score as the gate.
- Use the explanation as the fix-list.
- Triage explanations cluster-wise (same complaint across many
  questions = systemic; one-off complaints = noise).

### Operator action

- In Phase 4's run-output JSON, add a section
  `explanations_by_cluster` that groups judge explanations by 3-word
  trigram similarity (or similar cheap clustering). The top clusters
  become the regression-test additions for Phase 1 item 10. Cost: 1
  hour when Phase 4a lands. Without this, the explanations are read
  once and forgotten.

---

## 9. Recurring meta-themes worth internalising

### "It's a process, not a model" (Liam, Ryan, Dexter — independently)

Three different speakers at three different conferences say variants
of "2025 was about token-maxing; 2026 is about not wasting them."
"It's no longer about the model or the agent. It's about the
process." (Liam, ~191:18.) The audit's framing of QKG as a
"retrofit discipline, not rebuild" is the same instinct.

### "Don't outsource thinking" (Dexter, Ryan, Honor)

Repeated specifically against "let the agent figure it out." Dexter:
"Do not outsource the thing." Ryan: "It's our job to specify those
non-functional requirements." Honor: "An independent verification
layer because the systems for coding agents are optimized for
autocomplete on steroids." The unifying claim: agents are very good
at executing the spec; humans are still the authors of the spec.

### "Make things the same so the model doesn't have to think" (Ryan)

"Make things the same as much as possible so we can limit the amount
of attention the model needs to activate." (~74:08.) Applied to QKG
this means: consistent file structure (Phase 7), consistent naming
(audit cleanup), consistent tool-return shapes (the audit's "Pydantic
for tool schemas" wish-list item).

---

## What this doc deliberately does NOT propose

- **A switch to OpenClaw / Codex / Pi as the operator's primary harness.**
  Switching harnesses mid-retrofit is exactly the kind of "Rush"-phase
  move Stefan warned against (synthesis doc, theme 2). The operator
  works in Claude Code; that's fine.
- **A self-modifying agent.** Pi's approach is elegant for a coding
  agent operating on its own implementation. QKG's agent operates on a
  Neo4j graph, not on its own source. The pattern is interesting
  context but doesn't transfer.
- **Multi-agent orchestration.** Honor's swim-lanes work for OpenClaw
  scale (10-15 maintainers, 800 commits/day). QKG is a solo project on
  a paused loop. Adopt the *naming convention*, skip the
  *infrastructure*.
- **A code-review SaaS adoption (Kodto, CodeRabbit, Sourcery).** They
  solve a real problem but the audit's Phase 5 explicitly forbids
  "speculative tooling without two failing tests that triangulate it."
  The cheap second-pass-fresh-session pattern in §2 captures most of
  the value without a paid subscription.

---

## Five things worth trying in the next week (priority order)

1. **The 5-tool subset diagnostic tick** (§1) — 15 min, single ticket.
   Outcome: data point on whether tool-bloat hurts in practice.
2. **`docs/QKG_NON_FUNCTIONAL_REQUIREMENTS.md`** (§3) — 30 min, operator-
   authored. Outcome: anchor for Phase 4's "framing_appropriateness"
   rubric dimension.
3. **Swim-lane naming convention in CLAUDE_INDEX.md** (§5) — 10 min.
   Outcome: clearer parallel-session model when the loop resumes.
4. **`.claude/skills/add-eval-question/`** (§6) — 30 min for the first.
   Outcome: stops re-explaining the eval schema across sessions.
5. **Fresh-session second-pass review on the largest Phase-3a PR** (§2)
   — 20 min. Outcome: data point on whether independent review surfaces
   anything author-session missed.

Total: ~2 hours of operator time across five experiments. Each is a
discrete diagnostic with a clear outcome signal. Each can be discarded
if it doesn't pay off.
