#!/usr/bin/env python
"""sonnet_prep.py — Opus pre-warming for [opus]-tagged backlog tasks.

When the next pending IMPL task is tagged [opus], we know the IMPL tick will
spawn a nested Opus subagent. Opus is ~5× Sonnet's per-token cost, so doing
the cheap-but-mechanical part (reading source files, drafting an
implementation outline) on Sonnet first is net-positive:

  Sonnet draft cost:   ~30K tokens × $3/M  = $0.09
  Opus tokens saved:   ~20K tokens × $75/M = $1.50  (worst case)
  Net savings:                              ~$1.40 per opus tick

Even at realistic save rates (~5-10K saved), it's net positive AND produces
a richer plan for Opus to execute against.

Output: `data/sonnet_drafts/<task_id>.md` — read by the IMPL tick's nested
Opus subagent as additional context.

Runs ONLY when the next pending IMPL task in {agent_creative} (sorted by
priority) has [opus] in its description. Otherwise: no-op.

Called by scripts/tick_finalize.py after haiku_prep. Idempotent.

Disable with `SONNET_PREP_DISABLED=1` (e.g. for offline runs or when
Anthropic API is unavailable).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
    import requests
except ImportError as e:
    print(f"[sonnet_prep] missing dependency: {e} — skipping", file=sys.stderr)
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent
DRAFTS_DIR = ROOT / "data" / "sonnet_drafts"
BACKLOG_PATH = ROOT / "ralph_backlog.yaml"
STATE_PATH = ROOT / "ralph_state.json"

SONNET_MODEL = os.getenv("SONNET_PREP_MODEL", "claude-sonnet-4-6")
SONNET_TIMEOUT = 90
SONNET_MAX_TOKENS = 4000


def load_env():
    """Load .env into os.environ (idempotent)."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
    except ImportError:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip()
                if v:
                    os.environ[k.strip()] = v


def find_next_opus_task() -> dict | None:
    """Return the highest-priority pending task tagged [opus], or None."""
    if not BACKLOG_PATH.exists():
        return None
    try:
        b = yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    state = {}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    done = set(state.get("done_task_ids", [])) | set(
        state.get("quarantined_task_ids", [])
    )

    candidates = [
        t for t in b.get("tasks", []) or []
        if t.get("id") not in done
        and t.get("type") == "agent_creative"
        and "[opus]" in (t.get("description") or "").lower()
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda t: -int(t.get("priority", 0)))
    return candidates[0]


def draft_already_fresh(task_id: str) -> bool:
    """Return True if a draft for this task already exists and is non-empty."""
    draft = DRAFTS_DIR / f"{task_id}.md"
    return draft.exists() and draft.stat().st_size > 500


def call_sonnet(prompt: str) -> str | None:
    """Single Anthropic API call. Returns text or None on failure."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("  sonnet_prep: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": SONNET_MODEL,
                "max_tokens": SONNET_MAX_TOKENS,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=SONNET_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"[sonnet_prep] API call failed: {e}", file=sys.stderr)
        return None


def prewarm_task(task: dict) -> bool:
    """Generate an implementation-plan draft for one task. Returns True on success."""
    task_id = task["id"]
    if draft_already_fresh(task_id):
        print(f"  sonnet_prep: draft already exists for {task_id}, skipping")
        return False

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    description = task.get("description", "")
    spec = task.get("spec") or {}
    acceptance = spec.get("acceptance", [])

    # Read project context (small, lean)
    primers = []
    for path_rel in ("CLAUDE_INDEX.md", "STATE_SNAPSHOT.md"):
        p = ROOT / path_rel
        if p.exists():
            try:
                primers.append(f"## {path_rel}\n\n{p.read_text(encoding='utf-8')[:6000]}")
            except Exception:
                pass

    prompt = f"""You are pre-warming an implementation plan for a complex task that will be executed by a separate Opus subagent in the next tick of an automated loop. Your draft is read as additional context so Opus can skip the cold-discovery phase.

## Project context (lean primers)

{chr(10).join(primers)}

## The task

**ID**: `{task_id}`
**Type**: {task.get('type', 'agent_creative')}
**Priority**: {task.get('priority', '?')}
**Description**:
{description}

**Acceptance criteria**:
{json.dumps(acceptance, indent=2)}

## Your job

Produce a focused **implementation plan**, NOT the final deliverable. The Opus subagent will execute the plan against the actual codebase. Your draft should include:

1. **Scope clarification** — what's in scope, what's not, what assumptions you're making
2. **Files to read** — specific file paths in the repo that Opus should examine first
3. **Files to modify** — concrete paths + 1-line description of the change
4. **Sub-step breakdown** — 4-8 ordered steps Opus should execute
5. **Risks / unknowns** — what could go wrong, what Opus should double-check before committing
6. **Acceptance check** — how to verify the deliverable matches the acceptance criteria

Keep it tight (target 600-1000 words). Markdown headings. Cite repo file paths with `repo://path/to/file`. Don't write code unless one specific snippet is the cleanest expression of the plan. Don't try to actually execute anything — you're a planner, not a doer.
"""

    text = call_sonnet(prompt)
    if not text:
        return False

    out = DRAFTS_DIR / f"{task_id}.md"
    out.write_text(
        f"---\n"
        f"task_id: {task_id}\n"
        f"drafted_at: {datetime.now(timezone.utc).isoformat()}\n"
        f"model: {SONNET_MODEL}\n"
        f"purpose: Pre-warmed implementation plan; read by Opus subagent during IMPL tick.\n"
        f"---\n\n"
        f"# Implementation plan: `{task_id}`\n\n"
        f"_Auto-drafted by `scripts/sonnet_prep.py` to reduce cold-discovery cost when the\n"
        f"IMPL tick spawns the Opus subagent. Treat as a starting point, not gospel._\n\n"
        f"---\n\n"
        f"{text}\n"
    , encoding="utf-8")
    print(f"  sonnet_prep: drafted {task_id} ({len(text)} chars)")
    return True


def main():
    load_env()
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[sonnet_prep] starting at {ts}")

    if os.environ.get("SONNET_PREP_DISABLED") == "1":
        print("  sonnet_prep: disabled via SONNET_PREP_DISABLED=1")
        return

    task = find_next_opus_task()
    if not task:
        print("  sonnet_prep: no pending [opus] tasks")
        return

    print(f"  sonnet_prep: next opus task = {task['id']} (p{task.get('priority', '?')})")
    try:
        prewarm_task(task)
    except Exception as e:
        print(f"  sonnet_prep: prewarm_task failed: {e}", file=sys.stderr)

    print(f"[sonnet_prep] done")


if __name__ == "__main__":
    main()
