# AIE Miami + Europe — Cross-Video Synthesis for QKG

Date: 2026-05-15
Author: Claude (research session, branch `claude/research-aie-miami-2026`)
Operator-brief deliverable for triage; no production code touched.

Source per-video docs:
- [yt_DeM_u2Ik0sk.md](yt_DeM_u2Ik0sk.md) — AIE Miami Day 2 (Cerebras / OpenCode / Cursor / Arize)
- [yt_6IxSbMhT7v4.md](yt_6IxSbMhT7v4.md) — AIE Miami Keynote (OpenCode / DeepMind / OpenAI)
- [yt__zdroS0Hc74.md](yt__zdroS0Hc74.md) — AIE Europe Day 1 (Pi / DeepMind / Anthropic / Cursor / Linear)
- [yt_O_IMsEg91g8.md](yt_O_IMsEg91g8.md) — AIE Europe Day 2 (DeepMind / OpenAI / Vercel / @pragmaticengineer)

Note: the operator-brief listed all four as "AIE Miami." In reality videos 3
and 4 are AIE Europe (London). The synthesis is filed under "aie_miami_*" per
the brief's filename guidance, but the content is cross-conference.

---

## Themes that appeared across multiple videos

### 1. MCP context bloat is the #1 problem, and the consensus answer is *progressive discovery + Code Mode*

Mentioned by David Sora Par (creator of MCP, AIE Europe Day 1), Kent C. Dodds
(AIE Miami Keynote), Rita / Cloudflare (AIE Miami Keynote), and indirectly by
Lori Voss / Arize (AIE Miami Day 2). Strong signal — four independent
speakers, three different conferences/days, same prescription.

**The pattern:**
- Dumping all MCP tool descriptions into the system prompt at session-start
  inflates context (Cloudflare's full OpenAPI ≈ 2.3M tokens; QKG's 21 tools
  are smaller but the principle holds).
- **Progressive discovery**: give the agent a `tool_search` meta-tool that
  returns the top-K relevant tool descriptions on demand. Anthropic shipped
  this in Claude Code, showed "massive reduction in tool context usage."
- **Code Mode / Programmatic Tool Calling**: give the agent a script-
  execution tool (V8 isolate, Monty, Lua) and have the model write code
  that *composes* tool calls. Cuts agent turns dramatically (Lori
  measured 12 → 5 turns on tier-4 GitHub tasks).

### 2. "Use control flow for control flow, not prompts"

Said directly by Dexter (AIE Miami Keynote); echoed by Rita on Code Mode
("LLMs are very good at writing code; tool calling was bolted on at the
end"); echoed by Anna at Pinterest with her LangGraph + SQL-template
pattern. The consistent advice: switch statements > prompt branching,
deterministic flows > LLM-driven orchestration, smaller models on
smaller modular prompts > big model on monolithic prompt.

### 3. Knowledge graphs are having a moment, and decision-trace / audit is the lead use case

Nia (Neo4j, AIE Miami Day 2) gave the marquee talk on "context graphs." Alvin
(OutRrival, AIE Miami Day 2) mentioned knowledge graphs as part of the
"derived memory" spectrum. Radik (OpenClaw, AIE Europe Day 2) described
Obsidian's 3,000-page interlinked graph as the substrate for his personal
agent. The repeated framing: **knowledge graphs solve auditability /
explainability / decision-trace, which are the lifecycle gaps that pure
vector retrieval can't close.**

### 4. Evals are existing-software's tests, not ML's metrics

Lori (Arize, AIE Miami Day 2): "I don't know why the eval industry decided we
were going to call these things 'evals' rather than 'logs and tests' which
is what they are." Dexter (AIE Miami Keynote): "You need a process and then
you need a defensible metric." Liam (OpenClaw, AIE Europe Day 2): "There is
evals, surprisingly. We built a fake Slack with synthetic models so we can
run evaluation loops to check that each provider and channel works." The
treating-evals-as-tests framing is exactly Phase 4 of the QKG retrofit.

### 5. 2026 connectivity stack = skills + MCP + CLI, used together

David Sora Par named it explicitly. Liam (OpenClaw) shipped his `.skills`
directory alongside his `.dotfiles`. Kent / Cloudflare wrap MCP in CLI-style
ergonomics via Code Mode. Lori's eval compared MCP-vs-skills-vs-CLI and the
practical answer was "use whichever works for the task" — agents that
combine all three are the strongest.

### 6. The bitter lesson is back — for memory and orchestration

Alvin (AIE Miami Day 2) explicitly invoked the bitter lesson: "General
methods leveraging massive computation will outperform approaches built on
human domain knowledge." His Dynamic Memory Discovery (DMD) approach
beats years of vector-DB / KG pipeline research by giving the model raw
files and a planning loop. David Sora Par's Code Mode is the same idea
applied to tool orchestration. Karpathy's quote (cited by Alvin and
Radik): "It's a skill issue. Today's LLMs can solve most tasks; it's
just a matter of getting the right things into the right window at the
right time."

---

## Patterns directly applicable to QKG

Grouped by which retrofit phase they affect.

### Phase 4 (behaviour-asserted eval) — extensions

- **Add latency / cost / tool-fidelity dimensions to the v2 rubric.** Lori's
  eval was 5 metrics: correctness, output quality, latency, cost, tool
  fidelity. Phase 4 currently has 4 LLM-as-judge dimensions; latency and
  cost are objective (wall clock, token count) and would not need a judge.
  Tool fidelity (% allowed tool calls / total tool calls) is exactly the
  kind of falsifiable behaviour-assert metric Phase 4 wants and catches
  the "EXHAUSTIVE SEARCH MANDATE" over-call problem in a single
  measurement.
- **LLM-judge explanations as iteration signal.** Lori used the LLM's
  one-sentence explanation alongside its score to iterate the eval itself
  (caught bugs in his harness). Phase 4 already plans this implicitly
  (judge produces "0-5 integer score and one-sentence justification") —
  but the synthesis lesson is to *aggregate the explanations*, not just
  the scores, to identify systematic harness issues.

### Phase 5 (loop taming) — revisions

- **Liam's git-worktree warning.** Phase 5 item 19 proposes
  worktree-per-tick isolation. Liam at OpenClaw runs 70-80 active
  worktrees on his machine and called it "hell" — the test harness +
  many worktrees combination is the problem. He suggests just cloning the
  repo 10 times instead. The Phase 5 doc should incorporate this lesson:
  document the disk + harness cost up front; cap concurrent worktrees;
  consider clone-N-times as an alternative isolation primitive for the
  test-running step.

### Phase 6 (re-verify recent unverified work)

- **Re-evaluate Gemini Embeddings 2 against BGE-M3-EN.** The audit's
  "SKIP Aura Agent" decision was made when the only way to access Gemini
  embeddings was via Aura's stack-locked deployment. Gemini Embeddings 2
  is now a standalone API and omnimodal. Worth a head-to-head on QRCD,
  but only AFTER Phase 4's v2 eval is the gating measurement (otherwise
  we're back to anecdotal claims).
- **Re-verify `bge-reranker-v2-m3` on QRCD.** Phase 6 item 22 already
  has this. The conference content doesn't add new evidence, but Lori's
  observation that reranker choice is "a bet" (Alvin's framing) confirms
  the audit's caution about taking the 32-pt-lift claim at face value.

### Phase 7 (trim sprawl) — alternatives

- **Tool consolidation has two paths now.** Phase 7 item 28 says
  "Consolidate 21 tools toward 8-10." The conference suggests two
  alternatives that don't require deletion:
  - *Progressive discovery* (David Sora Par): keep 21 tools, expose via
    `tool_search`. Smaller prompt, same capability.
  - *Code Mode* (Rita, Kent): keep 21 tools, expose them as functions in
    a Python sandbox the agent writes code against. Fewer turns, same
    capability.
  Item 28 should be revised to "*pick an exposure strategy* for the 21
  tools" — consolidation is one option, not the default.
- **Promote `classify_query()` from prompt to code.** Phase 7 item 29
  already says this. Dexter's "use control flow for control flow" is
  independent validation — strengthens the priority.
- **Split `run_cypher` by authority.** Phase 7 item 30 audits `run_cypher`.
  Anna's Pinterest pattern suggests splitting it: a read-only Cypher tool
  with no schema-modifying verbs, *plus* a separate `cypher_admin` tool
  that simply isn't in the agent's tool list. Cleaner than a regex
  denylist.

### Phase 9 (honest meta-system)

- **Nia's "context graph" concept is what QKG's reasoning-memory subgraph
  already is.** Phase 9 item 36 ("decide on the reasoning-memory
  subgraph") gets a stronger directional answer: keep it; expose
  decision-trace traversal as a queryable tool (the agent should be able
  to ask "show me past traces that retrieved 2:255 and were rated
  positively"); separate label-guard from production graph but don't
  delete.
- **Reasoning-memory lifecycle.** Alvin's three components of memory
  (state / curation / **lifecycle**) call out a gap in QKG: today every
  query writes a `:ReasoningTrace`, nothing prunes. Define a
  forgetting/decay policy.

### A potential new phase: "Phase 12 — Connectivity surface"

Conference-strong signal that 2026's win is connectivity (skills + MCP +
CLI). If QKG's audience is "agent-tooling developers" (per Phase 8 item 31's
options), shipping a thin CLI binary first (`qkg-cli get-verse 2:255`) and
a Code-Mode-shaped MCP server second is a coherent strategy. The CLI is
discoverable; the MCP server is rich. Skills-over-MCP carries Khalifa-
specific context with the server. This is a wish-list expansion of the
current audit, not a current-phase item.

---

## Patterns explicitly NOT applicable

- **Cloudflare-scale MCP optimisation** — Rita's talk solves a problem at the
  scale of 1.7M-token contexts spanning workers, R2, DNS, observability,
  cache. QKG's 21-tool prompt is ~2-4K tokens. The pattern (progressive
  discovery, Code Mode) still applies; the scale doesn't.
- **OpenClaw / Anthropic / NemoClaw commit-maxing (3,000 commits/day)** —
  doesn't fit QKG's solo-developer-with-paused-Ralph-loop reality.
- **Pinterest's LangGraph-based stateful workflow** — QKG's queries are
  single-turn agentic loops, not multi-step approval workflows. The
  *philosophy* (authority/risk pairing) applies; the *framework* doesn't.
- **Dexter's "surfing the models" / new-model-every-week thinking** —
  QKG is currently on Sonnet 4.x and Ollama / OpenRouter free-tier
  fallbacks. The dance of swapping providers weekly isn't QKG's reality
  and the audit explicitly says "no speculative abstraction without two
  failing tests" — that rules out a model-selection profile system
  inspired by this content.
- **DMD (Dynamic Memory Discovery) replacing QKG's graph substrate** —
  Alvin's "throw out the vector DB and KG, just use files + agent"
  pattern works *because* his memory problem is unstructured. QKG's
  graph IS the substrate, not auxiliary memory; the bitter-lesson move
  here would be removing the graph entirely, which would defeat the
  purpose. The *lifecycle* sub-lesson does apply.
- **Cerebras / Cursor / OpenRouter scale + cost stats** — context, not
  action.
- **Karpathy's "skill issue" framing as a justification to do nothing** —
  cited by multiple speakers as cover for "we don't need engineering,
  just bigger models." The audit explicitly rejects this; QKG's problems
  are engineering problems (test discipline, eval rigour, tool sprawl).

---

## Companies / tools worth deeper investigation

| Tool / company | Why look at this | URL |
|---|---|---|
| **Arize AI + Phoenix** (Lori Voss) | Eval framework with LLM-judge + trace inspection + experiment tracking. QKG's Phase 4 lands evals; Arize is one shape Phase 4's CI integration could take, alongside Langfuse / LangSmith from the existing wish list. | arize.com |
| **MiniCheck-FT5** | Already in QKG (`citation_verifier.py`). Not directly conference-referenced, but Lori's LLM-judge framing reinforces that QKG's existing citation_verifier is on the right axis. | github.com/Liyan06/MiniCheck |
| **OutRrival's DMD blog post** | "How I built the most accurate memory system in the world in 5 days." Frames memory as state + curation + lifecycle — useful for the reasoning-memory cleanup. | outrival.com |
| **Cloudflare Code Mode reference** | The architectural reference for programmatic tool calling. Dynamic worker loaders + bundle execution. | cloudflare.com (blog) |
| **HumanLayer CRISPY prompts** | Dexter's open-source planning prompts (3-prompt baseline that he suggests breaking into 8). Useful if QKG ever splits its system prompt by query bucket. | humanlayer.dev |
| **Nia's context-graph-demo.vercell.app** | Live demo of Neo4j + agent + decision-trace graph rendering. Architectural reference for exposing QKG's reasoning memory as a UI artefact. | context-graph-demo.vercell.app |
| **Vercel skills.sh + claude-skills-vault** | Skill-deploy mechanisms Liam uses. Worth knowing if QKG ever ships "Khalifa context" as a portable skill. | skills.sh ; github.com (search) |
| **Gemini Embeddings 2** (DeepMind) | Omnimodal, Matryoshka representation learning. Candidate to re-evaluate against BGE-M3 once Phase 4's eval is the gating measurement. | deepmind.google |
| **FastMCP (Python SDK)** | Anthropic's David admitted it's better than the official Python SDK. If QKG ever exposes MCP, start here. | github.com (search) |

---

## Surprises (positive or negative)

### Positive surprises

- **The conference consensus on MCP-context-bloat solutions is almost
  exactly what QKG's retrofit Phase 7 item 28 implies but doesn't yet
  prescribe.** Tool-search-based progressive discovery + Code Mode are
  not in the current retrofit plan but they fall directly out of item
  28's "consolidate 21 tools" goal as alternative paths. This means the
  Phase 7 plan can be enriched, not contradicted.
- **Nia's "context graph" pattern is essentially what QKG already does
  with `reasoning_memory.py`.** Independent validation from a Neo4j
  representative at a 1000-person conference is strong evidence that the
  audit's preserve-the-Neo4j-graph stance is correct.
- **Lori's LLM-judge eval (with explanations) maps onto Phase 4 exactly.**
  The conference content gives us specific metric additions (latency,
  cost, tool fidelity) without changing the philosophy. Phase 4 is on
  the right track.

### Negative surprises (worth flagging)

- **Lori's data shows MCP server exposure is not free.** The audit's
  wish-list includes "Expose QKG as an MCP server" as a high-strategic
  add. Lori's 500-test eval shows that MCP-based agent loops take 2.4×
  more turns and burn far more tokens than CLI-based ones on a mature,
  representative tooling (GitHub MCP). Before investing in an MCP server,
  QKG should sanity-check whether its tool surface would have the same
  fixed-API-multi-call problem.
- **Liam's worktree warning contradicts Phase 5's tick-isolation design.**
  Phase 5 item 19 proposes worktree-per-tick. Liam at OpenClaw scale
  ran into "hell" with 70-80 active worktrees. QKG's loop runs one
  tick at a time so it's much less likely to hit this, but the
  isolation design should account for it explicitly.
- **The conference enthusiasm for "agent-in-the-loop / autonomous swarms"
  is exactly what the audit pauses.** Liam pushes 3,000 commits/day,
  OpenClaw 800 commits/day, "Bart looping" as a more curated Ralph.
  The retrofit's deliberate scope shrink (Phase 5: cut research /
  vault-hygiene / ADR-backfill from loop dispatch) goes against this
  current. Worth noting that the loop-taming decision is contrarian
  *but well-reasoned* — the audit's 62%-DONE_WITH_CONCERNS finding
  contradicts the "more autonomy = more progress" narrative.
- **No one mentioned RLHF, fine-tuning, or DPO as solutions.** Several
  speakers waved the bitter lesson at these techniques. For QKG, which
  is firmly post-training and has no fine-tune in the loop, this is
  reassurance that the audit's "no new ML training" stance is consensus
  industry direction in 2026.

---

## How this synthesis was produced

- All four transcripts captured via `youtube-transcript-api` (skill at
  `~/.claude/skills/yt-transcript-skill`). 34,283 lines total.
- Per-video docs grounded in time-stamped quotes (see individual docs).
- Synthesis written from the per-video docs only; not from a re-read of
  raw transcripts.
- Three-hour soft cap in the brief; ~2.5 hours used; remaining budget
  goes to the proposed-tasks YAML and commits.
