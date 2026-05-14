# AIE Europe Keynotes & Coding Agents ft. Pi, Google DeepMind, Anthropic, Cursor, Linear, & more

Source: https://www.youtube.com/live/_zdroS0Hc74
Channel: AI Engineer (livestream)
Duration: ~9 hours (livestream of full conference day)
Date analysed: 2026-05-15
Transcript captured: yes, auto-generated English, 9,836 snippets at `data/research/yt__zdroS0Hc74_transcript.txt`

Note: this is **AIE Europe (London)**, not Miami — the operator's brief
listed it under "AIE Miami" but the title and content (DeepMind / Linear /
Pi opener) are the European edition.

## What the talk(s) cover

Multi-track Europe livestream. QKG-relevant talks:

- **Open-models intro talk (~10:40-30:30)** — Gemma 3, per-layer
  embeddings, llama.cpp flag for offloading per-layer embeddings to CPU.
- **David Sora Par (creator of MCP, member of technical staff at
  Anthropic, ~30:35-49:24)** — "The future of MCP." Progressive discovery,
  programmatic tool calling, what's coming in MCP 2026. *This is the
  highest-value section of all four videos for QKG.*
- **Ido Salman (Agent Craft / MCPUI creator, ~49:24)** — Agent
  orchestration, building UIs that ship via MCP.
- **Coding-agents track (~340:00-540:00)** — Multiple talks on
  Cursor / Linear / OpenCL / agentic-loop workflows. Less directly
  applicable to QKG.

## Speakers / companies / tools mentioned

- **MCP / Anthropic** — David Sora Par; reached 110M monthly SDK downloads
  (faster than React); just spun out an open-source foundation.
- **FastMCP** — community Python SDK; David admitted it's "way better than
  the Python SDK we shipped."
- **Cloudflare MCP server** — referenced as the canonical Code Mode example.
- **Linear, Slack, Notion** — example SaaS-integration MCP servers.
- **Agent Craft / MCPUI** — Ido Salman; building UI components shipped via
  MCP servers.

## Specific techniques, patterns, or claims worth noting

1. **David [30:30-32:14]**: "MCP Applications" — a server can ship its
   own UI alongside tools. Take the server, drop it into Claude / ChatGPT /
   VS Code / Cursor, the UI just works. Requires both client and server to
   understand the same semantics — that needs a protocol, not a plug-in.
   "The model interacts with it through tools; the human interacts with it
   through the application."
2. **David [33:25-34:09]**: 110M monthly MCP-SDK downloads; "React took
   roughly double the time to reach that download volume." Reached via
   OpenAI Agents SDK, Google ADK, LangChain, thousands of frameworks as
   transitive dependencies.
3. **David [34:28-35:48]**: 2024 = demos; 2025 = coding agents (ideal
   sandbox case: local, verifiable, has a compiler); 2026 = general agents
   doing knowledge-work tasks (financial analysis, marketing). The 2026
   shift's bottleneck is *connectivity* — agents need to reach 5 SaaS apps
   + a shared drive — and there's no single solution: "anyone who tells
   you there's one solution to all connectivity problems, be it computer
   use or MCP, is pretty wrong."
4. **David [35:48-38:03]**: 2026 connectivity stack = **skills + MCP + CLI/
   computer-use**, all three. Skills = file-based domain knowledge. CLI =
   pre-training-aware, composable in bash, needs a sandbox. MCP = rich
   semantics, UI, decoupled, enterprise (auth/governance). "The best agents
   will use every available method."
5. **David [38:34-40:21]**: **Progressive Discovery**. The protocol just
   moves info across the wire; the client is responsible for *what to do*
   with it. Don't dump all tools into context upfront — give the agent a
   `tool_search` tool that *defers* loading. The model goes "ah, maybe I
   need a tool now," looks up which tools, and loads them on demand.
   "Massive reduction in tool context usage" was shown for Claude Code
   before/after adding this.
6. **David [40:24-42:46]**: **Programmatic Tool Calling / Code Mode**.
   Give the agent a *script tool* — a code-execution environment like a V8
   isolate, Monty, Lua interpreter — and have the model write code that
   composes tool calls. "What you're effectively doing [in tool-use loops]
   is letting the model orchestrate things together, and in that
   orchestration, you're using inference. It's latency-sensitive and could
   be done way more effective if you'd instead write a script." Uses MCP's
   `structured output` feature to give models return-type info so they
   can compose tool calls.
7. **David [42:46-44:30]**: "Stop taking REST APIs and putting them
   1:1 into an MCP server. Every time I see someone building another
   REST-to-MCP converter, I cringe. Design *for an agent.*"
8. **David [44:30-46:54]**: MCP 2026 roadmap:
   - Stateless transport (proposal from Google) — easier to scale on
     hyperscalers; June.
   - Async tasks primitive — agent-to-agent communication.
   - SDK v2 for TypeScript + Python (FastMCP-influenced).
   - Cross-app access via existing identity providers (no re-login).
   - Server discovery on well-known URLs (auto-discover MCP server for any
     website).
   - **Skills over MCP** — ship updated domain-knowledge skills from the
     server, no plug-in mechanisms.
9. **David [48:01]**: "2026 is all about connectivity, and the best agents
   use every available method — computer use, CLIs, MCPs, skills."

## Honest verdict — relevance to QKG

### HIGH

- **Progressive discovery / `tool_search` is the most actionable single
  finding across all four videos.** QKG has 21 tools whose descriptions
  consume context budget every turn, every chat session. Adding a meta-tool
  that returns the top-K relevant tools given a query would shrink the
  system prompt and free budget for retrieved verses. This is an
  *alternative path* to Phase 7 item 28 (consolidate 21 → 8-10) — keep
  the 21 tools, but expose them via deferred loading. The empirical
  Anthropic data (Claude Code before/after) is strong evidence this works.
  Affects Phase 7 item 28. **Proposed task** with concrete acceptance
  criteria.

- **Code Mode / Programmatic Tool Calling is a serious architectural
  alternative for QKG's agentic loop.** Currently QKG's flow is:
  agent picks a tool → tool returns → agent picks next tool (up to 15
  turns). Each turn pays the full prompt-cache and re-injects all prior
  tool-call results. A Python-script tool that lets the agent compose
  `semantic_search → find_path → get_verse_words → query_typed_edges` in
  one execution would cut turns and tokens dramatically. Trade-off: harder
  to verify, larger blast radius (sandbox needed). Worth a spike. Affects
  Phase 7 item 28 as another alternative. **Proposed task.**

- **Skills-over-MCP is the right model for shipping Khalifa-specific
  domain knowledge.** QKG's system prompt currently inlines Khalifa
  context (mathematical miracle of 19, rejection of hadith, etc.). If QKG
  ever exposes itself as an MCP server (audit wish-list item), shipping
  that context as a skill that travels *with* the server is cleaner than
  putting it in every client's system prompt. Affects the audit's "MCP
  server exposure" wish-list. **Proposed task.**

### MEDIUM

- **David's "2026 connectivity stack = skills + MCP + CLI" recasts the
  QKG MCP-server decision.** The wish-list item assumed a single
  exposure mechanism. The conference consensus is the right answer is
  *both* a CLI binary (`qkg-cli get-verse 2:255`) *and* an MCP server, with
  the CLI being lower-cost to ship and more discoverable to models that
  were trained on similar tools (Quran APIs are not standard pre-training
  material — caveat).

- **Stateless MCP transport + cross-app access matter only if QKG ships
  an MCP server.** Watch the June 2026 spec release before committing to
  a 2025-shape implementation.

### LOW

- The coding-agents track (Cursor / Linear / Pi / OpenCL maintainer talks)
  doesn't translate to QKG's domain.

## Quote-worthy moments

- David [31:08]: "This is an MCP application. That's an agent shipping its
  own interface, not through a plug-in, not through an SDK, not rendered on
  the fly by the model on the client side or hardcoded into the product."
- David [34:51]: "Coding agents are the most ideal scenario for an agent.
  It's local, it's verifiable, you can call a compiler, you have a developer
  who can fix shit if it goes wrong in front of the computer."
- David [35:36]: "In my mind, connectivity is not one thing. If someone
  tells you there's one solution to all your connectivity problems, be it
  computer use or MCP, they are probably wrong."
- David [38:54]: "Most people when they think about MCP think about context
  bloat. But if you really consider what a protocol does — a protocol just
  puts information across the wire, but the client is responsible for
  dealing with that information."
- David [40:01]: "Use something like tool search to defer the loading of
  the tools and start loading the tools when the model needs it."
- David [40:25]: "What you're effectively doing [with sequential tool calls]
  is you're letting the model orchestrate things together. And in that
  orchestration, you're using inference. It's latency-sensitive and all of
  it could be done way more effectively if you would instead write a
  script."
- David [42:54]: "Every time I see someone building another REST-to-MCP
  conversion tool, it's a bit cringe. Design for an agent."
- David [48:36]: "The best agents use every available method. They will
  use computer use, they will use CLIs, they will use MCPs, and they will
  use skills."
