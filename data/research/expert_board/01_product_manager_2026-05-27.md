# Expert 1 — Product Manager / Strategist

*Quran Knowledge Graph board critique, 2026-05-27. Reference baseline: [docs/QKG_AUDIT.md](../../../docs/QKG_AUDIT.md) §6 (Product Strategist), which graded product vision C− on 2026-05-13.*

## Who I am, and what I'm evaluating from

I've spent eleven years shipping consumer and prosumer search/study products
— two stints inside Google (Knowledge Graph adjacent), a B2B SaaS for academic
researchers, and four years running product for a religious-text app with
a six-figure DAU. I've reviewed two dozen "AI-powered study tool" pitches
in the last eighteen months. My read on this project comes from CLAUDE.md,
[README.md](../../../README.md), the cache audit, the baseline JSONL, the
sibling audit on `claude/architecture-audit-2026-05-22`, the doctrinal audit
on `claude/doctrinal-audit-2026-05-22`, and a hard look at where the
project's energy has been going commit-by-commit over the last 60 days
(286 commits, 99 in the last 14). I have no theological stake. I evaluate
product on three axes: does it solve a real problem, for a named user,
defensibly?

## TL;DR grade: **D+**

The original audit gave the product dimension a C−. I am moving it down a
half-grade. Engineering quality, eval rigor, and content discipline have
all improved substantially since 2026-05-13. Product clarity has actively
regressed — more surface area, more apps, more tools, more research
artifacts, and no closer to a defined audience than three weeks ago. This
is not a sustainability complaint about the operator; it is a strategic
complaint that the project's *artifact graph* is now an order of magnitude
denser than its *user graph*, and the operator's working-agreement
(`~/.claude/working_agreement.md`) is now the de-facto product spec. That
is a meta-system gaining mass faster than the product (audit §7 finding),
re-emerging as the product itself.

## Findings

### F1 — Audience is still undefined three weeks after the audit said so. **BLOCKING.**

The README opens with *"An AI-powered Quran study tool"* and never names who it
is for. The original audit (§6) proposed three plausible audiences —
Submitters, academic Quranic-studies researchers, agent-tooling developers
— and asked for a pick. Three weeks on, still no pick. The implication
shows up everywhere: four deployment modes (`app.py`/`app_full.py`/
`app_lite.py`/`app_free.py`), 20 tools, eval rubric tilted toward citation
correctness AND tool-path correctness AND framing AND completeness — i.e.
optimising for all four because there is no clarified job-to-be-done that
would tell you which two to drop.

Action: spend one hour. Pick *one* of the three audiences. Write a 200-word
"who/what/why" alongside `CLAUDE_INDEX.md`. Defer all multi-audience UX
work until the chosen audience is shipping value. The architecture audit's
item 9 (README rewrite) is the natural carrier.

### F2 — The 3D visualisation is the project's logo but not its product. **SERIOUS.**

[index.html](../../../index.html) opens with a 6,234-node Fibonacci sphere
and WASD fly controls. The README front-page screenshot is the sphere. The
cache audit shows the project actually *delivers* on citations-in-prose —
the top-10 cited verses are all theologically meaty ([6:55], [2:74],
[2:255], [2:177], [9:60]) and the baseline answers are 5,000–15,000-char
prose with inline `[S:V]` bracket references. The interaction model that
generates the value is *chat with hoverable citations*. The 3D sphere is
where the marketing energy lives.

This split is doing real damage. The audit (§6 finding 2) called the 3D
viz "demo-ware and dubious primary UX." It is still primary. The right
demotion is item 33 of `docs/QKG_RETROFIT_PLAN.md` (3D viz → optional
toggle); operator has not actioned it. Until the chat surface is treated
as primary, the project will continue to over-invest in an idiom that
impresses on a first screenshot and gets ignored on the second visit.

Action: demote the sphere to a toggle on the chat page. Make the default
landing experience *the conversation*. The architecture supports this; it
is a 30-line frontend change.

### F3 — The Khalifa disclosure is still buried, three weeks after it was promised in Phase 0. **BLOCKING for credibility.**

I grep'd `index.html`: zero mentions of Khalifa, Submitter, or "this is one
translation among many." The README mentions Khalifa twice, both deep in
the "Translation Context" section near the bottom (line 411). The audit
§5 (Religious Studies Scholar) called this out on 2026-05-13. The retrofit
plan's Phase 0 acceptance criteria explicitly require a Khalifa paragraph
"in the first screen of content." The architecture audit's item 11 (HIGH,
medium effort) flags the UI banner as still open. Three weeks. This is
the single largest *unfixable-by-eval* risk the project carries — the
content is doctrinally aligned ([doctrinal audit](../../doctrinal_audit/operator_briefing_2026-05-22.md):
94.7% aligned, 0% drifted) and yet the UI gives a first-time visitor
*zero* signal that they are reading a non-mainstream translation. Every
day this stays unshipped is reputational debt accruing at a rate the
project's defences (eval, cache, citation verification) cannot pay down.

Action: Today. Two-line YAML in the frontend header. One paragraph in
README §About. Don't wait for Phase 8's translation toggle. The disclosure
is a five-line change blocked by nothing.

### F4 — The artifact graph is growing faster than the user graph. **SERIOUS.**

In the last fourteen days (`git log --since="14 days ago"`):

- ~57-question advisor-generated baseline
- Cache schema enrichment + BGE-M3 re-embedding
- Cache quality audit + prune passes 1 and 2.5
- Coverage analysis + Shuaib matcher fix
- Architecture audit (4 passes + synthesis)
- Doctrinal audit (4 passes + briefing)
- Phase 5 Ralph loop taming design doc
- Two parked branches awaiting validation against the new baseline

That is a *lot* of internal-facing research output. Zero of it changed
what a user sees. Compare against the user-facing diff in the same window:
the Khalifa banner is not yet up; the 3D viz is not yet demoted; the
system prompt is not yet trimmed; no translation toggle; no thumbs-up/down
on answers (retrofit plan item 138 in the supporting-tools section, not
yet started). The operator is paying — in attention, in compute, in cache
storage — for research-as-product. A product manager looking at this graph
would call a freeze on internal artifacts and force the next four to six
sessions to be user-visible. The doctrinal audit is the right kind of work
(it ships a regression guard against future cache drift); the architecture
audit's 34-item list mostly is not (it audits debt without paying any of
it down — separate ticket-creation step).

Action: Define a "user-visible delivery" gate. Any new branch must land
either (a) a user-visible change, (b) a regression test that prevents a
known user-visible regression, or (c) a measured quality lift on the v2
eval. Internal audits that produce more audits do not satisfy the gate.

### F5 — Sefaria-style "this is reference architecture" is being modelled, not stated. **MODERATE.**

`ref_resolver.py` (459 LOC) is described in CLAUDE.md as "Sefaria-style
citation NER" and powers a separate `/api/resolve_refs` endpoint + a
`/quran_linker.js` widget. Both look usable as a standalone library —
parse `[2:255]`, `Surah Al-Baqarah verse 286`, Arabic `سورة البقرة آية
255`, ranges, lists. This is a *real* moat: there is no general-purpose
Quranic-reference NER package on PyPI that handles Arabic + English +
named-surah forms with the same parser. The agent-tooling-developer
audience the audit named (§6) would value this enormously.

Today this is a side-effect of building the chat product. If the operator
picked the agent-tooling audience, this becomes the headline ("we ship
the Quranic-reference parser and an MCP server backed by a real graph");
the chat app becomes the reference implementation, not the product. The
retrofit plan's "Expose QKG as an MCP server" recommendation in the
augmenting-tools section is the same finding from a different angle.

Action: hold this in the audience-pick decision (F1). If "agent-tooling
developer" is the choice, productise `ref_resolver` + an MCP server as
the public face within four weeks. Otherwise leave it as internal.

### F6 — The product has no thumbs-up/down feedback loop, so it cannot learn from real users even if it had any. **MODERATE.**

The retrofit plan's compounding-tools list item 6 ("User feedback signal —
thumbs up/down on answers → `:UserRating` node. Phase 8.") is unbuilt.
The graph schema does not yet have a UserRating node. Until this is in,
the project has *no* mechanism for distinguishing a 9,000-character
beautifully-cited bad answer from a 2,000-character right-on-target good
one. The 94.7% doctrinal alignment number is encouraging but it is a
*content* metric, not a *fit* metric. A user might rate `expansion-001`
five stars and `expansion-002` zero stars; today the system would not
know.

This is a four-hour build (one new node label, one POST endpoint, one
button per chat bubble) that compounds for the lifetime of the project.
It also creates the only valid alternative to the operator-as-sole-judge
problem: a user feedback graph is observably independent of operator
preference.

Action: Build the thumbs-up/down node + endpoint + button in a single
session. Defer any analytics dashboard. Just collect the signal.

### F7 — Pricing / monetisation / sustainability are invisible. **MODERATE.**

The free version (`app_free.py`, Ollama/OpenRouter) is the operator's
preferred path and produces the cache content. The paid versions exist
but `app.py` / `app_full.py` / `app_lite.py` each commit ~$0.01-$0.35
per question. There is no "who pays" model surfaced anywhere. The audit
(§6) called this out: *"If 'research project,' say so and stop building
like a product."* The doctrinal audit found the cache content is mostly
mergeable; the question of who runs the queries that fill the cache
forward is unaddressed.

Three honest options:

- **Personal study tool / open-source reference project.** State that.
  Stop building toward broader release. Save operator attention.
- **Niche app for the Submitter community.** ~10K worldwide, a thumbs-up
  feedback loop (F6) becomes the discovery channel, monetisation is
  pay-what-you-want.
- **Reference architecture / MCP server.** Sell to other dev shops as
  template + curated dataset. F5 is the path.

Action: in the same hour as F1, pick one. Pricing follows the audience;
audience cannot follow pricing.

### F8 — The eval set itself is now the only first-class user. **MODERATE.**

This is the deepest one. The v2 eval (62 questions, four-dimensional LLM
judge, hard-asserted citations) is the most-developed user of the system.
Every recent commit serves it: cache improvements raise its scores, the
baseline JSONL feeds back into the cache, the architecture audit and
doctrinal audit are both downstream of "what would make the eval
trustworthy." A human user has not been put through the system in the
same disciplined way the eval has.

This is fine for one or two more cycles. It becomes pathological if it
continues: a system optimised exclusively for a 62-question eval set is a
system that hits 100% on those 62 questions and degrades on the 6,234
verses worth of other things a user might ask. The cache audit's "118
entries with zero citations" and "94 entries with repetition" suggest the
edges of the input space are quietly accumulating rot while the centre
gets polished.

Action: add five "outside the eval set" questions to every weekly
operator check-in. Sample them from real user behaviour if any. Pulling
from `data/answer_cache.json`'s low-tier entries also works.

## If you fix nothing else, fix this

Pick the audience this week. Until the operator names which of "Submitter
study tool / academic researcher tool / agent-tooling reference" this
project actually is, every subsequent decision — from the 3D viz demotion,
to the Khalifa banner content, to the v2 eval rubric weights, to whether
`run_cypher` stays in the agent's toolbox — gets relitigated. The audit
asked for this three weeks ago and was correct then; it is now overdue.
One paragraph, one stakeholder (the operator), thirty minutes of focused
writing. After that paragraph, half the open items in the retrofit plan
will answer themselves.

## Defending the D+ grade

Engineering rigor: B+ (real improvement from C+). Eval rigor: B (real
improvement from C). Content discipline: A− (the doctrinal audit's 94.7%
is a strong result). Audience clarity: F (no pick). Surface area
discipline: D (still four apps, still 20 tools, still two competing
front-page experiences). Reputation risk management: D (Khalifa
disclosure unshipped). The weighted view drops product strategy below
last cycle's C− because the engineering improvements have raised the
*cost* of the strategic ambiguity — a sharp project with no audience is
more wasteful than a sloppy project with no audience. Hence D+.
