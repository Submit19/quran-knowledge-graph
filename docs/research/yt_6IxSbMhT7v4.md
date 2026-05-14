# AIE Miami Keynote & Talks ft. OpenCode, Google DeepMind, OpenAI, and more!

Source: https://www.youtube.com/live/6IxSbMhT7v4
Channel: AI Engineer (livestream)
Duration: ~7.5 hours (livestream of full conference day)
Date analysed: 2026-05-15
Transcript captured: yes, auto-generated English, 7,749 snippets at `data/research/yt_6IxSbMhT7v4_transcript.txt`

## What the talk(s) cover

Day-1-keynote-track livestream. QKG-relevant talks:

- **Dexter / Dax Rods (OpenCode founder, ~17:09)** — Context engineering, the
  CRISPY workflow, instruction-budget thinking. Coined "context engineering."
- **Shashank Goyal (OpenRouter, ~143:00)** — Stats: 75T tokens/month, 5M users,
  60 providers, 300 models. Argues benchmarks are gamed and user-vote rankings
  are the real signal.
- **Jeff (~276:31)** — "Dumb zone" / context-window degradation (referenced
  by Dexter, not deeply transcribed).
- **Anna (Pinterest, ~346:14)** — "From tickets to PRs: shipping a governed
  Snowflake ops agent with LangGraph and MCP."
- **Kent C. Dodds (~407:34)** — Kodi, his personal agent built on Cloudflare
  with three MCP tools (search, execute, third). Heavy on Cloudflare's Code
  Mode pattern.
- **Rita (Cloudflare VP of Product, ~429:21)** — Building infrastructure for
  billions/trillions of agents. Deep dive on MCP context bloat (Cloudflare's
  full OpenAPI = 2.3M tokens) and Code Mode as the solution. Live demo of
  "vanilla MCP agent" vs "Code Mode agent."

## Speakers / companies / tools mentioned

- **OpenCode** — Dexter / Dax / Frank's open-source coding agent. "Surfing
  the models" mental model.
- **OpenRouter** — Shashank; model-aggregator. ~75T tokens/mo, 300+ models.
  Benchmark-ranking page based on user dollar-votes, not lab scores.
- **HumanLayer** — Dexter referenced the open-source CRISPY prompts (3
  prompts, suggested users break them into 8).
- **Pinterest** — Anna's team built a Snowflake ops agent with LangGraph.
- **LangGraph** — Workflow-orchestration framework for stateful agents
  (entry points, re-entry, exit, state-on-ticket, restartable from where
  it left off).
- **Snowflake MCP** — Anna used this for metadata sub-agent inside her
  governed ops workflow.
- **Cloudflare** — Code Mode + dynamic worker loaders + artifacts (Kent and
  Rita).
- **Kodi (heycodi.dev)** — Kent's personal agent. 3 tools: search, execute,
  one more. Secrets management pattern: agent never sees secrets, user
  enters via HTTPS UI, agent references via `{{curly-braces}}`.
- **Fluma** — Rita's "fake Luma" demo app for Code Mode comparison.

## Specific techniques, patterns, or claims worth noting

1. **Dexter [43:55-46:01]**: "Surfing the models" — context engineering keeps
   you 1-5-10% ahead of naive prompting; new model lands, your work becomes
   irrelevant, but you push the new frontier. By turn 20 of a long-horizon
   agentic task, 99% vs 97% per-turn compounds to a 27% gap.
2. **Dexter [42:48-46:01]**: "Use control flow for control flow, not
   prompts." Don't put `if input is X do Y else Z` in a system prompt;
   write a switch statement. They split their CREATE_PLAN mega-prompt of
   85 instructions into 3 prompts of <40 each: faster, more accurate,
   could be run on a smaller dumber model. Quote: "More attention spread
   out over more instructions is not going to fix this."
3. **Dexter [42:48]**: "Dumb zone" — past ~100k tokens (Claude) accuracy
   degrades. Not just "too much info" but "too many instructions."
4. **Dexter [48:00-51:14]**: **CRISPY** = Questions, Research, Structure-
   outline, Plan, Implement (the Y is just for the acronym). Five phases
   to plan, before implementing. Each phase produces a markdown artifact
   that humans bot-check, the agent reads. "Hides the ticket from the
   researcher programmatically" — research has its own one-shot context
   window over generated questions, not the original ticket.
5. **Dexter [51:08-52:36]**: "There is no magic prompt. We actually don't
   publish the CRISPY prompts because the core of this is: understand
   context engineering and instruction budgeting. Break it down into
   smaller workflows. Use the open-source ones from HumanLayer as a
   starting point and break their three prompts into eight."
6. **Anna [351:30-353:18]**: "Match agent authority to workflow risk." For a
   SOC-compliant system: agent does interpretation, context-gathering, SQL
   gen, PR creation; cannot write to production, cannot run its own SQL,
   cannot approve its own PR. Boundaries are explicit, not negotiated by
   the agent.
7. **Anna [361:30-362:25]**: Use SQL templates with explicit hand-off
   instructions: "It's up to you to figure out how many roles you need,
   but use this template. Don't make assumptions, don't insert semicolons
   where they shouldn't be." Templates are guard-rails; the agent has
   judgement over which template, not over the schema.
8. **Kent [416:30-418:43]**: MCP context-bloat critique is bad reasoning:
   "We see a problem, we don't say it's foundationally flawed and run away.
   We do a search on the MCP tools and load only the relevant ones. Claude
   does this now, ChatGPT does this now." (This is the same point David
   Sora Par makes in video 3 — see `yt__zdroS0Hc74.md`.)
9. **Kent [418:00-419:30]**: "Code Mode" pattern: take an MCP/OpenAPI
   spec → generate TypeScript definitions → tell agent to write code
   against them → eval in a sandbox (Cloudflare dynamic worker loaders).
   Cloudflare did 2 tools (search, execute); Kent added a third.
10. **Rita [433:24-438:20]**: Cloudflare's full OpenAPI = 2.3M tokens (more
    than biggest model context window). Solving by splitting into
    per-domain MCP servers doesn't really solve it — it pushes the picker
    problem onto users. Code-Mode demo: "create event each day in May 2026"
    — vanilla MCP agent confused about dates and tried to confirm, Code
    Mode agent wrote a script that pulled `today()` and iterated.

## Honest verdict — relevance to QKG

### HIGH

- **Dexter's "use control flow for control flow, not prompts" is exactly
  what Phase 7 item 29 says.** Item 29: "Promote `classify_query()` from
  prompt to code. Demote prompt rubric to fallback." Dexter's stage-talk is
  independent validation of that retrofit direction. The instruction-budget
  framing is also useful for QKG: the system prompt is large (Khalifa
  context + 21 tool descriptions + EXHAUSTIVE SEARCH MANDATE). Splitting
  the EXHAUSTIVE SEARCH MANDATE out of the agent's main prompt and into
  per-tool descriptions would be a direct application. Affects Phase 7
  item 29 + a new mini-task. Proposed task: split system prompt into
  classification + per-bucket sub-prompts, measure with v2 eval.

- **Code Mode is a serious alternative to the "consolidate 21 tools
  to 8-10" Phase 7 item 28.** Instead of cutting tools, expose them via a
  smaller programmatic interface where the agent writes Python that calls
  multiple tools per turn. This trades agent turns for code-execution
  surface. For QKG's Neo4j-heavy retrieval (where many queries naturally
  compose: "search → find_path → get_verse_words"), this could collapse
  3-5 tool-use turns into one Python script. Worth a spike. Affects
  Phase 7 item 28 (alternative path).

- **Rita's 2.3M-token OpenAPI observation parallels QKG's 21-tool prompt
  situation.** Not as extreme — QKG's tool descriptions are probably 2-4K
  tokens — but progressive discovery (load tool descriptions on demand via
  a `tool_search` meta-tool) would shrink the system prompt and free
  context budget for retrieved verses. Affects Phase 7 item 28.

### MEDIUM

- **Anna's "match agent authority to workflow risk" framing applies to
  `run_cypher`'s denylist guard** (Phase 7 item 30: "audit + log every
  `run_cypher` invocation. Regression-test the denylist."). Currently QKG
  treats `run_cypher` as a single escape-hatch tool with a regex denylist.
  Anna's pattern would split it: a "read-only Cypher" tool and a
  "schema-modifying Cypher" tool, where the latter does not exist in the
  agent's tool list at all. Affects Phase 7 item 30.

- **Dexter's CRISPY (planning before implementation) is more relevant to
  Ralph-loop tick scheduling than to QKG itself.** The loop already does
  research/eval ticks alternated with implementation ticks; CRISPY's
  insistence on planning artifacts as separate markdown docs is what the
  loop already does badly (62% DONE_WITH_CONCERNS design docs). Worth
  knowing but not a task — the retrofit's Phase 5 specifically *cuts back*
  on this scope.

### LOW

- Terminal-tooling demos (T-Max, term-draw, hunk) — irrelevant to QKG.
- OpenRouter scale stats — interesting but no action.
- Pinterest's Snowflake-specific patterns are too domain-specific.

## Quote-worthy moments

- Dexter [42:48]: "Don't use prompts for control flow if you can use control
  flow for control flow. Switch statements and if-statements are actually
  kind of good."
- Dexter [45:34]: "If you're doing long-horizon agentic tasks, by turn 20
  the difference between 99% and 97% is a 27% gap because this compounds."
- Dexter [51:14]: "There is no magic prompt. We actually don't publish the
  CRISPY prompts because the core of this is: understand context
  engineering and instruction budgeting."
- Anna [352:11]: "Match agent authority to workflow risk."
- Anna [354:23]: "It can't approve its own changes."
- Kent [417:31]: "[The criticism is] 'There's just context bloat and it's
  a huge mess.' Well, we're software developers. We see a problem, we
  don't just say 'this is foundationally flawed' and go off to something
  else. We could just do some sort of search on the MCP tools and now we
  have just the ones that are relevant for the thing we're doing."
- Rita [436:28]: "Are we holding this wrong? We're trying to make LLMs do
  things that they're not that good at. We're inflating the context window.
  What's a different way to attempt to do this? And that's where Code Mode
  came from."
- Rita [435:51]: "It's not too dissimilar from if you took Shakespeare and
  you gave him a month-long crash course in Mandarin. I presume he was
  extremely smart, so if you asked him to write a play in Mandarin, it's
  bloody Shakespeare, so it's gonna be good, but it's not going to be his
  best work."
