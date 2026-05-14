# AIE Miami Day 2 ft. Cerebras, OpenCode, Cursor, Arize AI, and more!

Source: https://www.youtube.com/live/DeM_u2Ik0sk
Channel: AI Engineer (livestream)
Duration: ~7.5 hours (livestream of full conference day)
Date analysed: 2026-05-15
Transcript captured: yes, auto-generated English, 7,460 snippets at `data/research/yt_DeM_u2Ik0sk_transcript.txt`

## What the talk(s) cover

This is a full-day conference livestream covering ~10 talks. The QKG-relevant
talks are:

- **David House (G2I, organiser)** — opener on "transforming programming
  mindsets" / case studies in agentic coding adoption.
- **Nia Mlinaric (Neo4j)** at ~146:08 — "Context Graphs" / structural retrieval
  / using knowledge graphs to give agents auditable decision traces.
- **Alvin (OutRrival)** at ~319:00 — "Dynamic Memory Discovery" / how to think
  about agent memory; bitter-lesson framing against vector-DB-heavy pipelines.
- **Stefan Abram (OpenCode)** at ~416:53 — "Multimodal future is open source";
  the "3 Rs" (Resist / Rush / Rain) framework for enterprise AI adoption.
- **Lori Voss (Arize AI, ex-npm)** at ~428:07 — A real 500-test evaluation of
  GitHub MCP vs CLI-skills, with five metrics including tool fidelity.

Other talks (Le on mobile MPUs, Tis, Fidian, Lena demo, Dave Kiss) were less
directly QKG-applicable and are skipped here.

## Speakers / companies / tools mentioned

- **Neo4j** — Nia represented Neo4j; demo at `context-graph-demo.vercell.app`;
  uses Neo4j Graph Data Science (GDS) plugin, FastRP graph embeddings,
  PageRank centrality.
- **OutRrival** (out-rival.com) — Alvin's company; published blog post "How I
  built the most accurate memory system in the world in 5 days" (LongMemEval).
- **OpenCode** — open-source coding agent; Frank+Dax (founders), Stefan
  (head of business). Ramp case study: 30% of merged PRs from Ramp's "Inspect"
  agent built on OpenCode in a couple of months.
- **Arize AI** — observability + eval framework. Lori is head of DevRel.
- **Anthropic Claude Agent SDK** — Lori built his eval atop the same SDK that
  powers Claude Code.
- **MIT NANDA initiative** — 2025 GenAI Divide report, "95% of AI pilots
  deliver no measurable P&L impact" (cited by Nia).
- **LongMemEval** — Conversational AI memory benchmark, recently saturated to
  100% (Alvin).
- **Skills repos referenced by Lori**: LoHub, claude-skills-vault.

## Specific techniques, patterns, or claims worth noting

1. **Nia [149:43-152:11]**: Vector search captures *meaning*, knowledge graphs
   capture *connections*. "Every retrieval pipeline we use operates on one
   dimension — text similarity. There's a second dimension almost no one
   builds on: structural similarity (are these entities connected in the
   same way?)."
2. **Nia [156:21-156:56]**: Telecom benchmark from Zhang et al. (eunations Mar
   2026 on 3GPP QA): base model 37% → fine-tune 54% → KG+RAG 91%. "Rag alone
   does not close the accuracy gap."
3. **Nia [167:00-167:08]**: "Context graph" = knowledge graph specifically
   designed to capture decision traces — full context, reasoning, and causal
   relationships behind every significant decision. Differs from an audit log
   in that it captures the *why*, not just transaction history.
4. **Nia [174:00-175:32]**: Hybrid (vector + graph) demo uses Neo4j GDS:
   FastRP for graph-structure embeddings + vector similarity for semantic
   matching, both surfaced through MCP-exposed tools.
5. **Alvin [321:24-322:30]**: "Every additional assumption is new surface area
   to be wrong." When you use an embedding model you bet on semantic
   similarity; when you chunk you bet on the right slices being made
   before any question is asked; when you rerank you bet on your ranking
   being better than the agent's.
6. **Alvin [323:33-324:31]**: Dynamic Memory Discovery (DMD) approach to
   LongMemEval: NO vector storage. Just file system + raw JSON sessions +
   agent orchestrator with file-tools + plan file. Outperformed years of
   pipeline research. Bitter-lesson application: "general methods leveraging
   massive computation will outperform approaches built on human domain
   knowledge."
7. **Alvin [325:00-326:50]**: Three components of memory: **state**
   (place for context to live), **curation** (right things into the context
   window at the right time), **lifecycle** (what persists, what updates,
   when to forget). LongMemEval benchmarks only test state+curation, not
   lifecycle. Production failure modes even at 100% benchmark score:
   temporal reasoning, entity disambiguation, principled forgetting.
8. **Alvin [326:00-327:00]**: Memory is a *spectrum* from raw (file-system +
   agent reasoning) to derived (vector DB, KG, learned-summary). Raw is more
   performant on benchmarks; derived buys you production-cost constraints.
9. **Stefan [420:30-424:55]**: Enterprise AI adoption in three stages — Resist,
   Rush (token-max, AI everywhere), Rain (cost matters, model choice matters,
   control matters). Cost varies 60× across coding tools. Uber's CTO said
   coding tools already maxed their 2026 AI budget.
10. **Lori [436:42-447:30]**: 500-test eval of GitHub MCP vs two GitHub
    skills (LoHub 2,187-line reference vs Claude-skills-vault 6× shorter
    playbook). Metrics: correctness (LLM-judge), output quality (LLM-judge),
    latency (wall clock), cost, **tool fidelity** (% allowed tool calls /
    total tool calls). All three got ~high-80s on correctness BUT MCP took
    2.4× more turns (12 vs 5 on tier-4 tasks) and burned far more tokens
    because (a) verbose JSON responses overflowed context, forcing fallback
    to bash+grep; (b) GitHub MCP's fixed API surface required multiple
    calls where CLI could do it in one.
11. **Lori [444:13-444:34]**: One major advantage of LLM-as-judge over binary
    test results: every result is accompanied by an explanation. "You get a
    little LLM buddy who's watching every single test who explains exactly
    what went wrong or right." Used those explanations to iterate the eval
    itself.

## Honest verdict — relevance to QKG

### HIGH

- **Nia's "context graph" / decision-trace pattern is what QKG already does**
  via `reasoning_memory.py` writing `(:Query)-[:TRIGGERED]->(:ReasoningTrace)
  -[:HAS_STEP]->(:ToolCall)-[:RETRIEVED]->(:Verse)`. This is independent
  validation that the approach is sound. **Where it goes further than QKG's
  current implementation**: Nia explicitly captures the *causal chain*
  (why-not-just-what) and pushes for query-able / traversable decision traces,
  which QKG's reasoning memory does store but does not yet expose as a tool.
  Affects Phase 9 item 36 (decide on reasoning-memory subgraph). Proposed task:
  expose decision-trace traversal as a queryable tool, similar to Nia's demo.

- **Lori's 5-metric MCP-vs-CLI eval is directly transferable to Phase 4's
  eval design.** Phase 4 currently specifies citation_accuracy /
  answer_completeness / tool_path_correctness / framing_appropriateness with
  weighted-sum aggregation. **Tool fidelity** (% allowed tool calls / total)
  is not in that list and is exactly the kind of falsifiable behaviour-assert
  metric Phase 4 wants. **Latency and cost** are also missing from Phase 4's
  rubric and matter for QKG's product positioning (agent-tooling devs care).
  Affects Phase 4. Proposed task: add latency, cost, and tool-fidelity
  dimensions to the v2 eval rubric.

- **Alvin's "memory spectrum" framing maps directly onto QKG's reasoning-
  memory architectural choice.** QKG sits firmly on the *derived* end (writes
  structured subgraph to Neo4j). The bitter-lesson position is that the
  *raw* end (file-system + agent) is more performant. For QKG this is
  unlikely to apply — the graph IS the substrate, not just memory — but
  the *lifecycle* component (what persists, what forgets) is genuinely under-
  built in QKG. Today every query writes a trace; nothing prunes. Affects
  Phase 9 item 36 + a new "reasoning-memory lifecycle" concern. Proposed
  task: define + implement a forgetting/decay policy for `:ReasoningTrace`
  nodes older than N days with no incident-graph linkage.

### MEDIUM

- **Lori's discovery that MCP servers can overflow context and force agents
  to fall back to bash/grep is a warning for the audit's wish-list item
  "Expose QKG as an MCP server"** (CLAUDE_INDEX.md, "Once eval works" tier).
  Before investing, run the same kind of head-to-head MCP-vs-CLI eval on a
  QKG task. Proposed in synthesis doc, not as a concrete task yet.

- **Stefan's 3 R's framing legitimises the retrofit's deliberate pause.**
  The audit explicitly pauses the Ralph loop to move from a "Rush" state
  (49 ticks of DONE_WITH_CONCERNS) to a "Rain" state (test-passes gate).
  Not a task, just confirmation.

### LOW

- Stefan's broader claim that "multimodal future is open source" is
  product-positioning; doesn't move QKG.
- The OpenCode / Cursor / Cerebras parts are coding-agent vendor pitches,
  orthogonal to QKG.

## Quote-worthy moments

- Nia [150:59]: "Every retrieval pipeline we're using operates on one
  dimension — text similarity. There's a second dimension that almost no
  one is building on. That's structural similarity. It's not 'do these two
  documents mean the same thing' but 'are these entities connected in the
  same way?'"
- Nia [153:39]: "Better models don't fix fractured context."
- Nia [167:00]: "A context graph is a knowledge graph specifically designed
  to capture your decision traces — the full context, reasoning, and causal
  relationships behind every significant decision."
- Alvin [321:24]: "Every additional assumption is new surface area to be wrong."
- Alvin [325:38]: "What LongMemEval benchmarks fail to evaluate is the
  lifecycle. Our agent is working in the real world. It's doing real things
  and the world is changing. So what persists, what do you update, when do
  you forget?"
- Lori [442:51]: "If you look at latency and cost, things are wildly
  different. MCP is taking way more turns to get the task done — more than
  twice as many turns, about 12 calls per task versus five on the complex
  tier-4 tasks."
- Lori [445:37]: "MCP on its worst run used 71 tool calls. The worst part
  is that only three of those 71 tool calls were actually MCP calls — all
  the rest were the agent messing around with bash and grep trying to parse
  these JSON files it had downloaded."
