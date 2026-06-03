# Composer Rewire — Phase 4: Phased Implementation Plan

_Builds on `02_design_proposal_2026-05-28.md`. Each sub-phase is independently
mergeable in its own advisor session. Branch convention: `claude/composer-rewire-<n>-*`._

The plan slices the design into **five** atomic sub-phases ordered by dependency.
Each flips a defined set of the Phase 3 xfail tests
(`tests/test_composer_design_{a,b,c}_*.py`) from xfail → pass, removing the
`@pytest.mark.xfail` marker **in the same commit** as the implementation (project
TDD discipline). Effort is S (≤2h) / M (½–1 day) / L (multi-session).

```
   ┌─ Task C (corpus indexing, SEPARATE session — hard dependency for SP-1)
   │
SP-1 ──► SP-2 ──► SP-3 ──► SP-4 ──► SP-5
(corpus  (compose (source   (cache   (per-app
 tool)    contract) audit)   gate)    rollout)
```

---

## SP-0 (pre-req, NOT this project): Index the Khalifa corpus — **Task C**

Out of scope for the rewire itself but **hard-blocks SP-1**. A separate session
indexes `data/khalifa_corpus/**` (~527K words, text + sermons) into a vector store
with paragraph-coherent chunks retaining frontmatter provenance
(`title, bucket, source_url, chunk_id, flagged_9_128_129, byline_note`). Both corpus
branches must be merged first. **The rewire treats the index as an external
dependency** — SP-2…SP-5 can proceed in a degraded "verse-only + abstain-on-
interpretation" mode if SP-0/SP-1 slip.

---

## SP-1 — Khalifa-corpus retrieval tool

- **Scope:** add `tool_search_khalifa_corpus` to `chat.py`, register it in `TOOLS`,
  wire it into `dispatch_tool`. Reuse `retrieval_gate._get_reranker` (shared BGE
  singleton). Returns chunks with citable provenance. Add `enable_corpus_retrieval`
  to `AgentConfig` (default-off) and the `"khalifa commentary"` class to
  `required_tool_classes`.
- **Definition of done:** the tool retrieves ranked chunks for a query against the
  SP-0 index and returns provenance fields; a corpus call is mandated for
  interpretive questions via the discipline map.
- **Flips to passing:** `test_composer_design_a_corpus_retrieval.py::`
  `test_composer_uses_khalifa_corpus_for_commentary` (both asserts: tool in `TOOLS`
  + `tool_search_khalifa_corpus` dispatch fn).
- **Rollback:** `enable_corpus_retrieval=False` on every app's `AGENT_CONFIG`
  disables the tool with zero behavior change; the tool code is dead until flipped.
- **Effort:** **M** (retrieval glue + tests; assumes SP-0 index exists).
- **Dependencies:** SP-0 (Task C index). No dependency on SP-2…SP-5.

## SP-2 — Context-only composition contract

- **Scope:** rewrite the source section of `prompts/system_prompt.txt` +
  `prompts/system_prompt_free.txt` to the "no source chunk, no claim" contract
  (generalize the Code-19 discipline); teach `(Khalifa, <work>, <locator>)` citation
  form; rewrite the `build_cache_context` injection line (drop "add new information
  if needed"); change the citation-density retry trigger in `shared_agent.py` from
  *count* to *provenance coverage* (regenerate on uncited claims, not on "too few").
- **Definition of done:** both prompts carry the contract; the retry path no longer
  rewards raw citation volume; cache-injection wording no longer licenses fill.
- **Flips to passing:** none on its own (prompt changes are behavioral, not
  unit-assertable); it is the *enabling* change that makes SP-3's audit pass at low
  regeneration rates. Verified by SP-3's tests + a manual eval-set spot check.
- **Rollback:** revert the two prompt files + the retry-trigger diff (small,
  self-contained). No data migration.
- **Effort:** **S** (prose + one retry-condition change).
- **Dependencies:** none hard; best landed before SP-3 so audits start from a
  contract-shaped baseline. Can land before SP-1.

## SP-3 — Source-audit gate (`source_audit.py`)

- **Scope:** new `source_audit.py` extending `citation_verifier.py`. Implement
  `audit_answer(answer_text, retrieved_verses, retrieved_corpus_chunks) -> AuditResult`
  (atomic-claim decomposition → per-claim provenance label via NLI/MiniCheck against
  *both* evidence sets → `passed`, `claims`, `unsupported_claims`, `invalid_citations`)
  and `scrub_no_surface(text) -> (clean_text, violations)` (promote
  `scripts/check_no_surface_rule.py` regex to runtime, broaden to prose forms). Wire
  the draft→audit→revise(×1)→abstain loop into `shared_agent.agent_stream` behind
  `enable_source_audit="advisory"|"blocking"` (default off). Add `HAS_SOURCE_AUDIT`
  to reasoning memory.
- **Definition of done:** an interpretive answer is decomposed, each claim labeled,
  unsupported claims trigger one regeneration then abstention; 9:128/129 surfaces are
  HARD-FAILED and scrubbed; advisory mode logs without blocking.
- **Flips to passing:** all of `test_composer_design_b_*` (`rejects_non_source_claim`,
  `cites_every_claim`) **and** `test_composer_design_c_*`
  (`never_surfaces_9_128_129`, `blocks_hadith_reference`). **4 of 5 tests.**
- **Rollback:** `enable_source_audit` unset → gate is inert; `scrub_no_surface` is
  pure and side-effect-free; revise loop only fires when the flag is on.
- **Effort:** **L** (the heaviest sub-phase — claim decomposition, double-NLI,
  revise loop, precision/recall measurement on a labeled set).
- **Dependencies:** SP-1 (needs `retrieved_corpus_chunks` to exist) for the
  corpus-grounded path; the no-surface + verse-only paths can be built/tested without
  SP-1. SP-2 recommended-before to keep regeneration rates sane.

## SP-4 — Cache gate (`save_answer` behind the audit)

- **Scope:** gate `answer_cache.save_answer` (and its `shared_agent` call site) behind
  `gate_cache_on_audit` so only audit-passing answers are cached (fail-closed on
  audit error). State + document the legacy-cache end-state (purge-and-rebuild vs.
  audit-and-quarantine — **operator-decided**, see briefing open question 2);
  executing the legacy cleanup is a separate session.
- **Definition of done:** a contaminated answer is never written to the cache; clean
  answers are; the flag default-off preserves current behavior.
- **Flips to passing:** none directly (cache behavior is integration-tested, not in
  the design xfail set); guard with a new small unit test on the gated `save_answer`.
- **Rollback:** `gate_cache_on_audit=False` restores ungated caching.
- **Effort:** **S** (one call-site gate + a guard test).
- **Dependencies:** SP-3 (needs `AuditResult`).

## SP-5 — Per-app rollout (advisory → blocking)

- **Scope:** flip the four flags per app. Sequence: **shadow/advisory first**
  (measure unsupported-claim and false-positive rates from `HAS_SOURCE_AUDIT`
  telemetry), then **blocking**. Anthropic apps (`app.py`/`app_lite.py`/`app_full.py`)
  first (lower latency, easier audit budget); `app_free.py` (canonical, slower local
  path) last after the revise-loop cost is measured.
- **Definition of done:** all apps run `enable_source_audit="blocking"`,
  `gate_cache_on_audit=True`, `enable_corpus_retrieval=True`,
  `enable_no_surface_scrub=True`; telemetry shows the blocking gate's
  false-positive/over-abstention rate is within an operator-set tolerance.
- **Flips to passing:** none new (the tests are unit-level on the modules); this is
  the integration milestone the design's §e integration scenario describes.
- **Rollback:** per-app flag flip back to advisory or off — no code revert needed.
- **Effort:** **M** (rollout + telemetry watch; mostly observation, not code).
- **Dependencies:** SP-1…SP-4.

---

## Suggested session order

1. **SP-2** (S, no deps) — land the contract early; cheap, reversible.
2. **SP-0 / Task C** (separate track) — corpus index; unblocks SP-1.
3. **SP-1** (M) — corpus tool. Flips test §a.
4. **SP-3** (L) — the audit. Flips tests §b + §c (4 tests).
5. **SP-4** (S) — cache gate.
6. **SP-5** (M) — rollout, advisory→blocking, per app.

A natural cut line for a first shippable increment: **SP-2 + SP-3's no-surface +
verse-only audit in advisory mode** — this delivers the runtime 9:128/129 scrub and
contamination *telemetry* with no dependency on Task C, flipping the
`never_surfaces_9_128_129` test and de-risking the heavy SP-3 work before the corpus
index lands.
