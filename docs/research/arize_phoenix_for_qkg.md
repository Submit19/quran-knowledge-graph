# Arize Phoenix — relevance to QKG

Written 2026-05-15. One of the companies in the operator's flagged
YouTube video (AIE Miami Day 2, with Cerebras, OpenCode, Cursor,
Arize AI). I couldn't fetch the talk's transcript, so this isn't an
analysis of what was said. It's a snapshot of what Arize Phoenix is,
based on training-time knowledge, and where it would fit in QKG's
roadmap.

Pairs with `docs/QKG_RETROFIT_PLAN.md` augmenting-tools list (Phase 5
infrastructure additions).

**Caveat:** training cutoff is January 2026; Arize Phoenix has been
moving quickly. Verify current capabilities against
[arize.com/docs/phoenix](https://arize.com/docs/phoenix) before
committing time to integration.

---

## What Phoenix is

Phoenix is Arize AI's open-source LLM observability tool. Self-hostable
(Apache 2.0 license). Targets LLM-app developers, not ML ops teams.
Three main capabilities:

1. **Tracing** — every LLM call, tool invocation, retrieval, and
   embedding lookup gets captured as an OpenTelemetry span. The
   tracing UI lets you drill into a single agent run, see every
   step, every prompt, every response.

2. **Evaluation** — built-in LLM-as-judge framework with templates
   for the common evaluations (Q&A correctness, hallucination
   detection, retrieval relevance). Calibration helpers — though
   the workflow is less prescriptive than QKG's Phase 4c plan.

3. **Datasets + experiments** — you save eval datasets, run a model
   change against them, get a diff vs the prior baseline. Closer to
   our Phase 4a's runner than to our Phase 4c calibration.

It's the LLM-app equivalent of what Datadog is to web services.
Langfuse is the closest competitor (more startup-oriented; Phoenix is
more academic-Arize-research-oriented).

## Where it would fit in QKG's roadmap

### Strongest fit: Phase 5 + Phase 9

The "augmenting tools" list in the retrofit plan includes:
- **Langfuse (self-hosted) or LangSmith (managed)** — LLM observability
- **Cost + latency observability** — augmenting-tools item #5

Phoenix is a direct alternative to Langfuse for this slot. The choice
between them is largely about preference, not capability:

| Dimension | Phoenix | Langfuse |
|---|---|---|
| License | Apache 2.0 | MIT |
| Self-hostable | Yes (Docker, K8s) | Yes (Docker, K8s) |
| Cloud option | Arize Cloud (paid) | Langfuse Cloud (free tier) |
| Python SDK ergonomics | Decorator-based, OTel-native | Decorator-based, ad-hoc |
| Built-in evals | More extensive | Lighter; defer to LangChain |
| Tracing UI | Polished, jupyter-friendly | More dashboard-oriented |
| Cost-tracking | Yes (per-trace token + USD) | Yes |
| Production hardening | Newer; some sharp edges | Older; better tested |

Honest take: either works. If the operator has existing affinity for
one, that wins. If starting fresh: Langfuse is slightly more proven
for production; Phoenix is slightly more pleasant for dev/notebook
workflows.

### Secondary fit: Phase 4 eval infrastructure

Phoenix's eval module overlaps with what Phase 4a is building. Key
question: is Phase 4a's hand-rolled runner the right call, or should
QKG adopt Phoenix's eval framework?

Arguments for hand-rolled (what we're doing):
- Full control over the rubric, judge prompts, calibration loop
- No new dependency at the eval boundary
- Aligns with the audit's recommendation: behaviour-asserted eval,
  domain-specific to QKG's tool-call shape
- The Phase 4a deliverable is ~400 lines of code; not over-engineered

Arguments for Phoenix:
- Battle-tested calibration helpers (we're rolling our own in Phase 4c)
- Integrates tracing + evals — same dataset can be both the eval set
  and the production trace store
- "Did this PR regress quality?" workflow is built-in; we're hand-
  rolling the diff-vs-baseline comment for the CI workflow

Honest take: **the hand-rolled runner is the right call for Phase 4a.**
QKG's rubric (citation accuracy / answer completeness / tool path /
framing) is too domain-specific to fit neatly into Phoenix's templates.
But Phoenix would be a strong fit at the LAYER BELOW — using Phoenix
for trace capture in production, then using QKG's own runner for the
rubric scoring.

The integration shape that would make sense:
1. Phoenix instruments `shared_agent.agent_stream` via OpenTelemetry
2. Every production chat request becomes a trace in Phoenix
3. QKG's Phase 4a runner reads from Phoenix's trace store for
   historical evals (not just synthetic eval-set runs)
4. The eval-set runner stays QKG-native; the production observability
   is Phoenix

This is a Phase 5 / 9 task, not Phase 4. Don't blend them.

## Concrete integration sketch (deferred, not for now)

If/when QKG adopts Phoenix (suggest Phase 9 alongside the ADR cleanup):

1. **`pip install arize-phoenix arize-phoenix-otel`** (~50 MB)
2. **Add a Phoenix server to docker-compose** for local dev; pointed at
   a SQLite or Postgres backend for trace storage
3. **Instrument shared_agent.agent_stream** with the OTel decorator
   pattern:
   ```python
   from phoenix.otel import register
   tracer_provider = register(project_name="qkg", endpoint="...")

   @tracer.start_as_current_span("agent_turn")
   def _agent_turn(...): ...
   ```
4. **Instrument dispatch_tool** with per-tool spans:
   ```python
   @tracer.start_as_current_span("tool_call")
   def dispatch_tool(...):
       span = trace.get_current_span()
       span.set_attribute("tool.name", tool_name)
       span.set_attribute("tool.duration_ms", duration)
       ...
   ```
5. **Surface Phoenix UI** as a separate dev endpoint (not user-facing):
   `http://localhost:6006` is Phoenix's default

After integration, the operator can:
- Click into any production chat, see the full agent run
- Filter traces by tool error / high latency / specific question patterns
- Cross-reference an eval result with the production traces that
  matched the same question

## What Phoenix does NOT solve for QKG

- **The "did the model say the right thing" problem.** Phoenix captures
  what the model said; deciding if it's right is still LLM-as-judge or
  human review. QKG's Phase 4 owns that question. Phoenix would be
  downstream of the eval, not a replacement for it.
- **The Khalifa positioning question.** Audit finding #5 is product-
  strategy, not observability.
- **The 21-tool sprawl.** Phoenix can show which tools are called
  most/least; it doesn't decide which should be removed.

## Recommended action

Do nothing about Phoenix until **Phase 9**, when the meta-system
hygiene work lands. At that point, the ROI tracking (audit #37) needs
production data — Phoenix is one of two reasonable options for
collecting it (the other being Langfuse).

In the meantime: don't pre-integrate. The hand-rolled Phase 4 runner
is the right primary investment.

## If the AIE Miami talk specifically pitched Phoenix features

When the operator gets the transcript (the YouTube research session
should produce it), check whether Arize introduced anything new that
changes the calculus above. Particularly worth watching for:

- **Phoenix's calibration tooling** — if it's substantially better
  than what Phase 4c plans to hand-roll, consider adopting earlier.
- **OTel-native trace storage** in the Anthropic / Ollama SDKs —
  changes the instrumentation surface and could make Phoenix the
  default observability stack at near-zero cost.
- **Datasets-as-trace-filters** — if Phoenix lets you build eval
  datasets by filtering production traces, that's the workflow QKG
  Phase 4d should adopt.

If none of those are in the talk: this doc's recommendation (Phase 9
adoption, hand-rolled eval in Phase 4) stands.

## References

- Phoenix docs: https://arize.com/docs/phoenix
- Phoenix GitHub: https://github.com/Arize-ai/phoenix
- Comparison with Langfuse: search "Phoenix vs Langfuse" — both
  publish their own comparisons; Langfuse's is more honest
- Original AIE Miami video that prompted this note:
  https://www.youtube.com/live/DeM_u2Ik0sk (Day 2)
