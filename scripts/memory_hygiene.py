#!/usr/bin/env python
"""memory_hygiene.py — keep the 5-tier memory stack current.

Called from the MAINT tick procedure (every 6th cron fire). Does four
failure-safe jobs:

  1. promote_codebase_patterns — scan ralph_log.md for `PATTERN:` lines
     in tick notes, dedupe, and append durable ones to the Codebase
     Patterns block at the top.

  2. session_log_rolling_entry — if SESSION_LOG.md's top entry is older
     than 24h AND >5 commits have landed since, ask Haiku to write a
     rolling interim entry summarizing what shipped + what's queued.

  3. refresh_moc — auto-regenerate the "Backfilled content" section of
     QKG Obsidian/MOC.md from the current vault file list. Catches new
     ADRs / architecture / research notes that don't yet have MOC links.

  4. arch_drift_spotcheck (every 4th MAINT tick, ~every day) — spawn
     Haiku on 2 random architecture/ notes; compare to the underlying
     source files; flag substantive drift to data/memory_drift.md.

Idempotent. Disable individual jobs with env vars:
  MEMORY_HYGIENE_DISABLED=1  — skip everything
  MEMORY_HYGIENE_SKIP_HAIKU=1  — skip Haiku calls (offline mode)
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
    import requests
except ImportError as e:
    print(f"[memory_hygiene] missing dependency: {e} — skipping", file=sys.stderr)
    sys.exit(0)

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "QKG Obsidian"
LOG = ROOT / "ralph_log.md"
SESSION = ROOT / "SESSION_LOG.md"
DRIFT = ROOT / "data" / "memory_drift.md"
MOC = VAULT / "MOC.md"
STATE = ROOT / "ralph_state.json"

HAIKU_MODEL = os.getenv("HAIKU_MODEL", "claude-haiku-4-5")


def load_env():
    env = ROOT / ".env"
    if not env.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(env, override=True)
    except ImportError:
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                v = v.strip()
                if v:
                    os.environ[k.strip()] = v


def git(*args):
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def haiku_call(prompt: str, max_tokens: int = 1500) -> str | None:
    """Single Haiku API call. Returns text or None on failure."""
    if os.getenv("MEMORY_HYGIENE_SKIP_HAIKU") == "1":
        return None
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
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
                "model": HAIKU_MODEL,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=45,
        )
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception as e:
        print(f"  haiku call failed: {e}", file=sys.stderr)
        return None


# ── Job 1: Codebase Patterns promotion ──────────────────────────────────────

def promote_codebase_patterns():
    """Scan ralph_log.md for PATTERN: lines in recent tick rows.
    Dedupe + append unique ones to the <!-- PATTERNS:START --> block."""
    if not LOG.exists():
        return
    txt = LOG.read_text(encoding="utf-8")

    # Extract block region
    start = txt.find("<!-- PATTERNS:START -->")
    end = txt.find("<!-- PATTERNS:END -->")
    if start < 0 or end < 0 or end < start:
        return

    block = txt[start + len("<!-- PATTERNS:START -->"):end].strip()
    existing_patterns = {
        line.strip().lstrip("-").strip()
        for line in block.splitlines()
        if line.strip().startswith("-")
    }

    # Find new PATTERN: lines in the rest of the log
    rest = txt[end:]
    found = set()
    for m in re.finditer(r"PATTERN:\s*(.+?)(?:\n|$)", rest):
        p = m.group(1).strip().rstrip("|").strip()
        if p and len(p) > 8:
            found.add(p)

    new = found - existing_patterns
    if not new:
        return

    new_block_lines = []
    if block:
        new_block_lines.append(block)
        new_block_lines.append("")
    for p in sorted(new):
        new_block_lines.append(f"- {p}")
    new_block = "\n".join(new_block_lines)

    txt = (
        txt[: start + len("<!-- PATTERNS:START -->")]
        + "\n"
        + new_block
        + "\n"
        + txt[end:]
    )
    LOG.write_text(txt, encoding="utf-8")
    print(f"  promoted {len(new)} new patterns to Codebase Patterns block")


# ── Job 2: SESSION_LOG rolling interim entry ────────────────────────────────

def session_log_rolling_entry():
    """If SESSION_LOG hasn't been updated in 24h AND >5 commits landed,
    auto-generate a rolling interim entry via Haiku."""
    if not SESSION.exists():
        return

    txt = SESSION.read_text(encoding="utf-8")
    # Find top entry timestamp — assume first "## YYYY-MM-DD" heading
    m = re.search(r"^##\s+(\d{4}-\d{2}-\d{2})\b", txt, re.MULTILINE)
    if not m:
        return
    try:
        top_date = datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return

    now = datetime.now(timezone.utc)
    if now - top_date < timedelta(hours=24):
        return

    # Check if there's been significant commit activity since
    commits = git("log", "--oneline", f"--since={top_date.isoformat()}")
    n_commits = len([l for l in commits.splitlines() if l.strip()])
    if n_commits < 5:
        return

    today = now.strftime("%Y-%m-%d")
    # Avoid duplicate auto-entries on the same day
    if f"## {today}" in txt[:2000]:
        return

    # Ask Haiku to summarize commits since top_date
    last_commits = git("log", "--oneline", "-50", f"--since={top_date.isoformat()}")
    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    done_recent = state.get("done_task_ids", [])[-15:]

    prompt = f"""Write a SESSION_LOG.md interim entry for {today}. The format is the same as existing entries in SESSION_LOG.md.

This is a ROLLING auto-generated entry (not a human session end) — make that clear in the title with "(rolling)".

# Commits since {top_date.date()}

{last_commits}

# Recent tasks completed (last 15)

{', '.join(done_recent)}

# Output format

```
## {today} · Auto (rolling) · "<2-5 word summary of biggest themes>"

### Shipped since last entry
- bullets, 1 per major commit or task; ~10-15 bullets max
- group by theme (loop infra / memory infra / research / IMPL wins)

### Queued
- 3-5 bullets on what's next

### Tip for next session
One line.
```

Output ONLY the markdown block above, ready to insert at the top of the entries (after the `---` separator). 250 words max."""

    body = haiku_call(prompt, max_tokens=2000)
    if not body:
        return

    # Clean body — extract the first ## block
    body = body.strip()
    if body.startswith("```"):
        # strip ``` fences
        body = re.sub(r"^```\w*\n?", "", body)
        body = re.sub(r"\n?```\s*$", "", body)
    if not body.startswith("##"):
        return  # bail if format is wrong

    # Insert at the top, just after the first --- separator
    separator = "---\n"
    idx = txt.find(separator)
    if idx < 0:
        return
    insert_at = idx + len(separator)
    txt = txt[:insert_at] + "\n" + body.strip() + "\n\n---\n" + txt[insert_at:]
    SESSION.write_text(txt, encoding="utf-8")
    print(f"  inserted rolling SESSION_LOG entry for {today}")


# ── Job 3: MOC refresh ──────────────────────────────────────────────────────

def refresh_moc():
    """Regenerate the 'Backfilled content' section of MOC.md from current
    vault file inventory. Keeps cross-references current as new ADRs /
    architecture notes / research notes land."""
    if not MOC.exists():
        return
    txt = MOC.read_text(encoding="utf-8")

    # Locate the Backfilled content section (between "## Backfilled" heading
    # and the next "## " or "## Dataview")
    start_marker = "## Backfilled content"
    end_marker_candidates = ["## Dataview", "## Top-level"]

    start = txt.find(start_marker)
    if start < 0:
        return

    # Find next "## " after start_marker
    rest = txt[start + len(start_marker):]
    next_section = len(rest)
    for cand in end_marker_candidates:
        idx = rest.find(cand)
        if idx >= 0 and idx < next_section:
            next_section = idx

    # Inventory vault folders
    sections = []
    sections.append(start_marker + " (auto-refreshed by memory_hygiene.py)")
    sections.append("")

    for folder, heading in [
        ("decisions", "Decisions (ADRs)"),
        ("architecture", "Architecture"),
        ("research", "Research"),
        ("sessions", "Sessions / milestones"),
    ]:
        d = VAULT / folder
        if not d.exists():
            continue
        files = sorted(p.name for p in d.glob("*.md"))
        if not files:
            continue
        sections.append(f"### {heading} ({len(files)})")
        for fname in files:
            stem = fname[:-3]
            sections.append(f"- [[{folder}/{stem}]]")
        sections.append("")

    new_section = "\n".join(sections)
    new_txt = txt[:start] + new_section + "\n" + txt[start + len(start_marker) + next_section:]
    if new_txt != txt:
        MOC.write_text(new_txt, encoding="utf-8")
        print(f"  refreshed MOC.md backfilled-content section")


# ── Job 4: architecture drift spot-check (every 4th MAINT tick) ─────────────

def arch_drift_spotcheck():
    """Sample 2 random architecture/ notes; compare to underlying source files;
    flag substantive drift via Haiku."""
    if not STATE.exists():
        return
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return
    tc = int(state.get("tick_count", 0))
    # Only run every 4th MAINT tick (every 24th overall tick)
    if tc == 0 or tc % 24 != 0:
        return

    arch_dir = VAULT / "architecture"
    if not arch_dir.exists():
        return
    candidates = sorted(arch_dir.glob("*.md"))
    if not candidates:
        return

    # Pick 2 deterministically based on tick_count so we eventually cover all
    import random
    random.seed(tc)
    sample = random.sample(candidates, min(2, len(candidates)))

    findings = []
    for note in sample:
        # Identify referenced source files from the note (repo://path mentions)
        body = note.read_text(encoding="utf-8")
        refs = re.findall(r"repo://([^\s)`]+)", body)
        if not refs:
            continue
        src_paths = []
        for r in refs[:3]:
            p = ROOT / r
            if p.exists() and p.is_file():
                src_paths.append(p)
        if not src_paths:
            continue

        src_content = "\n\n".join(
            f"## {p.relative_to(ROOT)}\n```\n{p.read_text(encoding='utf-8')[:4000]}\n```"
            for p in src_paths
        )

        prompt = f"""You are auditing whether an architecture note in our docs vault still matches the underlying source code.

# Architecture note (from QKG Obsidian/architecture/{note.name})

{body[:6000]}

# Current source file(s) referenced by the note

{src_content[:12000]}

# Your job

Flag SUBSTANTIVE drift. Examples:
- The note claims a function/class exists that no longer does
- The note describes a schema field that has been renamed or removed
- The note describes a flow / pattern that the code no longer implements

Ignore:
- Surface-level wording differences
- Updated examples
- Minor refactoring (rename of internal variables, etc.)

Output strict format:
DRIFT: yes | no
SEVERITY: low | medium | high
DETAILS: <one short paragraph, max 80 words, only if DRIFT=yes>

Output only those three lines."""
        result = haiku_call(prompt, max_tokens=400)
        if not result:
            continue
        if "DRIFT: yes" in result:
            findings.append(f"### `{note.name}`\n\n{result.strip()}\n")

    if findings:
        out = [
            f"# Architecture drift findings — {datetime.now(timezone.utc).isoformat()[:16]}Z",
            "",
            "_Auto-generated by `scripts/memory_hygiene.py` (every 24th tick)._",
            "_Reviewed notes need operator attention; flagged drift means the note "
            "may mislead future readers if not refreshed._",
            "",
        ]
        out.extend(findings)
        DRIFT.write_text("\n".join(out), encoding="utf-8")
        print(f"  arch drift: {len(findings)} notes flagged → {DRIFT.relative_to(ROOT)}")
    elif DRIFT.exists():
        # No current drift; remove stale findings file
        DRIFT.unlink()


# ── main ────────────────────────────────────────────────────────────────────

def main():
    load_env()
    if os.getenv("MEMORY_HYGIENE_DISABLED") == "1":
        print("[memory_hygiene] disabled")
        return
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[memory_hygiene] starting at {ts}")
    for fn in (
        promote_codebase_patterns,
        session_log_rolling_entry,
        refresh_moc,
        arch_drift_spotcheck,
    ):
        try:
            fn()
            print(f"  [memory_hygiene] {fn.__name__} ok")
        except Exception as e:
            print(f"  [memory_hygiene] {fn.__name__} FAILED: {e}", file=sys.stderr)
    print(f"[memory_hygiene] done")


if __name__ == "__main__":
    main()
