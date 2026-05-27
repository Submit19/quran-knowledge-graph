# Expert 2 — Software Architect

*Quran Knowledge Graph board critique, 2026-05-27. Builds on the architecture
audit on `claude/architecture-audit-2026-05-22` (synthesis at
[refactor_priorities_2026-05-22.md](../../../data/research/architecture_audit/refactor_priorities_2026-05-22.md), 4 prior passes).
Reference baseline: [docs/QKG_AUDIT.md](../../../docs/QKG_AUDIT.md) §4
(Senior Software Engineer, C+).*

## Who I am, and what I'm evaluating from

I've designed and led the rewrites of three large Python codebases (10k+ LOC
each — a data-pipeline platform, a search backend, an ML-serving runtime).
I have a hard preference for *changeable* code over *clever* code: if a new
contributor cannot trace one user-facing request to one file within fifteen
minutes, the architecture is failing its primary job. My evaluation here
is on top of the sibling architecture audit (which I have read in full); I
am the second opinion on whether its prescriptions are the right ones and
whether they capture the load-bearing problems.

## TL;DR grade: **B−**

The original audit gave code quality a C+. Phase 3a (4 apps → `shared_agent.py`
+ thin wrappers) and Phase 3b (four real regression-test-first bug fixes:
SSE worker leak, tool-cache TTL race, typed-edge Cypher concat, whitespace
normalisation) are textbook execution. The biggest tech-debt item from the
original audit is *resolved well*. Test count went from "near zero" to 209.
But chat.py is still 2,650 LOC, ~44 files still hand-roll Neo4j driver
init, three citation regexes still drift, and the next round of consolidation
work has not started. The B− reflects substantial real progress that is
now plateauing — the easy wins were taken, the hard refactors are queued
behind decisions the architecture audit cannot make alone.

## Findings

### F1 — chat.py is still the single largest cognitive liability. **SERIOUS.**

[chat.py](../../../chat.py) is 2,650 LOC at HEAD. The audit's prescription
(split into `tools/search.py`, `tools/etymology.py`, `tools/code19.py`,
`dispatch.py`, `tools/schema.py`) is the right shape. The architecture
audit's item 29 names this and rates effort L (full day). The 20-tool
TOOLS schema list alone is `chat.py:1777-2358` — that is 580 lines of
JSON-shaped Python in one of the most-read files of the project. The
`dispatch_tool` switch at `chat.py:2469-2540` is a 20-arm if/elif chain
that violates Beck's "eliminate duplication" in spirit even though each
arm is independently small.

The reason the split has not happened is not that it is hard; it is that
the operator does not want to risk a trajectory regression mid-refactor.
Solution: capture a trajectory baseline (a single fixed-seed run of the
v2 eval) before the split, run it after the split, require the trajectory
to match byte-for-byte on tool sequence. Phase 3a did exactly this for
the FastAPI extraction (`scripts/capture_baseline_trajectory.py` per
`d34909f` ancestry) — proven pattern, ready to repeat.

Action: a focused day. Split chat.py per the audit's prescription;
trajectory baseline before/after; commit per tool family.

### F2 — Neo4j driver boilerplate ×44 files is the single largest "we need a package" signal. **SERIOUS.**

Forty-four files. Each one has its own 4-variable env block plus its own
`GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))` call.
Each one re-implements the same connectivity check. The architecture
audit's item 8 (HIGH, M effort, −400 LOC) names this. A `quran_kg/neo4j.py`
helper with `get_driver()` and `session(db=...)` collapses the lot.

Architecturally, this is the moment the project should commit to actually
becoming a package (`quran_kg/` directory, `pyproject.toml` package
metadata). Today the repo is a *script-orchestra* — every `.py` is a
top-level executable, and the only thing that has the shape of a library
is `eval/v2/`. The 44-file driver boilerplate is the load-bearing
evidence that the script-orchestra has outgrown itself.

Action: create `quran_kg/` package today. First inhabitant: `neo4j.py`
with `get_driver` + `session`. Mechanical sweep replaces 44 files. Net
−400 LOC. Open to whether the package should also house `env.py` (audit
item 5) and `ref_resolver.py` (audit items 6 + 9). My recommendation is
yes — those three plus `model_registry.py` form a coherent infrastructure
core.

### F3 — Three competing citation regexes mean two of them are wrong. **SERIOUS.**

The architecture audit's duplication pass found three implementations:

| Site | Pattern | Semantics |
|---|---|---|
| `evaluate.py:38` | `\[(\d+:\d+)\]` | bracketed only |
| `autoresearch_local.py:73` | `\[(\d+:\d+)\]` | bracketed only |
| `shared_agent.py:203` | `(\d+:\d+)` | unbracketed — picks up arbitrary "X:Y" |
| `eval_qrcd.py:88` | separate function | bracketed |
| `ref_resolver.py` (the real one) | 8 regexes covering bracketed + named-surah + Arabic + ranges | Sefaria-grade |

`shared_agent`'s unbracketed regex *will* match the citation-density retry's
own text saying "verse 2:255" without brackets, count it as a citation,
and skip the retry. That is the kind of silent semantic disagreement that
makes a system mysteriously stop reliably retrying. Whether it is
currently firing is an empirical question I would want answered in a
session.

Action: replace all three with `ref_resolver.resolve_refs(text)`. One
half-hour commit. Add a regression test that asserts the four sites agree
on a shared fixture corpus of mixed citation forms.

### F4 — ~7,950 LOC of addressable dead/parked code is half the audit pass-1 finding. **MODERATE.**

The architecture audit pass 1 catalogued:

- 6 unambiguously dead modules: `graph_qa.py`, `explore.py`, `ui.py`,
  `consolidate_traces.py`, `run_tests_filtered.py`, `evaluate.py` —
  ~1,862 LOC.
- 3 "older infra" autoresearch modules: ~1,623 LOC.
- 6 Ralph-loop modules + 7 tick scripts: ~3,140 LOC parked behind Phase
  5 decision.
- 2 one-shot migrations: ~280 LOC.
- 4 superseded QRCD harnesses: ~1,100 LOC.

Each of these has a different decision shape:
- The 6 unambiguously dead modules are operator-confirm-and-delete. No
  reason to hold them.
- The 1,623 LOC of Optuna autoresearch needs an explicit operator call:
  is hyperparameter sweep coming back, or are we eval/v2-only now? The
  ARCHITECTURE.md still markets it; the retrofit plan implicitly retires
  it.
- The 3,140 LOC of Ralph scaffolding is hostage to Phase 5. Until Phase
  5 lands (or is decided against), no one can clean this up because the
  ralph_loop.py is the heaviest single file in the project (951 LOC) and
  no one knows yet how much of it survives the trim.

Action: schedule three separate decision sessions. Session A: delete the
6 dead modules (15 min). Session B: operator decision on autoresearch
fate (30 min). Session C: Phase 5 design pick OR formal abandonment (1
hour, blocking everything Ralph-adjacent).

### F5 — Test coverage is uneven; the most-load-bearing modules are at 0%. **SERIOUS.**

Per the architecture audit's testing-gaps pass:

- 209 tests, 20% direct-test coverage by function count.
- 4 critical modules at 0% direct coverage:
  - `retrieval_gate.py` (213 LOC, the cross-encoder + lost-in-middle
    reorder + gate_tool_result). This is the only thing standing between
    the agent and a bad rank order.
  - `citation_verifier.py` (317 LOC, NLI + MiniCheck + FActScore). Env-
    gated, so the prod path may bypass it — but when enabled it is the
    hallucination check.
  - `reasoning_memory.py` (452 LOC, writes the Query/Trace/ToolCall
    subgraph; reads it back via `recall_similar_query`). 9.3K verses of
    inputs/outputs flow through this.
  - `ref_resolver.py` (459 LOC, pure regex, the single highest-test-
    value-per-hour target).

The architecture audit's items 12, 13, 20-24 cover this. The right
sequencing is item 12 (`ref_resolver`, pure regex, 2h) → item 13
(`retrieval_gate`, injectable model, 2h) → item 20
(`answer_cache.save_answer`) → 21 (`citation_verifier`, needs NLI
fakes) → 22 (FastAPI handlers via TestClient) → 23 (`reasoning_memory`,
needs testcontainers).

The right framing: every time the cache content shifts (which it does
on every advisor session), `ref_resolver` and `retrieval_gate` are the
two modules whose silent breakage would not surface in pytest. Cover
them this week.

Action: book half a day. Two PRs, items 12 and 13 of the architecture
audit. Net +230 LOC of tests against 672 LOC of zero-coverage critical
path.

### F6 — The system prompt says "15 tools" but the agent has 20. **SERIOUS (subtle, runtime impact).**

[prompts/system_prompt.txt:23](../../../prompts/system_prompt.txt) says
*"You have 15 tools to explore the graph"*. [chat.py:1777-2358](../../../chat.py)
registers 20. The model uses what it is *told* about, not what is
registered. This means `recall_similar_query`, `run_cypher`,
`hybrid_search`, `concept_search`, `get_code19_features` — five of the
most recent tools — are described to the model only by their `description`
fields in the JSON-schema, with no system-prompt narrative.

This is the architecture audit's item 1 (HIGH severity, XS effort). Two
fixes: (a) one-line edit "15 → 20" + add the five missing tool blurbs
in the system prompt body; (b) generate the count + bulleted list at
server startup from `chat.TOOLS`. (b) is correct; (a) is acceptable as a
holdover.

The semantic version of this finding is also true and worse: the
EXHAUSTIVE SEARCH MANDATE at [prompts/system_prompt.txt:44-50](../../../prompts/system_prompt.txt)
still tells the model to call `search_keyword` AND `semantic_search` AND
`traverse_topic` for every topical question. The audit's agentic-systems-
engineer finding 2 from 2026-05-13 called this "you've prompted the
worst-case path into existence." Three weeks on, unchanged. With a 30s
tool-cache the cost is bounded; the latency cost is not.

Action: today, ship (a) for the count. Within a week, ship (b) and also
re-evaluate the EXHAUSTIVE SEARCH MANDATE against the v2 eval — does
removing it move the citation_accuracy dimension by more than its
confidence interval? If not, drop it.

### F7 — Phase 3a refactor finished the loop but not the FastAPI surface. **MODERATE.**

Phase 3a moved the agent loop body into `shared_agent.py`. The four apps
now share that loop. But each app still has its own:

- `_load_env()` helper (5 verbatim copies — audit item 5)
- Neo4j driver init (4 of the 44 files)
- `FastAPI()` instance
- `/`, `/stats`, `/cache-stats`, `/verses`, `/chat`, `/model-info` route
  registrations (~90-180 LOC per app file)

Phase 3a unified the *behaviour*; it did not unify the *surface*. The
architecture audit's item 28 (HIGH, L effort, −400-500 LOC) prescribes a
`shared_app.build_app(config)` factory that returns a configured FastAPI
app. Each `app_*.py` becomes a 10-line config + `app = build_app(cfg)` +
`uvicorn.run(...)`.

This finishes the Phase 3a job. The 387 LOC across the four wrappers
collapses to ~50.

Action: schedule as a follow-up to Phase 3a. Apply the same trajectory-
baseline discipline that Phase 3a used. Estimated half a day per app.

### F8 — `run_cypher` is still exposed to the agent. **SERIOUS.**

`tool_run_cypher` at [chat.py:1587](../../../chat.py) is still in the
tool list at [chat.py:2273](../../../chat.py). The original audit (§3,
agentic-systems-engineer finding 5) called this "a footgun. Read-only ≠
safe. Confabulated Cypher that returns nothing can silently confirm wrong
claims. Log every invocation." The retrofit plan's Phase 7 item 30
("Audit + log every `run_cypher` invocation. Regression-test the
denylist.") is the right shape. There IS now a regression test
(`b1bb8cf test: regression-guard tool_run_cypher denylist (Phase 7 item
30)`) so the denylist itself is tested. The *audit* part (write to a
log file on every invocation, surface in `/cache-stats`-like endpoint)
is not yet shipped.

Importantly, the *capable-model baseline* relied on `run_cypher` for
most of its 62 answers (you can see this in the `tools_used` arrays of
[data/eval/v2/baseline_capable_model.jsonl](../../../data/eval/v2/baseline_capable_model.jsonl)
— almost every entry shows `["run_cypher"]`). The capable model bypassed
the curated tools. That is honest signal — but it also means `run_cypher`
is now the load-bearing tool for cache content. Removing it would force
a rebuild of the cache pipeline. Keep, but audit-log.

Action: add invocation logging (one-line append to `data/run_cypher.log`
with timestamp + caller + query hash + result-rows-count). Surface count
in `/cache-stats`. Six-line change.

### F9 — Documentation drift between README, CLAUDE.md, ARCHITECTURE.md, and runtime. **MODERATE.**

This is the architecture audit's pass 4 (documentation drift) result,
which my read agrees with. Headline drifts:

- README's "Hallucination Reduction Pipeline" table at line 155 references
  `ms-marco-MiniLM-L-6-v2` as the reranker. CLAUDE.md says the default is
  now `BAAI/bge-reranker-v2-m3` (with the legacy explicitly tagged
  "HARMFUL on Arabic"). The README claim is technically correct only for
  `app_full.py` if no env var override is set — and the operator's launch
  command exports `RERANKER_MODEL=BAAI/bge-reranker-v2-m3`.
- README's "Claude's 15 Tools" section is the same 15-tool mistake the
  system prompt has.
- README cites a 500-entry cache cap. CLAUDE.md says 5,000. Cache file
  is 1,607.
- ARCHITECTURE.md Mermaid diagrams cite "92K nodes / 403K edges / 500
  entries / 15 tools" — all stale.
- README's build-pipeline ordering is missing the 9 recent build scripts
  (`build_code19_features.py`, `build_revelation_metadata.py`,
  `build_fulltext_index.py`, `build_concepts.py`, `import_mutashabihat.py`,
  `backfill_*` — that's the architecture audit's item 9 finding).

A new contributor following today's README ends up with: legacy MiniLM
only, no Concept layer, no Code-19 features, no mutashabihat, no BM25
fulltext index. Four-plus chat tools fail silently because their
dependencies don't exist.

Action: README onboarding rewrite is ~3 hours and unblocks every future
collaborator. Architecture-audit item 9 covers it. Pair with item 10
(ARCHITECTURE.md) in the same sweep.

### F10 — Frontend index.html is 1,651 LOC of inline CSS + JS in a single file. **MODERATE, deferred.**

Per the original audit (§4, finding 6). The retrofit plan's Phase 10
items 38-39 split the file. I would not touch this until F1-F9 are
shipped — the frontend is currently *working* and the split has
non-trivial risk of breaking the 3D viz / chat interleave. The right
sequence: ship the Khalifa banner inline (1 div), the citation tooltip
fix (1 function), the marked.parse() O(n²) fix (1 function). Then split
when the file's size + the operator's appetite for frontend work both
say go.

## If you fix nothing else, fix this

Create the `quran_kg/` package. First three inhabitants: `neo4j.py`
(driver factory), `env.py` (the `_load_env` helper), `refs.py` (re-
export from `ref_resolver`). Then sweep the 44 files for driver init,
the 5 files for `_load_env`, and the 3 files for citation regex. Net
−500 LOC of boilerplate plus the long-term win of having a *package* to
add code to instead of a script-orchestra. Every subsequent refactor —
chat.py split, FastAPI factory, citation-regex consolidation — gets
easier once the package exists. The architecture audit's items 5, 6, 7,
8 are all instances of this same finding.

## Defending the B− grade

Phase 3a + 3b are textbook execution. Eval v2 is shipped. Tests at 209
from "near-zero." Cache discipline. Two parallel audit branches that
catalogue the remaining debt rigorously. *Everything the audit prescribed
that the operator can do solo has been done.* The remaining items — chat.py
split, package extraction, dead-code deletion, README rewrite — are each
one focused session and none are blocked by architecture; they are blocked
by *prioritisation*. That is why the grade is B−, not C+ (audit baseline)
and not B+ (which I would give if the package extraction were also
shipped). The grade can move to B+ within three operator-sessions; it
will not move past A− without a real second human contributor (see
Expert 6).
