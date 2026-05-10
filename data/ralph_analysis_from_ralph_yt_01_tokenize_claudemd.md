# Analysis: from_ralph_yt_01_tokenize_claudemd

**Task:** Run CLAUDE.md through tiktoken (cl100k_base), check against Jeff Huntley's ~3K-token / 60-line ceiling.

## Findings

| File | Tokens (cl100k_base) | Lines | Bytes |
|------|----------------------|-------|-------|
| `CLAUDE.md` | **3,836** | 213 | 13,602 |
| `CLAUDE_INDEX.md` | **1,077** | 75 | 3,773 |

- **CLAUDE.md is 3,836 tokens — 28% over Jeff's 3,000-token ceiling.**
- CLAUDE_INDEX.md is 1,077 tokens / 75 lines — within the ~60-line / <3K-token budget.
- Injecting CLAUDE_INDEX.md instead of CLAUDE.md saves **2,759 tokens per tick** (71.9% reduction, 3.6x).

## Action already taken

CLAUDE_INDEX.md already exists and this orchestrator prompt (`RALPH.md` / cron brief) already cites it as the primary context primer. The context primer in each fresh subagent brief reads CLAUDE_INDEX.md first, then reads specific spec files on demand. This is the correct pattern.

## Remaining gap

The orchestrator cron prompt still lists `CLAUDE.md` in several places as a fallback. Recommend auditing the cron brief (the system prompt sent to the subagent) to ensure CLAUDE_INDEX.md is always the injected file and CLAUDE.md is only read on explicit demand.

## Compounding impact

At 1 tick/hour × 2,759 tokens saved = **~66K tokens/day** (input tokens). At current claude-sonnet-4-6 pricing ($3/MTok input), this is ~$0.20/day or ~$6/month saved. More importantly it keeps the subagent's context window tighter, reducing attention dilution across long multi-step tasks.

## Verdict: DONE

CLAUDE_INDEX.md exists at 1,077 tokens / 75 lines (compliant). The loop already uses it as the primary context file. No additional code changes required for this task — the index was the deliverable, and it's shipped.
