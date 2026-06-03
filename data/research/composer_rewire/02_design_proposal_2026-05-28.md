# Composer Rewire — Phase 2: Khalifa-Strict Architecture Proposal

_Builds on `01_current_flow_2026-05-28.md`. Branch `claude/composer-rewire-design-2026-05-28`._
_Binding scope rule: `memory/feedback_khalifa_only_sources.md`. Operative output contract:_
_`data/khalifa_corpus/COMPOSER_CONSTRAINTS.md` (corpus-vs-output table)._

**This is design only. No runtime code changes in this session.** Each section follows the
operator's required structure: **Problem → Proposed solution → Alternatives considered &
rejected → Risks → Concrete test scenario.** The five sections map to the operator's
dimensions a–e.

---

## Design thesis (one paragraph)

Turn the agent from *"retrieve facts, interpret from memory"* into *"retrieve facts AND
authorized commentary, compose only from what was retrieved, then audit the output for
provenance."* Concretely: **(1)** add a third retrieval path — a Khalifa-corpus tool
alongside the existing Neo4j verse tools; **(2)** replace the advisory citation prompt
with a **context-only composition contract** ("every assertable claim traces to a retrieved
verse OR a retrieved Khalifa-corpus chunk; otherwise abstain on that point"); **(3)** add a
**source-audit gate** at the output boundary that classifies each claim's provenance and
blocks/regenerates/abstains on failure; **(4)** gate `save_answer` behind that audit so the
cache can only ever gain clean entries. Everything lands as default-off `AgentConfig` flags
on the single chokepoint `shared_agent.agent_stream`, so the rewire is incremental,
per-app, and reversible.

---

## §a · Source retrieval layer

### Problem

Today the composer can retrieve only Quran verses (Neo4j). Khalifa's own commentary — the
*second* authorized source — has no entry point (Phase 1 §1, §5). So all interpretation is
forced to come from training knowledge (leak L2). The Khalifa-only rule requires **three**
coexisting source paths; only one exists.

### Proposed solution

Three retrieval paths, all feeding the same `msgs` context the model composes from:

1. **Quran verse retrieval — keep as-is.** The 21 Neo4j tools + `retrieval_gate` reranker
   stay. This is source (1).

2. **Khalifa-corpus retrieval — NEW tool `search_khalifa_corpus`.** A new tool function in
   `chat.py` (registered in `TOOLS` + dispatched in `dispatch_tool`) that does dense +
   lexical retrieval over the indexed corpus (Task C builds the index) and returns chunks
   with **citable provenance** — `{title, bucket, source_url, chunk_id, text, flagged_9_128_129}`.
   It reuses the `retrieval_gate._get_reranker` singleton (BGE-reranker-v2-m3, already
   multilingual, already the pattern `answer_cache` borrows). The model cites corpus chunks
   as `(Khalifa, The Final Testament, Appendix 24)` exactly as it cites `[9:40]`
   (COMPOSER_CONSTRAINTS.md, "The two-source rule").
   - **Index location decision: a parallel vector store, not Neo4j nodes.** Rationale in
     Alternatives. Chunks carry the frontmatter provenance fields so the audit + scrub
     layers can route flagged chunks (§c).
   - **Retrieval invocation: mandated by prompt + discipline class.** The corpus tool joins
     the `required_tool_classes` map (a new class `"khalifa commentary"`) so the
     multi-tool-discipline nudge forces at least one corpus call on any interpretive
     question — the same mechanism that today forces `semantic_search`.

3. **System constraints — promoted to a first-class layer.** The rule itself, the
   composition contract, and the scrub patterns are not "just the prompt" anymore; they are
   versioned constraint artifacts (the prompt text + `COMPOSER_CONSTRAINTS.md` + the audit
   ruleset) that the design treats as a maintained interface.

### Alternatives considered & rejected

- **Index corpus as Neo4j nodes (`:KhalifaChunk`) with edges to verses.** Rejected for
  *this* layer: it couples corpus retrieval to graph availability, bloats the graph, and
  the corpus↔verse linking is a richer follow-on project (Task C may still choose to add
  `:DISCUSSES` edges later). A standalone vector store (FAISS/sqlite-vec/Chroma, Task C's
  call) is the minimum that unblocks composition. *Not mutually exclusive — graph edges can
  be added later without changing the composer contract.*
- **Stuff the whole corpus into the system prompt.** Rejected: 527K words ≫ context window;
  defeats the point of retrieval; ruinous token cost per request.
- **Have the model retrieve corpus via `run_cypher` once it's in the graph.** Rejected:
  `run_cypher` is an escape hatch with a denylist; corpus retrieval needs semantic ranking,
  not raw Cypher, and must be a first-class, prompt-mandated tool.

### Risks

- **Coverage gaps.** 527K words is large but finite; many questions will have thin or no
  corpus coverage. Mitigated by the abstention policy (§c/§d) — *not* by letting the model
  backfill from memory.
- **Index staleness / dependency.** This layer is hard-blocked on Task C. If Task C slips,
  the composition-contract and audit layers can still ship (degrading gracefully to
  verse-only + abstain-on-interpretation), but the *value* of the rewire is muted.
- **Chunking artifacts.** Bad chunk boundaries can sever a Khalifa argument mid-sentence,
  producing mis-citable fragments. Task C owns chunk quality; the design asks for
  paragraph-coherent chunks with title/appendix provenance retained.

### Concrete test scenario

> Q: *"What is the significance of the number 19 in the Quran?"*
> The agent calls `get_code19_features` (arithmetic) **and** `search_khalifa_corpus("code 19
> miracle")` → retrieves Appendix 1 chunks. The answer's interpretive claims ("Khalifa
> identified the count of … as evidence of divine authorship") cite `(Khalifa, TFT, Appendix
> 1)`; the numeric claims cite the tool figure; the verse claims cite `[74:30]`. **Zero**
> sentences are sourced from generic Islamic numerology in training knowledge.

---

## §b · Composition-constraint layer

### Problem

The model fills interpretation from training knowledge (L2), and the only guardrail is an
advisory verse-citation rule that checks *attachment*, not *provenance* (Phase 1 §2a). We
need the composer to be **architecturally unable** (or at least strongly disincentivized
and then *caught*) to assert anything not traceable to a retrieved verse or corpus chunk.

### Proposed solution — **two-stage compose → audit → revise, with a context-only contract**

**RECOMMENDED.** Combine a hard *prompt contract* with a *programmatic audit gate*
(the audit itself is §c). Two layers because neither alone suffices: the prompt shapes
behavior cheaply but can't be trusted; the gate enforces but is expensive and needs the
prompt to keep regenerations rare.

1. **Context-only composition contract (rewrite of the system prompt's source section):**
   - "You may assert only what is supported by (a) the text of a verse returned by a tool
     this turn, or (b) a Khalifa-corpus chunk returned by `search_khalifa_corpus` this turn.
     You have **no other sources**. Your training knowledge of Islam — hadith, classical
     tafsir (Ibn Kathir, Tabari, Qurtubi…), the four madhabs, later Submitter teachers — is
     **not a source** and must not inform any claim."
   - "Every interpretive sentence carries a citation: `[s:v]` for verse-grounded, or
     `(Khalifa, <work>, <locator>)` for commentary-grounded. A sentence with neither is a
     violation — delete it or replace it with a corpus-grounded version."
   - "If neither source supports a point the user asked about, say so explicitly
     ('Khalifa's available writings do not address …') rather than supplying it from
     general knowledge."
   - Generalizes the proven Code-19 discipline ("no tool call, no count") to all claims:
     **no source chunk, no claim** (Phase 1 §2d).
   - Replaces the harmful citation-*density* retry (Phase 1 §2b): the retry trigger becomes
     **provenance coverage**, not citation *count* (regenerate if uncited claims exist,
     not if there are "too few" citations).

2. **Audit-and-revise loop (draft → audit → revise → re-audit):** after the model produces
   `full_text`, a programmatic **source-audit** (§c) decomposes it into claims and labels
   each `verse-grounded | corpus-grounded | unsupported`. If any `unsupported` claims exist,
   feed them back ("These sentences have no retrieved source: … Either ground each in a
   retrieved verse/corpus chunk or remove it.") and regenerate **once**. Re-audit. On a
   second failure, **abstain on the unsupported spans** (drop them) rather than ship them.

### Alternatives considered & rejected

- **Strict context-only prompting alone (no gate).** Rejected as *insufficient*: it's L2's
  current half-measure dressed up. A capable model still leaks; an honest design must
  *catch* leaks, not just request their absence. (Kept as the cheap first layer, not the
  whole answer.)
- **Citation-required-per-claim enforced purely at compose time (constrained decoding /
  forced tool-cite tokens).** Rejected: brittle across three backends (Anthropic / Ollama /
  OpenRouter), no portable mechanism, and it can't tell a *real* grounding from a
  plausible-looking one. The post-hoc audit is backend-agnostic.
- **Single-pass scanner that only flags, never revises (the current verifier shape).**
  Rejected as the *primary* mechanism: flagging without regeneration ships the contaminated
  answer with a warning the user never sees (L5). Acceptable only as telemetry, not control.
- **N-pass debate / multiple composers voting.** Rejected for v1: heavy latency/token cost
  on the local app_free path; the draft→audit→revise→abstain loop captures most of the
  benefit at one regeneration. Revisit only if audit shows the single revision is
  insufficient.

### Risks

- **Over-abstention / blandness.** A strict contract + abstain-on-unsupported can make
  answers terse or repeatedly say "Khalifa doesn't address this." This is the *intended*
  failure direction (rule wins over throughput per the binding memo) but must be tuned so
  well-covered questions still produce rich answers.
- **Latency / cost of the revise loop.** One extra LLM round-trip per contaminated answer.
  Bounded to a single regeneration; the prompt contract aims to make most first drafts pass.
- **Audit false-negatives** (a contaminated claim labeled grounded) — covered in §c risks.
- **Self-citation laundering.** The model could cite a *corpus chunk that doesn't actually
  support the claim* to satisfy the gate. The audit must verify *support* (entailment),
  not mere *presence* of a citation — reuse the NLI/MiniCheck machinery against corpus
  chunks, not just verses.

### Concrete test scenario

> Draft contains: *"The Prophet said in a hadith that intentions determine deeds, which
> aligns with [2:225]."* Audit labels the clause "The Prophet said in a hadith…"
> `unsupported` (no retrieved hadith source — and there can be none). Revise prompt returns
> it. Re-audit: the sentence is either re-grounded as *"[2:225] teaches that God judges by
> what hearts have earned"* (verse-grounded) or dropped. Shipped answer contains no hadith
> reference.

---

## §c · Output-validation layer (the source audit)

### Problem

There is no runtime check that an answer is Khalifa-clean. The no-surface scanner is
offline + 9:128/129-only; the citation verifier is off-by-default, advisory, and
provenance-blind (Phase 1 §2c, L4, L5). We need a runtime gate that (i) verifies every
claim is source-traceable, (ii) enforces the 9:128/129 no-surface rule on *output*, and
(iii) has a defined failure behavior.

### Proposed solution — **a three-check `source_audit` gate, run before `done` and before `save_answer`**

1. **Source-attribution check (the new core).** Decompose `full_text` into atomic claims
   (reuse `citation_verifier`'s FActScore-style decomposer — already in the codebase,
   `CITATION_DECOMPOSE=atomic`). For each claim, classify provenance:
   - `verse-grounded` — entailed by a verse retrieved this turn (NLI/MiniCheck, existing).
   - `corpus-grounded` — entailed by a Khalifa-corpus chunk retrieved this turn (same NLI
     machinery, new evidence set).
   - `unsupported` — neither. **This is the contamination signal.**
   The gate's verdict is the count of `unsupported` claims and the specific spans.

2. **Citation-validity check (existing, kept).** Cited `[s:v]` refs must resolve to real
   verses (catches the "impossible verseId" cache-rot class, e.g. `[110:9]`); corpus
   citations must resolve to a real chunk id.

3. **No-surface check (promote `check_no_surface_rule.py` to runtime).** Run the existing
   bracket + prose scan (regex at least as broad as `9\s*[:.]\s*12[89]`, plus prose forms
   like "verse 128 of sura 9" per COMPOSER_CONSTRAINTS.md) on the **output** text. Route
   `flagged_9_128_129` corpus chunks through this scrub specifically. A hit is a **HARD
   FAIL** (the corpus may contain these refs; the output may not).

**Failure behavior (the operator's explicit sub-question):**

| Failure | Action |
|---|---|
| `unsupported` claims present, attempt 1 | **Regenerate once** with the offending spans listed (§b loop). |
| `unsupported` claims present, attempt 2 | **Abstain on the spans** — drop them; ship the grounded remainder. If that guts the answer, ship an explicit "Khalifa's writings + the Quran don't cover this" abstention. |
| Invalid citation | Strip the invalid ref; if it was load-bearing, treat the claim as `unsupported`. |
| 9:128/129 surface | **HARD FAIL → scrub the span and re-audit.** Never ship; never cache. |
| Audit itself errors | Fail **closed** for cache (do not `save_answer`); fail **open** for display only if `source_audit` is in advisory mode (see staged rollout, Phase 4). |

`save_answer` is gated: **only audit-passing answers are cached** (closes L4 — the cache
can only gain clean entries). This is the single highest-leverage change for stopping
contamination compounding.

### Alternatives considered & rejected

- **Regex/keyword contamination blacklist** ("Bukhari", "Ibn Kathir", "the Prophet said").
  Rejected as the *primary* check: trivially evaded by paraphrase, and it flags legitimate
  mentions (e.g. a corpus chunk where Khalifa himself names a hadith collection to reject
  it). Useful only as a cheap *pre-filter* feeding the real entailment audit.
- **Verse-entailment only (current verifier).** Rejected: provenance-blind (L5). A
  hadith-sourced claim consistent with a verse passes. The new `corpus-grounded` vs
  `unsupported` distinction is the whole point.
- **Ship-with-warning (advisory only).** Rejected as end-state: the user never sees the
  warning; contamination ships. Allowed only as a *staged-rollout* intermediate (Phase 4
  shadow mode) to measure false-positive rates before turning the gate to blocking.

### Risks

- **Decomposition + double-NLI cost** (verse evidence set + corpus evidence set per claim)
  is the heaviest part of the design. Mitigate: run only on interpretive profiles
  (`classify_query`), batch claims, cache audit verdicts keyed on answer hash.
- **NLI false-positives → over-abstention; false-negatives → leaks survive.** The audit is
  only as good as the NLI model. The honest framing: this *raises the bar*, it doesn't
  guarantee purity. Measure precision/recall on a labeled set before trusting it (Phase 4).
- **The audit can't see *un-cited training-knowledge that happens to match a retrieved
  verse*.** If the model paraphrases a tafsir reading that a retrieved verse weakly entails,
  it's labeled `verse-grounded`. This is an accepted residual risk; the contract + corpus
  availability reduce its frequency but don't eliminate it.

### Concrete test scenario

> A composed answer contains 9 claims. Audit: 7 `verse-grounded`, 1 `corpus-grounded`
> (cites Appendix 9), 1 `unsupported` ("most scholars hold that…"). Gate regenerates with
> the 1 span flagged; revised answer re-grounds it as corpus-grounded or drops it; re-audit
> passes; only then `save_answer` writes it. A separate answer that surfaces "[9:128]" is
> HARD-FAILED, scrubbed, never cached.

---

## §d · Failure modes (where the design breaks)

### d1 — Question the corpus doesn't cover

**Problem:** "What does Khalifa say about cryptocurrency?" — no corpus coverage, no verse
coverage. **Design response:** the contract + gate force abstention: *"The Quran and
Khalifa's available writings do not directly address this."* This is correct behavior, not
a bug. **Risk:** abstention fatigue if it happens too often; **test:** a deliberately
out-of-corpus question must produce an abstention, not a training-knowledge essay.

### d2 — Paraphrase-without-citing

**Problem:** the model states a corpus idea in its own words but omits the citation, so the
audit labels it `unsupported` even though it *is* grounded. **Design response:** the revise
loop returns it; the model adds the citation (the chunk is in its context). **Risk:**
unnecessary regenerations inflate latency; **mitigation:** the contract emphasizes "cite
the chunk you used"; **test:** an answer that paraphrases a retrieved chunk without a cite
gets one regeneration that adds the cite (not a drop).

### d3 — Sources disagree (rare under Khalifa-only)

**Problem:** two Khalifa-corpus chunks (e.g. an early vs. late SP article) appear to
conflict. **Design response:** present both with their locators ("In *SP* 1985-02 Khalifa
wrote …; in Appendix 24 he framed it as …") — surfacing Khalifa's own range is in-scope and
honest. **Risk:** the SP paragraph-vs-issue attribution caveat (COMPOSER_CONSTRAINTS.md) —
a short SP notice may not be Khalifa's own words; **mitigation:** prefer lead articles,
carry `byline_note` into the chunk; **test:** conflicting chunks yield a "Khalifa expressed
both…" presentation, not a silent pick.

### d4 — Gate laundering / citation that doesn't support

**Problem:** model cites a chunk that doesn't actually support the claim to pass the gate
(§b risk). **Design response:** the audit checks *entailment* of the claim by the cited
evidence, not mere citation presence. **Risk:** NLI weakness; **test:** a claim with a
deliberately mismatched corpus citation is labeled `unsupported`, not `corpus-grounded`.

### d5 — Cache poisoning via history replay

**Problem:** `req.history` replays prior contaminated turns (Phase 1 §1, entry 6) into a
new composition. **Design response:** history is model-authored context, not a *source* —
the contract already forbids treating prior assistant text as a source; the audit runs on
the *new* answer regardless of history. **Residual:** if the model copies a contaminated
claim from history, the audit catches it as `unsupported` on the new answer. **Test:** a
history seeded with a hadith claim does not let an unsupported claim survive the new audit.

---

## §e · Integration with existing infrastructure

- **The chokepoint.** All changes land in `shared_agent.agent_stream` + `chat.py`
  (new tool) + `prompts/system_prompt*.txt` (contract) + a new `source_audit.py`
  (the gate, extending `citation_verifier.py`). No app-file logic changes — the apps only
  flip new `AgentConfig` flags.
- **New `AgentConfig` flags (default-off, per-app):** `enable_corpus_retrieval`,
  `enable_source_audit` (with mode `advisory|blocking`), `enable_no_surface_scrub`,
  `gate_cache_on_audit`. Frozen-dataclass pattern preserved; rollout is per-app and
  reversible by flipping a flag (Phase 1 §4).
- **Cache.** `save_answer` gains an audit gate (only clean answers cached). The injection
  prompt's "add new information if needed" is rewritten to "use these only as a starting
  point; they are subject to the same source rule." Legacy-cache fate (purge vs.
  audit-and-quarantine) is an **operator decision** (open question 2) — *out of scope to
  execute here*, but the design's end-state assumes the cache is eventually audit-clean.
- **Reasoning memory.** Unchanged in content; add an audit-verdict field to the
  `ReasoningTrace` (the existing `HAS_CITATION_CHECK` pattern extends naturally to a
  `HAS_SOURCE_AUDIT`) so contamination rates are observable over time.
- **Tool-use loop.** Mostly unchanged — all 21 tools stay; one tool added; the
  multi-tool-discipline map gains a `"khalifa commentary"` class so interpretive questions
  must hit the corpus.
- **The four apps — does the rewire apply to all four? YES.** Because all four route
  through `shared_agent.agent_stream` (confirmed Phase 1: `app.py`/`app_lite.py`/
  `app_full.py` are `backend="anthropic"` with `chat.SYSTEM_PROMPT`; `app_free.py` is
  Ollama/OpenRouter with `system_prompt_free.txt`). The rewire is *defined once* in the
  shared module; each app opts in via flags. **`app_free.py` is the canonical user-facing
  app** and should be the first to flip the flags to blocking; the Anthropic apps (lower
  latency, easier audit budget) can run the gate in blocking mode immediately. Both system
  prompts need the contract rewrite (two files, same contract text).

### Concrete test scenario (integration)

> With `enable_corpus_retrieval=True`, `enable_source_audit="blocking"`,
> `gate_cache_on_audit=True` set on `app_free`'s `AGENT_CONFIG`, a single `/chat` request
> for an interpretive question: routes through `agent_stream`, calls verse tools + the new
> corpus tool, composes under the contract, audits, regenerates once if needed, ships a
> clean answer via SSE, and writes a clean entry to the cache — all without any app-file
> code change beyond the flags.

---

## Summary table — layers, modules, flags

| Layer | New / changed module | `AgentConfig` flag | Closes leak |
|---|---|---|---|
| Corpus retrieval | `chat.py` (`search_khalifa_corpus` + dispatch + TOOLS); vector index (Task C) | `enable_corpus_retrieval` | L2 (gives interpretation a source) |
| Composition contract | `prompts/system_prompt*.txt`; retry trigger in `shared_agent.py` | (prompt-level; retry reuse) | L2, L3 |
| Source audit | new `source_audit.py` (extends `citation_verifier.py`) | `enable_source_audit=advisory\|blocking` | L2, L5 |
| No-surface scrub | promote `scripts/check_no_surface_rule.py` to runtime | `enable_no_surface_scrub` | (9:128/129 output rule) |
| Cache gate | `answer_cache.save_answer` + `shared_agent.py` call site | `gate_cache_on_audit` | L1, L4 |
