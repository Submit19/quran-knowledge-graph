# Composer Rewire — Phase 1: Current Composition Flow + Leak Points

_Recon pass. Branch `claude/composer-rewire-design-2026-05-28`, off `origin/main` @ `d650eba`.
Binding scope rule: `memory/feedback_khalifa_only_sources.md` (the "Khalifa-only source rule").
This document is descriptive — it maps what exists today. The proposed fix is Phase 2._

---

## TL;DR

A single function — **`shared_agent.agent_stream`** (file `shared_agent.py`, the
`run(q, stop_event)` worker, lines ~808–1343) — is the composition pipeline for
**all four apps** (`app.py`, `app_lite.py`, `app_full.py` are `backend="anthropic"`;
`app_free.py` is `backend="ollama"`/`openrouter`). Each app is now a thin shim that
builds an `AgentConfig` + `AgentCollaborators` and calls `agent_stream`. **There is one
chokepoint, not four.** The rewire is therefore *feasible without a replatform* — the
"current composer is fundamentally not refactorable → STOP" condition does **not** fire.

The structural failure mode the Khalifa-only rule must block is simple and load-bearing:

> The agent retrieves **facts** (verse text + graph metadata) from Neo4j, but it composes
> **interpretation** (what the verses mean, thematic synthesis, Arabic-root significance,
> theological framing) from its **own training knowledge** — because there is no other
> source of interpretation wired in. The Khalifa primary-source corpus
> (`data/khalifa_corpus/`, ~527K words) **exists but is not retrievable by any tool.**
> Commentary has nowhere to come from except the model's pre-existing knowledge of Islam
> (hadith, classical tafsir, jurisprudence, Submitter-community materials). That is the
> contamination the rule forbids, and today nothing architecturally prevents it.

---

## 1. Source-entry-points

Every place where *material that can end up in a user-facing answer* enters the pipeline.

| # | Entry point | Module / location | What it contributes | In Khalifa-scope? |
|---|---|---|---|---|
| 1 | **Neo4j verse retrieval** (21 tools) | `chat.py::dispatch_tool` → `tool_*` fns; reranked by `retrieval_gate.gate_tool_result` | Quran verse text (Khalifa EN translation + Arabic Hafs), keywords, roots, typed edges, Code-19 arithmetic | ✅ **YES** — this is source (1), the Quran. |
| 2 | **System prompt** | `prompts/system_prompt.txt` (anthropic apps, via `chat.SYSTEM_PROMPT`); `prompts/system_prompt_free.txt` (app_free) | Routing rubric, tool catalogue, citation rules, "honesty" section | Constraint layer (today: weak — see §2). |
| 3 | **Answer cache** | `answer_cache.build_cache_context` → injected into `msgs[0]` system content (`shared_agent.py` ~842–854) | Up to 3 past Q&A pairs (cosine ≥0.6, BGE-reranked), each up to 1500 chars of *prior composed answer* | ⚠️ **CONTAMINATED.** The ~1,607-entry cache was composed pre-rule; "presumed contaminated to varying degrees" per the binding memo. Injected as quasi-authoritative context. |
| 4 | **Reasoning-memory playbook** | `reasoning_memory.find_similar_queries` → injected (`shared_agent.py` ~857–896) | Past *tool sequences* (which tools, which args, summaries) for similar queries | Mostly safe — it injects *tool-call traces*, not prose content. Low contamination risk. |
| 5 | **Model training knowledge** | The LLM itself (Anthropic / Ollama / OpenRouter) | All interpretation, synthesis, Arabic-meaning glosses, theological framing not literally present in retrieved verse text | ❌ **OUT OF SCOPE — and unbounded.** This is the leak. |
| 6 | **Conversation history** | `req.history` → replayed into `msgs` (`shared_agent.py` ~834–838) | Prior turns in the same session (themselves products of #1–#5) | Inherits whatever contamination its own composition introduced. |

**The asymmetry that creates the problem:** entry points 1 and 3–4 supply *retrieved
material*; entry point 5 supplies *everything the model wasn't handed*. Because no tool
retrieves Khalifa's own commentary (corpus is unindexed), the model is *structurally
required* to reach into #5 to answer any "what does this mean / why / how" question.
Source (2) of the rule — Khalifa's primary writings — has **no entry point at all today.**

---

## 2. Composition-constraint gaps

What, if anything, bounds composition today — and where each bound is insufficient.

### 2a. The system prompt is the only constraint, and it is advisory

`system_prompt.txt` lines 80–87 ("CITATION RULES — MANDATORY") and 126–131 ("HONESTY
AND LIMITS") get closest to a source constraint:

- *"EVERY claim … MUST be grounded in specific verses from the graph tools."*
- *"If you cannot find a verse to support a point, do NOT make the point. You are a
  graph-backed research tool, not a general-purpose Islamic scholar."*

**Gaps:**
1. It demands a *verse* citation per claim — it has **no concept of Khalifa-primary
   writing as a citeable source**. So legitimate Khalifa commentary (Appendix N, an SP
   article) cannot be cited even if the model knew it; and conversely, interpretation
   that *should* come from Khalifa is silently sourced from training knowledge as long
   as a *verse* is bolted on next to it.
2. "Grounded in a verse" ≠ "the interpretation came from an authorized source." The
   model can cite `[2:255]` and still attach a classical-tafsir reading of it. The
   citation rule checks *that a verse is attached*, not *where the surrounding claim
   came from*.
3. It is a **soft instruction**, not enforced. Nothing inspects the output to confirm
   compliance. A capable model that ignores or partially follows it produces a
   contaminated answer that ships.
4. It says nothing about hadith, classical tafsir, jurisprudence, or Submitter-community
   materials by name — the exact exclusion list in the binding rule is absent.

### 2b. Citation-density retry increases *volume*, not *purity*

`shared_agent.py` ~1238–1266: if the answer has `< min_citations_for_retry` (5) verse
refs, the loop asks the model to *add more sections with more citations*. This **worsens**
the purity problem on the margin — it pressures the model to manufacture more thematic
prose, which (absent a Khalifa corpus) is filled from training knowledge with a verse
stapled on. It optimizes the wrong metric (citation count = output volume, not provenance).

### 2c. The answer-cache injection explicitly invites fill

`answer_cache.build_cache_context` (answer_cache.py ~228–231) prepends:

> "PREVIOUSLY ANSWERED QUESTIONS (use these to inform your response — you may reuse
> verse citations and analysis from them, but still verify accuracy **and add new
> information if needed**)"

"Add new information if needed" is a direct license to reach into training knowledge.
Combined with a contaminated cache (entry point 3), this is a two-way contamination
channel: dirty cache flows *in* as context, and (see §3) freshly-composed answers flow
*back* into the cache via an ungated `save_answer`.

### 2d. The Code-19 / Arabic-root guards are the *only* hard, non-bypassable constraints

The prompt's strongest real constraints are narrow:
- *"NEVER invent a frequency count from memory … No tool call, no count"* (root counts).
- *"For Code-19 … cite the exact figure get_code19_features returns. NEVER state a count
  from memory."*

These work because the tool returns an immutable integer the model can't plausibly
fabricate convincingly, and the design treats memory-sourced numbers as illegitimate.
**This is the template the rewire should generalize**: "no source chunk, no claim" is
the arithmetic-count discipline applied to *all* interpretation, not just counts.

---

## 3. Where the model-knowledge-fill happens (the structural failure mode)

Step-by-step through `run(q, stop_event)` in `shared_agent.py`, flagging each leak (L):

```
/chat (app*.py)                         → StreamingResponse(_agent_stream(...))
  └─ shim → shared_agent.agent_stream(message, history, config, collaborators, ...)
       ├─ routing: pick backend/model (anthropic | ollama | openrouter)
       └─ run(q, stop_event) [daemon thread via sse_pump.pump_worker_into_sse]:
            1. msgs = [system_prompt] + history + user_message
            2. build_cache_context → inject ≤3 past Q&A         ── L1 (contaminated cache in;
                                                                       "add new info" license)
            3. reasoning_memory playbook → inject tool traces   ── (low risk)
            4. classify_query → profile (gates rerank only)
            5. priming graph update (app_free) → seed verses
            6. LOOP turn=1..max_tool_turns:
                 a. _call_backend → LLM proposes text + tool_calls
                 b. multi-tool discipline nudge (app_free)      ── forces retrieval breadth,
                                                                       NOT source purity
                 c. for each tool_call: dispatch_tool → Neo4j   ── verses/graph ONLY;
                       → gate_tool_result rerank → feed back            no Khalifa corpus tool
                 d. when model emits text with no tool_calls → DONE
            7. full_text = concatenated text blocks            ── L2 ★ THE CORE LEAK:
                                                                       interpretation composed
                                                                       from training knowledge
            8. citation-density retry if < 5 refs              ── L3 (amplifies L2)
            9. _fetch_verses(refs) → tooltip text
           10. save_answer(message, full_text, verses)         ── L4 (ungated write-back to cache)
           11. citation_verifier (env-gated, default OFF)      ── L5 (checks verse↔claim
                                                                       entailment, NOT provenance)
           12. q.put({"t":"done", ...}) → SSE to browser
```

### L2 — the core leak (step 7)

The model is handed: (a) a system prompt asking for thematic synthesis with dense
citations, and (b) a bag of retrieved verses. It is *asked to interpret*. Verses supply
the literal text; **everything between the citations — "this teaches…", "the significance
is…", "scholars understand…", "the Arabic conveys…" — is generated.** With no Khalifa
corpus available, that generated material is drawn from the model's training knowledge of
Islam, which is overwhelmingly hadith-informed, classical-tafsir-informed, and
mainstream-jurisprudence-informed — precisely the excluded sources. The leak is not a bug
in any line of code; it is the *absence* of an authorized interpretation source.

### L1 / L4 — the cache contamination loop (steps 2, 10)

`save_answer` (answer_cache.py ~119–165) writes **every** composed answer to the cache
with no validity/purity gate (the only filters are length ≥50 and a 0.98 dedupe). The
next similar question reads it back via `build_cache_context`. So an L2-contaminated
answer becomes injected "context" for future answers — contamination compounds and is
self-reinforcing across runs. The existing `scripts/check_no_surface_rule.py` (on
`origin/claude/composer-rule-enforcement-2026-05-27`) scans *files* offline; **it is not
wired into `save_answer` or any runtime path**, and it only checks 9:128/9:129, not
general source contamination.

### L5 — the verifier checks the wrong thing (step 11)

`citation_verifier.verify_response` (NLI / MiniCheck) asks "does cited verse V entail the
claim near it?" It is (i) **off by default** (`ENABLE_CITATION_VERIFY=1` required), (ii)
**post-hoc and advisory** — it emits a `verification` SSE event but never regenerates or
blocks, and (iii) **provenance-blind** — a claim sourced from hadith that happens to be
*consistent* with an adjacent verse passes NLI cleanly. It cannot detect "this is true
and verse-consistent but came from an unauthorized source."

---

## 4. Existing constraints inventory (what we can build on)

| Asset | Where | Reusable as |
|---|---|---|
| `retrieval_gate` reranker (BGE-reranker-v2-m3, lazy singleton, env-gated, profile-routed) | `retrieval_gate.py` | **Template + shared model** for a new Khalifa-corpus reranker. `answer_cache._get_reranker` already borrows it — same pattern works for corpus retrieval. |
| `check_no_surface_rule.py` (bracket + prose 9:128/129 scan of `answer` field) | `scripts/` (unmerged branch) | The **output-validation seed** — extend to a runtime scrub + broaden to contamination patterns. |
| `COMPOSER_CONSTRAINTS.md` (corpus-vs-output table, scrub regex `9\s*[:.]\s*12[89]`, SP byline caveat) | `data/khalifa_corpus/` (corpus branch) | The **operative spec** for the no-surface layer; the corpus authors already wrote the contract. |
| Code-19 / root "no tool call, no count" discipline | `system_prompt*.txt` | The **proven pattern** to generalize: "no source chunk, no claim." |
| `AgentConfig` feature-flag pattern (frozen dataclass, per-app axes) | `shared_agent.py` | New constraints land as **new flags** (e.g. `enable_corpus_retrieval`, `enable_source_audit`), default-off, so the rewire is incremental and reversible per-app. |
| `classify_query` profiles | `chat.py` | Routing hook — can gate *when* corpus retrieval / audit runs. |
| Corpus frontmatter (`flagged_9_128_129`, `byline_note`, provenance, sha256) | `data/khalifa_corpus/**` | Per-chunk routing signals for the retrieval + scrub layers. |

---

## 5. Corpus availability (the second source, ready but unwired)

Per the corpus + sermon branches (manifests read this session):

- **Text corpus** (`origin/claude/khalifa-corpus-scrape-2026-05-27`): 183 files /
  **197,716 words** — Introduction, 38 Appendices, *Quran, Hadith and Islam*, 64
  Khalifa-era *Submitters Perspective* issues. 18 files carry `flagged_9_128_129: true`.
- **Sermon corpus** (`origin/claude/sermon-pipeline-2026-05-28`): 47 transcripts /
  **329,959 Rashad-segmented words** under `data/khalifa_corpus/sermons/`.
- **Total ≈ 527K words.** Both branches are **unmerged**; neither is indexed into Neo4j
  or any vector store; **no tool reads them.** Indexing is explicitly *Task C, a separate
  session* — this design must therefore treat corpus retrieval as a **dependency**, not a
  thing it builds.

---

## 6. Stop-condition check

- ❌ **Not-refactorable → STOP**: does **not** fire. One chokepoint (`agent_stream`),
  clean feature-flag seam (`AgentConfig`), reranker pattern already proven for a second
  retrieval source (`answer_cache._get_reranker`). The architecture *supports* the rewire.
- The design (Phase 2) must respect one hard dependency: **the Khalifa corpus is not yet
  indexed** (Task C). The composition-constraint and output-validation layers can be
  designed and partially built independent of indexing; the *retrieval* layer is gated on it.

---

## 7. Open questions surfaced by recon (carried into Phase 2 / briefing)

1. **Abstention vs. degraded answer** when the corpus lacks coverage for a question —
   does the app say "Khalifa's writings don't address this" or answer verse-only?
2. **Legacy cache fate** — purge-and-rebuild under the rewired composer, or
   audit-and-quarantine the 1,607 existing entries? (Cache work is out of scope to *do*,
   but the design must state the intended end-state.)
3. **Enforcement strength** — soft (prompt + advisory audit) vs hard (audit gate that
   blocks/regenerates/abstains). The four apps differ in latency budget; a hard gate on
   the Anthropic apps is cheaper than on the local app_free path.
