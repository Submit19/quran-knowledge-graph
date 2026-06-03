# Composer Rewire — Operator Briefing

_Design-only session, 2026-05-28. Branch `claude/composer-rewire-design-2026-05-28`.
Full design: `01_current_flow`, `02_design_proposal`, `04_implementation_plan` in this folder._

## What the composer does today — and the contamination problem

Every answer the app produces is composed by one function, `shared_agent.agent_stream`,
which all four apps now route through. It hands the model a bag of **verses** retrieved
from Neo4j and asks for a thematic, densely-cited answer. The problem is structural, not a
bug: the verses supply *facts*, but everything *between* the citations — "this teaches…",
"the significance is…", "the Arabic conveys…" — is **interpretation the model generates
from its own training knowledge of Islam.** That knowledge is overwhelmingly
hadith-informed, classical-tafsir-informed, and mainstream-jurisprudence-informed —
precisely the sources the Khalifa-only rule excludes. The Khalifa primary-source corpus
(~527K words) exists but **no tool can retrieve it**, so the model has nowhere else to draw
commentary from. The only guardrail is the system prompt, which is advisory and checks that
*a verse is attached to each claim*, not *where the claim came from*. Worse, every composed
answer is written back to the answer cache ungated, and the cache is re-injected as
"context" into future answers — so contamination compounds across runs.

## The proposed rewire — one paragraph

Turn the agent from *"retrieve facts, interpret from memory"* into *"retrieve facts AND
authorized commentary, compose only from what was retrieved, then audit the output for
provenance."* Four moves: **(1)** add a `search_khalifa_corpus` tool so the model can
retrieve Khalifa's own commentary as a citeable source alongside verses; **(2)** rewrite the
prompt into a context-only contract — "no source chunk, no claim" (the proven Code-19
"no tool call, no count" discipline, generalized to all interpretation); **(3)** add a
runtime **source-audit gate** that decomposes the answer into claims, labels each
*verse-grounded / corpus-grounded / unsupported*, and on any unsupported claim regenerates
once then abstains on the offending spans — and which also enforces the 9:128/9:129
no-surface rule on output; **(4)** gate the cache write behind that audit so the cache can
only ever gain clean entries. Everything lands as default-off config flags on the single
chokepoint, so the rollout is incremental, per-app, and reversible by flipping a flag.

## Phased rollout — when what lands

Five atomic sub-phases (details in `04_implementation_plan`). Suggested order:

- **SP-2 — composition contract** (S, no deps). Prompt rewrite + retry-trigger fix. Land first.
- **Task C — corpus indexing** (separate track). Hard-blocks the corpus tool.
- **SP-1 — corpus tool** (M). Flips the §a test. Needs Task C.
- **SP-3 — source audit** (L, the heavy one). Flips 4 of 5 design tests. Its no-surface +
  verse-only paths can ship *before* Task C in advisory mode.
- **SP-4 — cache gate** (S) → **SP-5 — per-app rollout** (M), advisory→blocking, Anthropic
  apps first, `app_free` (canonical, slower) last.

**First shippable increment without waiting on Task C:** SP-2 + the no-surface scrub and
verse-only audit in *advisory* mode — delivers the runtime 9:128/129 guard plus
contamination telemetry, and de-risks the heavy audit work before the corpus index exists.

## Three risks the operator should know

1. **Over-abstention / blander answers.** A strict "no source, no claim" contract plus
   abstain-on-unsupported will make some answers terser or say "Khalifa's writings don't
   address this." This is the *intended* direction (the binding rule says the rule wins over
   throughput), but it needs tuning so well-covered questions still read richly.
2. **The audit only raises the bar — it doesn't guarantee purity.** Provenance labelling
   leans on NLI/MiniCheck. False-negatives let a leak survive; false-positives over-abstain.
   We must measure precision/recall on a labeled set in advisory mode before trusting the
   blocking gate. Honest framing: this makes contamination *rare and catchable*, not impossible.
3. **Latency and cost.** Claim decomposition + double-NLI + a possible regeneration is the
   heaviest addition, and it lands hardest on the slow local `app_free` path. Bounded to one
   regeneration; mitigated by running the audit only on interpretive query profiles.

## Three open questions the operator must decide before implementation

1. **Enforcement strength at launch** — ship the audit in *advisory* (log-only) mode first
   to gather false-positive data, or go straight to *blocking*? (Recommendation: advisory
   first, at least on `app_free`.)
2. **Legacy-cache fate** — purge-and-rebuild the ~1,607 pre-rule entries under the rewired
   composer, or audit-and-quarantine them in place? Both are out of scope to *execute* here,
   but SP-4's end-state assumes a decision.
3. **Abstention voice** — when neither the Quran nor Khalifa's corpus covers a question,
   what exactly should the app say, and should it offer the verse-only partial or refuse the
   point entirely? This shapes the contract wording in SP-2.

_Verification: `pytest tests/` = 208 passed, 2 skipped (baseline unchanged) + 5 xfailed
(the new design spec). No runtime code was changed this session._
