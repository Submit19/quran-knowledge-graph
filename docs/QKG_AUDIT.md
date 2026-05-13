# QKG — Consultant Audit (2026-05-13)

Multi-consultant review of the Quran Knowledge Graph at HEAD `2d8de42`. Eight perspectives, no flattery. Companion plan: `docs/QKG_RETROFIT_PLAN.md`.

---

## Summary verdict

| Dimension | Grade | One-line |
|---|---|---|
| Knowledge graph schema | A− | Rich, well-typed; bloated by reasoning-memory |
| Retrieval engineering | B+ | Solid choices (BGE-M3, multilingual reranker); eval claims overreach |
| Agent / tool design | B− | Too many tools, prompted into worst-case paths, classifier-as-prompt |
| Code quality | C+ | Four-apps duplication, 2,500-LOC chat.py, near-zero tests |
| Eval rigor | C | One real number; the rest don't survive scrutiny |
| Theological positioning | D | Major unaddressed risk; controversial translation, zero UX disclosure |
| Product vision | C− | No defined audience; demo-ware UX; backlog ≠ roadmap |
| Ralph loop infrastructure | A as research / C as ROI | Genuinely novel, ships code, growing faster than the product |
| Documentation / memory stack | B+ | Lean, well-cross-referenced; ADR-by-LLM is a category error |

---

## 1 · The Information Retrieval Scientist

- **n=13 is not an evaluation.** `eval_v1.py` is an existence test masquerading as a quality metric. `avg_unique_cites_per_q=43.6` is a count, not correctness.
- **The QRCD result is real but tiny** (n=22 unique questions, no CIs). Comparison to "AraBERT-base fine-tuned 0.36" is apples-to-oranges.
- **"Reranker drops hit@10 50%"** was on the old English-only model; never re-measured on the multilingual `bge-reranker-v2-m3`. The adaptive routing design rests on inference, not measurement.
- **"18,785× speedup"** is cold-call/cache-hit ratio against timer noise. Honest claim: caching provides speedups.
- **Cache "77% strong (≥10 cites)"** confuses output volume with output quality.

**Fix:** ship behaviour-asserted eval with external/blind grading, publish CIs, retire citation-count metric.

## 2 · The Knowledge Graph Architect

- **The schema is impressive** — typed edges, Concept ER, morphology, reasoning-memory subgraph.
- **Vector indexes over-provisioned.** Four indexes; kill the legacy MiniLM one (no callers, measured harmful).
- **Reasoning-memory at risk of becoming the dominant graph** — telemetry shouldn't live in the same store as substrate.
- **The 41-index audit found 4 missing composite/score indexes** — sign of organic growth.
- **HippoRAG negative is well-executed** — credit where due.

## 3 · The Agentic Systems Engineer

- **21 tools, agent uses 4–6 per query** — sprawl. Etymology cluster is 6 overlapping tools.
- **`EXHAUSTIVE SEARCH MANDATE`** in system prompt literally orders three search tools per question; you've prompted the worst-case path into existence.
- **Query Routing Rubric** is a classifier expressed as English with zero introspection. Move to code.
- **System prompt says 15 tools; `chat.py` exposes 21.** Model uses what it sees described.
- **`run_cypher` is a footgun.** Read-only ≠ safe. Confabulated Cypher that returns nothing can silently confirm wrong claims. Log every invocation.

## 4 · The Senior Software Engineer

- **Four near-duplicate apps** (`app.py` 587, `app_full.py` 616, `app_lite.py` 558, `app_free.py` 1148). ~600 lines of copy-paste. **Single biggest tech-debt item.**
- **`chat.py` is 2,497 lines** in one file. Split: `tools/search.py`, `tools/etymology.py`, `tools/code19.py`, `dispatch.py`, `cache.py`.
- **Daemon-thread leak on client disconnect** (`app_free.py:1087`) — burns Ollama/Neo4j cycles after tab close.
- **String concatenation into Cypher** at `chat.py:520` — allowlisted today, foot-gun for next contributor.
- **One real test file** (A/B harness, not unit tests). Every change is live-fire.
- **Frontend `index.html` 1,651 LOC, all inline CSS, marked.parse() per keystroke** — works, near ceiling.
- **38 `data/ralph_*.md` artefacts** the loop never deletes.

## 5 · The Religious Studies Scholar

**The conversation no one in the repo is having.**

- **Rashad Khalifa is non-mainstream** — excommunicated by Sunni and Shia scholarship; "19 miracle" rejected academically. None of this is in the README or UI.
- **ADR-0001 disclaimer is one sentence** — product implication unanalysed. System can only serve Submitters; to others it surfaces heterodox claims as "the Quran says".
- **System prompt positively highlights Khalifa-specific interpretations** alongside citation grounding — built a confidence machine for a contested position.
- **No comparison translation offered.** Sahih International / Pickthall / Abdel Haleem are public-domain, well-respected.
- **No epistemic humility in the UI.** Frame as authoritative without naming the translation choice.

**Fix:** README + UI disclosure; translation toggle (architecture supports it trivially — `Verse.text` is just a property).

## 6 · The Product Strategist

- **"Explorer for everyone" isn't an audience.** Three plausible ones:
  1. Submitters (small but coherent niche).
  2. Academic Quranic studies researchers (would want multi-translation, no theology in prompts, exportable citations).
  3. Agent-tooling developers (would consume as reference architecture for agentic GraphRAG — strongest moat).
- **3D viz is demo-ware and dubious primary UX.** Citation tooltips on chat are the actual value loop.
- **No product roadmap.** `ralph_backlog.yaml` is engineering tasks, not user value.
- **Moat is engineering, not product** — eval infra + Ralph pattern more original than the app.
- **Monetisation invisible.** If "research project," say so and stop building like a product.

## 7 · The Engineering Manager (Ralph loop)

- **The loop demonstrably ships code** — 79 ticks / ~13 days / ~40 code commits / 3 real features merged.
- **62% `DONE_WITH_CONCERNS` is a load-bearing fiction.** The "concerns" are absorbed silently because the human-review step never happens at scale.
- **The loop is rewriting its own scaffolding** — Max 20x, 30-min cadence, end-of-tick prep, Sonnet pre-warming, ADR backfill. *Meta-system gaining mass faster than the product.*
- **LLM-authored ADRs are a category error.** ADRs encode human judgement; Haiku reading commit messages produces confabulations of decisions.
- **Bus factor terrible** — loop keeps ticking out work no one reviews; queues choke within a week.
- **Strip the loop to code/eval/refactor** — not research summarisation, not ADR backfill, not memory hygiene.

## 8 · The First-Principles Skeptic

- **Does this need to be a graph at all?** ~90% of value seems to come from vector search + reranker + LLM. Strip the graph and measure.
- **Does this need to be agentic?** Single hybrid retrieval + single LLM call would handle 80% of queries, faster + cheaper.
- **Does the Ralph loop need to exist for this product?** Pattern-research disguised as feature work.
- **Does the product need to exist?** World has 100 Quran apps. Differentiator (agentic+graph+citation-verified) requires trust — which you've under-invested in (translation, eval) and over-invested in mechanism.

---

## The three things to fix this week

1. **Confront the Khalifa issue** in README and UI. Credibility risk that compounds with every user.
2. **Replace citation-count with real correctness eval** — 50q, blind-graded, published with CIs.
3. **Refactor the four apps into one shared module.** Unblocks every future change.

## The three things to fix this month

4. Consolidate 21 tools to 8–10 (start with etymology cluster).
5. Cap Ralph loop scope to code/eval/refactor; strip research summarisation + ADR backfill.
6. Decide what this is — research artifact, niche app, reference architecture — and let that answer remove half the backlog.

---

## TDD lens (Kent Beck)

Beck's *Test-Driven Development: By Example* reframes the diagnosis:

- **The Ralph loop has no Red.** Red → Green → Refactor; QKG's loop is brief → design doc → commit. No failing test defines done. That's why 62% of ticks are `DONE_WITH_CONCERNS` — no green bar to converge to.
- **Eval set is the Test List, far too thin.** n=13 is a stack of paper without a foot to land on.
- **Loop violates Isolated Test at meta-level.** Ticks inherit full state; not order-independent.
- **Four-apps duplication is the second rule violated** — "eliminate duplication". The duplication isn't a code-quality issue but a missing-abstraction signal.
- **Most ticks are *Obvious Implementation* without *Fake It* or *Triangulate*.** Adaptive routing shipped on a prediction; the eval to triangulate is task #95.
- **`data/ralph_*.md` graveyard is absence of *Do Over*.** Beck: throwing away work is a tool, not a failure.

**The single sentence to put on the wall:** *"TDD is an awareness of the gap between decision and feedback during programming, and control over that gap."* — Beck. QKG's gap is open: decisions ship at tick 73, feedback scheduled for tick ≥95.

---

Full action plan: `docs/QKG_RETROFIT_PLAN.md`.
