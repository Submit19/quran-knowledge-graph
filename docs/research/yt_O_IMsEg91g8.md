# AIE Europe Keynotes & OpenClaw ft DeepMind, OpenAI, Vercel, @pragmaticengineer, @mattpocockuk

Source: https://www.youtube.com/live/O_IMsEg91g8
Channel: AI Engineer (livestream)
Duration: ~9 hours (livestream of full conference day)
Date analysed: 2026-05-15
Transcript captured: yes, auto-generated English, 9,239 snippets at `data/research/yt_O_IMsEg91g8_transcript.txt`

Note: this is the **second day of AIE Europe (London)**, not Miami. Heavy on
DeepMind / OpenClaw-maintainer talks and a Pragmatic Engineer (Gergely Orosz)
fireside.

## What the talk(s) cover

- **DeepMind talk (~42:21-65:00)** — Several non-language-model topics:
  Gemini Embeddings 2 (omnimodal, Matryoshka representation learning),
  Graphcast / Gencast / FGN weather models, "the team is relentless."
- **Liam Hapton, OpenClaw maintainer (~177:00-191:30)** — Commit-maxing at
  scale (3,000 commits/day), swim-lane agent management, refactor-via-AI
  (the "great refactor" — 2,700 commits, ~1M LOC, 82% of core codebase
  touched in one night), git-worktrees-per-PR, "engineer becoming factory
  manager, bottleneck becomes taste."
- **Radik, OpenClaw maintainer (~194:00-260:00)** — "Giving the keys to my
  life to OpenClaw." Step-by-step process: WhatsApp → telegram → discord →
  knowledge-base access via Obsidian (3,000 markdown pages), Karpathy's
  viral tweet on LLM knowledge bases.
- **Pragmatic Engineer fireside (~462:00-540:00)** — Gergely Orosz +
  someone (Swix?) on the state of AI engineering, what's changed at the
  Pragmatic Engineer newsletter.

## Speakers / companies / tools mentioned

- **Google DeepMind** — Gemini Embeddings 2; Graphcast / Gencast / FGN
  weather models.
- **OpenClaw** — Maintainers Liam Hapton, Radik, Vincent, Peter. Pushing
  800-3000 commits/day at peak. ~10-15 core maintainers with day jobs.
  Uses git worktrees per agent session (one maintainer found 70-80
  active worktrees on his machine).
- **NemoClaw** — Nvidia variant of OpenClaw being built.
- **Anthropic (referenced)** — Building a new C compiler with autonomous
  agents.
- **Spotify (referenced)** — "No longer writing code by hand."
- **Steve Jger** — "Vibe maintainer," pushes ~50 PRs/day solo.
- **Vercel skills.sh** — Skill-deploy mechanism Liam uses.
- **HF skills CLI** — Hugging Face's skill set for agents.
- **Pragmatic Engineer** — Gergely Orosz; newsletter.

## Specific techniques, patterns, or claims worth noting

1. **DeepMind talk [47:08-51:14]**: **Gemini Embeddings 2** is fully omnimodal
   — one embedding model produces a single vector representing text (up to
   8K tokens), 128s of video, 80s of audio, or a full PDF.
2. **DeepMind [51:14-51:30]**: **Matryoshka Representation Learning (MRL)** —
   same network produces different embedding dimensions. Start retrieval
   with 256 dims (fast first-pass), expand to full dims for fine-grained
   reranking. Trades expressiveness against speed at retrieval time.
3. **DeepMind [52:01-56:00]**: **Graphcast → Gencast → FGN** — weather forecast
   models that beat physics-based simulations. Gencast is probabilistic, was
   more accurate than 1,300 gold-standard benchmarked forecasts 97% of the
   time, and produced 15-day forecasts in 8 minutes on a single chip vs.
   hours on a supercomputer. Tangential to QKG, but the architectural
   pattern (spherical-graph neural network with mesh nodes, autoregressive
   prediction across 100 variables) is intriguing.
4. **Liam [177:50-179:50]**: "Engineers writing code and editors — not so
   much. Swarms across repos. Engineers are becoming factory managers, and
   the bottleneck becomes taste." Anthropic / Spotify / OpenClaw all push
   commit volumes that 2024 maintainers would call astronomical.
5. **Liam [180:38-181:13]**: "This reminds me of Ralph looping — give it a
   task, burn tokens for 8-9 hours, wait, hope something happens. What if
   we had a more opinionated approach? What if we call it Bart looping?
   Do we need more than just tokens? What does that reward mechanism look
   like? How do we get more opinionated?" Direct callout to the Ralph
   loop pattern; suggests "Bart looping" as a more curated alternative.
6. **Liam [184:25-186:00]**: **Swim lanes** as the agent-management
   abstraction. Each lane is a tracked agent session. Lanes 1-2 might be
   low-attention refactors ("just commit, just push them through"), lanes
   3-4 are conversational features, lane 5 is P0/P1 triage. "Tokens are no
   longer the problem — it's raw compute and my brain space to keep an eye
   on these sessions."
7. **Liam [186:14-186:55]**: "The one thing I have complicated in my life
   is adopting git worktrees, and I kind of wish I hadn't. When you're
   running an extremely heavy test harness, every PR-attach ends up
   becoming a new git worktree. I end up with close to 70-80 active
   worktrees on my machine on any given day, and that's kind of hell."
   He built self-healing logic for codex sessions that crash on worktrees;
   recommends "just clone the repo 10 times and point 10 codex sessions
   to each."
8. **Liam [188:30-189:25]**: Skill management as engineering. Open-source
   his `.skills` directory (alongside `.dotfiles`); uses "skills gym"
   (Aga); runs Codex through sessions, has it read the logs, makes
   improvements to the skill, deploys via Vercel `skills.sh`. "There's a
   process to how I manage and maintain my skills as an engineer."
9. **Liam [190:24-191:30]**: "There is evals, surprisingly. After
   refactoring we built a fake Slack with synthetic and real models to run
   evaluation loops checking each provider and channel works." Evals run
   not against the agent's quality, but against the harness's correctness
   under refactor.
10. **Radik [194:00-198:40]**: Step-by-step adoption — never one big leap.
    Started with WhatsApp single-channel, migrated to telegram → discord;
    added one workflow at a time. "If something breaks, I take one small
    step back, fix it, see what doesn't work, understand why, have a setup
    that it never happens again, and just take one step further again."
11. **Radik [198:48-200:30]**: 3,000-page Obsidian vault as agent knowledge
    base — work, personal, tasks, projects, research, articles, links.
    Multiple search layers: normal search, QMD search for Obsidian,
    separate memory for workspace. "Everything is interlinked and that's
    where that magic happens." References Karpathy's viral tweet on LLM
    knowledge bases.

## Honest verdict — relevance to QKG

### HIGH

- **Matryoshka Representation Learning is directly applicable to QKG's
  BGE-M3 embeddings.** BGE-M3 already supports MRL (multiple output
  dimensions from the same model). QKG currently uses full 1024-dim
  embeddings for all retrieval. Adding a two-tier retrieval — 256-dim
  first-pass (fast, broad recall), 1024-dim second-pass on top-K (precise
  ranking) — would cut retrieval-stage compute substantially with minimal
  recall loss. Affects Phase 7 sprawl-cleanup (or could ride alongside).
  **Proposed task.**

- **Gemini Embeddings 2 is a candidate for re-evaluating QKG's embedding
  choice.** The audit's "SKIP Aura Agent migration" decision was made
  because it locked QKG to Google's stack. Gemini Embeddings 2 is now a
  standalone API and is fully omnimodal. Worth a head-to-head against
  BGE-M3-EN on QRCD — but only AFTER Phase 4's v2 eval lands, since the
  whole point is to have a real benchmark. Affects Phase 6 (re-verify
  prior decisions). **Proposed task, lower priority.**

- **Liam's "swim lanes" + git-worktrees pain is a direct warning for
  Phase 5 item 19 (tick isolation via worktrees).** The retrofit plan
  prescribes `git worktree add -b "ralph/$TICK_ID"` per tick. Liam's
  hard-won finding: heavy test harnesses + many worktrees = "hell." He
  recommends cloning the repo N times instead. Worth incorporating into
  Phase 5's design (currently calls disk cost "~50-200MB per active
  worktree" without flagging the test-harness interaction). Affects Phase
  5 item 19 (revise approach). **Proposed task — Phase-5 amendment.**

- **Liam's "skill engineering" workflow maps onto the audit's Phase 7 +
  Phase 11 (loop scope tightening and resume).** Liam runs Codex through
  its own logs, has it write improvements to the skill, deploys, repeats.
  This is the Ralph loop with a clearer reward signal: did the skill
  improve eval scores? QKG's Ralph loop currently has `file_min_bytes` as
  acceptance and is moving to `python_test_passes` (Phase 2 item 8). The
  natural next step is "did the v2 eval improve?" — which is Phase 4 + 11.
  Validation of direction, not a new task.

### MEDIUM

- **Radik's "3,000-page Obsidian + agent memory" pattern is what QKG's
  reasoning-memory subsystem could grow into.** Today it captures Query /
  ReasoningTrace / ToolCall / RETRIEVED edges per query. Radik's setup
  layers: normal search, vault-specific (QMD) search, workspace memory.
  QKG could expose its reasoning-memory subgraph as a query target ("show
  past traces that retrieved 2:255 and were rated >= 4 by the judge") so
  the agent can recall its own prior reasoning. Related to Phase 9 item
  36 (decide on reasoning-memory subgraph). MEDIUM not HIGH because
  capability already exists via `recall_similar_query` tool — needs
  *extension*, not invention.

### LOW

- DeepMind's weather models (Graphcast/Gencast/FGN) are intriguing but
  no QKG application.
- The Pragmatic Engineer fireside is industry-state context, not
  actionable.
- Commit-maxing at OpenClaw scale (3,000/day) doesn't map onto QKG's
  scope.

## Quote-worthy moments

- DeepMind [50:54]: "Matryoshka representation learning lets you have the
  same network but represent different dimensions. You could start out
  doing a retrieval using only 256 dimensions and then expand that to get
  more expressiveness."
- Liam [178:17]: "We're now switching to a world where engineers writing
  code and editors — not so much. Swarms across repos. Engineers are
  becoming factory managers, and the bottleneck becomes taste."
- Liam [180:42]: "This reminds me of Ralph looping. What if we had a more
  opinionated approach? What if we call it Bart looping? Do we need more
  than just tokens? How do we get a bit more opinionated? Yes, let's run
  loops, but let's be a bit more smart about how we do this."
- Liam [186:21]: "The one thing I have complicated in my life is adopting
  git worktrees, and I kind of wish I hadn't. When you're running an
  extremely heavy test harness, every PR-attach ends up becoming a new
  git worktree. I end up with close to 70-80 active git worktrees on my
  machine on any given day. And that's kind of hell."
- Liam [188:50]: "I have skills. I call it skills similar to dotfiles —
  both my `.skills` and `.dotfiles` are on GitHub, it's all open source.
  Some of my skills are private but there's skills in there for writing
  technical documentation that I co-created with other DevEx engineers."
- Liam [191:18]: "It's no longer about the model or the agent. It's about
  the process. 2025 was about token-maxing. 2026 is about not wasting
  them. It's about token efficiency. It's about agent-in-the-loop."
- Radik [197:51]: "If something breaks, I take one small step back, fix
  it, see what doesn't work, understand why it didn't work, have a setup
  that it never happens again, and just take one step further again."
- Radik [198:48]: "I gave it my knowledge base. I have about 3,000 pages
  or notes — markdown files in my Obsidian. This is everything: work
  stuff, personal stuff, tasks, projects, research, articles. It then
  finds the connections and puts it in context to other stuff I have."
