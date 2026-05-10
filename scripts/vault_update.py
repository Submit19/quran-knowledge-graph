#!/usr/bin/env python
"""
vault_update.py — keep the QKG Obsidian vault in sync with project activity.

Called by the cron orchestrator at the end of each tick (alongside state_snapshot.py).
Idempotent — running it again with no new commits is a no-op.

What it does each invocation:
1. **Daily note** — append a one-line entry per new commit to `daily/YYYY-MM-DD.md`
   (creating the file if missing). Captures the day's git activity.
2. **Research notes** — for any new tick that produced a `data/research_<topic>.md`
   file, create a corresponding stub vault note in `research/` if one doesn't exist.
3. **Tick row in CURRENT STATE** — covered by `state_snapshot.py` already.

The vault is at `QKG Obsidian/` in the repo root.

Designed to be cheap (no Claude API calls), deterministic, and safe to re-run.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "QKG Obsidian"
DAILY = VAULT / "daily"
RESEARCH = VAULT / "research"
SESSIONS = VAULT / "sessions"

NOW_UTC = datetime.now(timezone.utc)
TODAY_ISO = NOW_UTC.strftime("%Y-%m-%d")
TODAY_HM = NOW_UTC.strftime("%H:%M")

STATE_FILE = ROOT / ".vault_update_state.json"


# ── helpers ─────────────────────────────────────────────────────────────────

def git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode("utf-8", errors="replace").strip()
    except Exception:
        return ""


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(s: dict):
    STATE_FILE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:80] or "untitled"


# ── 1. Daily note: append new commits since last run ─────────────────────────

def update_daily_note():
    if not VAULT.exists():
        return
    DAILY.mkdir(exist_ok=True)
    note_path = DAILY / f"{TODAY_ISO}.md"

    state = load_state()
    last_sha = state.get("last_seen_commit", "")

    # Get commits since last run (or last 50 if no state)
    if last_sha:
        log = git("log", f"{last_sha}..HEAD", "--pretty=format:%H|%s|%ci")
    else:
        log = git("log", "-50", "--pretty=format:%H|%s|%ci")

    if not log.strip():
        return  # nothing new

    new_commits = []
    for line in log.splitlines():
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        sha, subject, ts = parts
        new_commits.append((sha, subject, ts))

    if not new_commits:
        return

    # Filter to today's commits only for the daily note
    todays = [c for c in new_commits if c[2].startswith(TODAY_ISO)]

    # Bootstrap the daily note if missing
    if not note_path.exists():
        note_path.write_text(
            f"---\n"
            f"date: {TODAY_ISO}\n"
            f"type: daily\n"
            f"tags: [daily]\n"
            f"---\n\n"
            f"# {TODAY_ISO}\n\n"
            f"_Auto-maintained by `scripts/vault_update.py`. Append your own reflections below the commit log._\n\n"
            f"## Commits today\n\n",
            encoding="utf-8",
        )

    # Append today's new commits to the commit log section
    if todays:
        existing = note_path.read_text(encoding="utf-8")
        addendum = "\n".join(
            f"- `{sha[:7]}` {subj}" for sha, subj, _ in todays
        ) + "\n"
        # Avoid duplicating commits we've already logged
        seen_shas = set(re.findall(r"`([a-f0-9]{7})`", existing))
        addendum_lines = [
            line for line in addendum.splitlines()
            if not any(sha in line for sha in seen_shas)
        ]
        if addendum_lines:
            with note_path.open("a", encoding="utf-8") as f:
                f.write("\n".join(addendum_lines) + "\n")

    # Update state with the latest sha
    state["last_seen_commit"] = new_commits[0][0]
    save_state(state)


# ── 2. Research stubs: ensure each data/research_<topic>.md has a vault note ─

def _existing_sources_in_research() -> set[str]:
    """Read frontmatter of every research/*.md and collect the `source:` paths
    they reference. Used to avoid creating duplicate stubs when a real note
    (subagent-written, hand-written) already exists for that source."""
    sources: set[str] = set()
    if not RESEARCH.exists():
        return sources
    for md in RESEARCH.glob("*.md"):
        try:
            head = md.read_text(encoding="utf-8")
        except Exception:
            continue
        # Look for `source: <path>` in the first ~20 lines
        for line in head.splitlines()[:20]:
            m = re.match(r"\s*source:\s*(.+)\s*$", line, re.I)
            if m:
                # Normalize: lowercase, strip quotes/backticks, drop "repo://" prefix
                val = m.group(1).strip().strip("`'\"")
                val = val.removeprefix("repo://").lower()
                sources.add(val)
                break
    return sources


def update_research_stubs():
    if not VAULT.exists():
        return
    RESEARCH.mkdir(exist_ok=True)

    existing_sources = _existing_sources_in_research()

    # Find research deliverable files
    candidates = list((ROOT / "data").glob("research_*.md")) + \
                 list((ROOT / "data" / "research_neo4j_crawl").glob("06*_*.md")) + \
                 list((ROOT / "data" / "research_neo4j_crawl").glob("0[1-5]*_*.md"))

    for src in candidates:
        # Skip raw transcripts
        if src.name.startswith("yt_"):
            continue

        # Skip if a vault note already references this source (don't double-stub)
        relpath_lower = src.relative_to(ROOT).as_posix().lower()
        if relpath_lower in existing_sources:
            continue

        slug = slugify(src.stem.replace("research_", "").replace("0", "", 1))
        note_path = RESEARCH / f"{slug}.md"

        if note_path.exists():
            continue  # already have a stub

        try:
            head = src.read_text(encoding="utf-8").splitlines()[:6]
        except Exception:
            head = []

        title = src.stem.replace("_", " ").replace("-", " ").title()

        relpath = src.relative_to(ROOT).as_posix()
        note_path.write_text(
            f"---\n"
            f"type: research\n"
            f"status: open\n"
            f"date_added: {TODAY_ISO}\n"
            f"source: {relpath}\n"
            f"tags: [research, auto-stub]\n"
            f"---\n\n"
            f"# {title}\n\n"
            f"_Stub auto-created by `vault_update.py`. Source artefact: `repo://{relpath}`._\n\n"
            f"## Source preamble\n\n"
            "```\n" + "\n".join(head) + "\n```\n\n"
            f"## Notes\n\n"
            f"_Distill the key findings from the source file here. Replace this stub when you do._\n\n"
            f"## Cross-references\n"
            f"- Source: `repo://{relpath}`\n"
            f"- [[../MOC]]\n",
            encoding="utf-8",
        )


# ── 3. CURRENT STATE mirror is handled by state_snapshot.py — nothing to do ──


def main():
    if not VAULT.exists():
        print(f"vault_update: vault not found at {VAULT.relative_to(ROOT)}; skipping",
              file=sys.stderr)
        return

    update_daily_note()
    update_research_stubs()
    print(f"vault_update: ok ({TODAY_ISO})")


if __name__ == "__main__":
    main()
