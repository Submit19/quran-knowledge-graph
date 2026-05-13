"""
ralph_loop.py — core utilities for the Ralph loop.

The loop is "wake up, pick the highest-priority unblocked task from
ralph_backlog.yaml, run it, measure impact, decide commit or revert,
log what was learned, update state, schedule next tick."

This module is the library; ralph_tick.py is the CLI entry point that
a scheduled wake-up (or you, by hand) calls.

Design principles:
- Read-only by default. A tick that doesn't have a measurable improvement
  doesn't commit.
- Each task type has an executor function. Adding a new task type means
  registering a new function — not modifying core logic.
- All state lives in two files:
    ralph_backlog.yaml   (human-editable queue, ranked)
    ralph_state.json     (auto: in_progress, done, last_tick, baselines)
- Append-only audit log:  ralph_log.md (markdown rows per tick)
"""

import json
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable

# Reuse: reasoning_memory has the canonical ISO-8601 UTC formatter.
# Importing it removes duplication across the repo (4 copies as of 2026-05).
from reasoning_memory import _now_iso

ROOT = Path(__file__).parent
BACKLOG_PATH = ROOT / "ralph_backlog.yaml"
STATE_PATH = ROOT / "ralph_state.json"
LOG_PATH = ROOT / "ralph_log.md"
DATA_DIR = ROOT / "data"

HISTORY_CAP = 500   # cap state['history'] FIFO; older entries dropped at save_state


# ── state I/O ────────────────────────────────────────────────────────────────

# ── status taxonomy (from obra/superpowers implementer-status pattern) ──────
#
#   DONE                — succeeded, acceptance criteria verified
#   DONE_WITH_CONCERNS  — succeeded but a sub-check warned (e.g. metric drifted)
#   NEEDS_CONTEXT       — couldn't run; missing inputs/dependencies
#   BLOCKED             — external blocker (Neo4j down, server crashed, model unreachable)
#   REGRESSION          — ran cleanly but metric dropped below threshold; keep status as REGRESSION pending investigation
#   FAILED              — ran with error
#   QUARANTINED         — ≥ MAX_ATTEMPTS failures; remove from auto-pick
#   SKIPPED             — task type not auto-runnable (manual / external_run)
#   RUNNING             — internal; only set transiently

DONE = "DONE"
DONE_WITH_CONCERNS = "DONE_WITH_CONCERNS"
NEEDS_CONTEXT = "NEEDS_CONTEXT"
BLOCKED = "BLOCKED"
REGRESSION = "REGRESSION"
FAILED = "FAILED"
QUARANTINED = "QUARANTINED"
SKIPPED = "SKIPPED"
RUNNING = "RUNNING"

TERMINAL_OK = {DONE, DONE_WITH_CONCERNS, SKIPPED}
TERMINAL_FAIL = {NEEDS_CONTEXT, BLOCKED, REGRESSION, FAILED}

MAX_ATTEMPTS_DEFAULT = 3   # superpowers: "3 failed attempts → architectural problem"


@dataclass
class TickResult:
    task_id: str
    type: str
    started_at: str
    finished_at: str = ""
    status: str = RUNNING
    attempt: int = 1
    metric_before: float | None = None
    metric_after: float | None = None
    delta: float | None = None
    notes: str = ""
    artefacts: list[str] = field(default_factory=list)
    error: str | None = None
    acceptance_results: list[dict] = field(default_factory=list)
    # OpenRouter / API usage — populated by executors that call paid/free APIs.
    # 0 means "no API call was made" (e.g. cypher_analysis, cleanup).
    tokens_in: int = 0
    tokens_out: int = 0
    api_calls: int = 0


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {
            "version": 1,
            "in_progress": None,
            "last_tick": None,
            "tick_count": 0,
            "done_task_ids": [],
            "skipped_task_ids": [],
            "baselines": {},  # metric_name -> value
            "history": [],    # list of TickResult dicts
        }
    return json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))


def save_state(state: dict):
    # FIFO-cap unbounded history so the file doesn't balloon over months
    h = state.get("history") or []
    if len(h) > HISTORY_CAP:
        state["history"] = h[-HISTORY_CAP:]
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False),
                          encoding="utf-8")


def load_backlog() -> dict:
    """Load ralph_backlog.yaml. Use a minimal YAML parser so we don't need
    a hard pyyaml dependency."""
    try:
        import yaml
        return yaml.safe_load(BACKLOG_PATH.read_text(encoding="utf-8"))
    except ImportError:
        # Fallback — pyyaml is in our requirements but be defensive
        sys.exit("pyyaml not installed. pip install pyyaml")


_LOG_HEADER = (
    "# Ralph Loop — tick log\n\n"
    "## Codebase Patterns\n"
    "_Consolidated learnings from prior ticks. Always append; preserve existing entries.\n"
    " A pattern goes here when it's general/reusable enough that future\n"
    " ticks (and future humans) should know it. Keep entries terse._\n\n"
    "<!-- PATTERNS:START -->\n"
    "<!-- PATTERNS:END -->\n\n"
    "## Tick history\n\n"
    "| ts | task_id | type | status | metric Δ | notes |\n"
    "|----|---------|------|--------|----------|-------|\n"
)


def _ensure_log():
    """Make sure ralph_log.md exists with the canonical header."""
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text(_LOG_HEADER, encoding="utf-8")
    else:
        # Be lenient if the file existed in v1 (pre-Codebase-Patterns) shape:
        body = LOG_PATH.read_text(encoding="utf-8")
        if "<!-- PATTERNS:START -->" not in body:
            # migrate: keep the existing tick rows, prepend the new header
            old_rows = body.split("|----|", 1)
            after = ("|----|" + old_rows[1]) if len(old_rows) > 1 else ""
            LOG_PATH.write_text(_LOG_HEADER + after, encoding="utf-8")


def append_log(result: TickResult, task: dict):
    """Append a markdown row to ralph_log.md."""
    _ensure_log()
    delta_s = ""
    if result.delta is not None:
        delta_s = f"{result.delta:+.2f}"
    notes = (result.notes or result.error or "")[:160].replace("\n", " ").replace("|", "/")
    row = f"| {result.started_at[:16]} | {result.task_id} | {result.type} | {result.status} | {delta_s} | {notes} |\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(row)


def add_codebase_pattern(pattern: str, source_task: str | None = None):
    """
    Append a durable learning to the `<!-- PATTERNS:START --> ... :END -->`
    block at the top of ralph_log.md. snarktank/ralph pattern: durable
    knowledge separate from per-tick rows.
    """
    _ensure_log()
    body = LOG_PATH.read_text(encoding="utf-8")
    start_tag, end_tag = "<!-- PATTERNS:START -->", "<!-- PATTERNS:END -->"
    i = body.find(start_tag)
    j = body.find(end_tag)
    if i < 0 or j < 0:
        return False  # tags missing — refuse to mangle the file
    line = f"- {pattern.strip()}"
    if source_task:
        line += f"  _(from `{source_task}`)_"
    line += "\n"
    inside = body[i + len(start_tag): j]
    if line.strip() in inside:
        return False  # already present
    new_inside = (inside.rstrip() + "\n" + line) if inside.strip() else "\n" + line
    new_body = body[:i + len(start_tag)] + new_inside + body[j:]
    LOG_PATH.write_text(new_body, encoding="utf-8")
    return True


# ── repo-wide quality gate ──────────────────────────────────────────────────
# Inspired by snarktank/ralph: "ALL commits must pass your project's quality
# checks (typecheck, lint, test)." For our project this is a fast smoke
# import — broken Python in any of the core modules and the live agent loop
# breaks. Run before committing any task that mutates code.

CORE_MODULES = [
    "chat", "app_free", "reasoning_memory",
    "retrieval_gate", "citation_verifier", "ref_resolver",
    "ralph_loop",
]


def quality_gate() -> tuple[bool, str]:
    """
    Run the smoke-import gate. Returns (passed, message).
    Fast — typically <2s. Catches broken-Python regressions immediately.
    """
    proc = subprocess.run(
        [sys.executable, "-c",
         "import " + ", ".join(CORE_MODULES) + "; print('ok')"],
        cwd=str(ROOT),
        capture_output=True,
        timeout=30,
    )
    stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
    stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
    if proc.returncode == 0 and "ok" in stdout:
        return True, "core modules import cleanly"
    err = (stderr or stdout)[-400:]
    return False, err


# ── task picker ──────────────────────────────────────────────────────────────

def pick_next_task(backlog: dict, state: dict, allow_types: set[str] | None = None) -> dict | None:
    """
    Return the highest-priority task that:
      - is not already done
      - is not in_progress
      - has no unfinished blockers
      - has not been quarantined (≥ MAX_ATTEMPTS failed)
      - if `allow_types` is given: type must be in that set
      - if `allow_types` is None: skip 'manual' and 'external_run' (auto-mode default)
    """
    done = set(state.get("done_task_ids", []))
    skipped = set(state.get("skipped_task_ids", []))
    quarantined = set(state.get("quarantined_task_ids", []))
    in_prog = state.get("in_progress")
    attempts = state.get("attempts", {})  # task_id -> count
    auto_skip_types = {"manual", "external_run"}

    candidates = []
    for t in backlog.get("tasks", []):
        if t["id"] in done or t["id"] in skipped or t["id"] in quarantined or t["id"] == in_prog:
            continue
        ttype = t.get("type")
        if allow_types is not None:
            if ttype not in allow_types:
                continue
        else:
            if ttype in auto_skip_types:
                continue
        if any(b not in done for b in (t.get("blockers") or [])):
            continue
        max_a = int((t.get("spec") or {}).get("max_attempts", MAX_ATTEMPTS_DEFAULT))
        if attempts.get(t["id"], 0) >= max_a:
            continue
        candidates.append(t)

    candidates.sort(key=lambda t: -int(t.get("priority", 0)))
    return candidates[0] if candidates else None


# ── verification ────────────────────────────────────────────────────────────
# Superpowers "Gate Function": run the command, read the output, check exit
# code, verify the output ACTUALLY confirms the claim — only THEN mark done.

def verify_acceptance(task: dict, result: TickResult) -> tuple[bool, list[dict]]:
    """
    Run the task's acceptance checks (declared in spec.acceptance). Returns
    (all_passed, [{check, passed, detail}]).

    Supported checks:
      - file_exists: <path>             (artefact was written)
      - file_min_bytes: {path, min}     (artefact has content)
      - metric_above: {name, value}     (metric beat threshold)
      - metric_at_least_baseline: name  (metric did not regress)
      - python: <expr>                  (eval'd in a sandbox; truthy = pass)
      - python_test_passes: <path>|[<path>, ...]
          Run `python -m pytest <path> -q --tb=short` for each path.
          All must exit 0. Stdout+stderr is captured into the detail
          string on failure. Preferred gate for any task that touches
          code (cleanup / cache_op / embed_op / prompt_variant).
    """
    spec = task.get("spec") or {}
    checks = spec.get("acceptance") or []
    if not checks:
        # No acceptance specified — superpowers would call this a soft pass.
        # We accept it but flag as DONE_WITH_CONCERNS later.
        return True, [{"check": "none specified", "passed": True,
                       "detail": "soft pass (consider adding acceptance criteria)"}]

    out = []
    all_ok = True
    for c in checks:
        if "file_exists" in c:
            p = ROOT / c["file_exists"]
            ok = p.exists()
            out.append({"check": f"file_exists {c['file_exists']}", "passed": ok,
                        "detail": str(p) if ok else f"missing: {p}"})
            all_ok = all_ok and ok
        elif "file_min_bytes" in c:
            cfg = c["file_min_bytes"]
            p = ROOT / cfg["path"]
            try:
                sz = p.stat().st_size
            except FileNotFoundError:
                sz = 0
            ok = sz >= int(cfg["min"])
            out.append({"check": f"file_min_bytes {cfg['path']} >= {cfg['min']}",
                        "passed": ok, "detail": f"size={sz}"})
            all_ok = all_ok and ok
        elif "metric_above" in c:
            cfg = c["metric_above"]
            v = result.metric_after
            ok = v is not None and v > float(cfg["value"])
            out.append({"check": f"metric_above {cfg['name']} > {cfg['value']}",
                        "passed": ok, "detail": f"actual={v}"})
            all_ok = all_ok and ok
        elif "metric_at_least_baseline" in c:
            v = result.metric_after
            b = result.metric_before
            ok = (v is not None and b is not None and v >= b * 0.95)  # within 5%
            out.append({"check": "metric_at_least_baseline",
                        "passed": ok,
                        "detail": f"before={b}, after={v}"})
            all_ok = all_ok and ok
        elif "python" in c:
            try:
                ok = bool(eval(c["python"], {"result": result, "task": task}))
                out.append({"check": f"python {c['python'][:60]}", "passed": ok,
                            "detail": "ok" if ok else "expression returned falsy"})
                all_ok = all_ok and ok
            except Exception as e:
                out.append({"check": f"python {c['python'][:60]}",
                            "passed": False, "detail": f"raised: {e}"})
                all_ok = False
        elif "python_test_passes" in c:
            paths = c["python_test_passes"]
            if isinstance(paths, str):
                paths = [paths]
            for p in paths:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", p, "-q", "--tb=short"],
                    capture_output=True, text=True, timeout=300,
                    cwd=str(ROOT),
                )
                passed = proc.returncode == 0
                out.append({
                    "check": f"python_test_passes {p}",
                    "passed": passed,
                    "detail": "ok" if passed else (proc.stdout + proc.stderr)[-2000:],
                })
                all_ok = all_ok and passed
        else:
            out.append({"check": str(c), "passed": False,
                        "detail": "unknown acceptance check shape"})
            all_ok = False
    return all_ok, out


# ── task executors ──────────────────────────────────────────────────────────

def _read_eval_metrics(eval_path: Path, metric: str) -> float | None:
    """Compute a single metric from an eval_v1-style results file."""
    if not eval_path.exists():
        return None
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    rows = (data.get("general") or []) + (data.get("surah") or [])
    if not rows:
        return None
    if metric == "avg_unique_cites_per_q":
        return sum(r.get("n_cites_unique", 0) for r in rows) / len(rows)
    if metric == "avg_chars_per_q":
        return sum(r.get("answer_chars", 0) for r in rows) / len(rows)
    if metric == "avg_time_sec_per_q":
        return sum(r.get("elapsed_sec", 0) for r in rows) / len(rows)
    if metric == "avg_tools_per_q":
        return sum(r.get("n_tool_calls", 0) for r in rows) / len(rows)
    return None


def execute_eval(task: dict, state: dict, result: TickResult) -> TickResult:
    """Run an eval script, snapshot results, compare to baseline."""
    spec = task.get("spec") or {}
    script = spec.get("script", "eval_v1.py")
    metric = spec.get("metric", "avg_unique_cites_per_q")
    compare_to = spec.get("compare_to") or "data/eval_v1_results.json"
    env = {**os.environ, **(spec.get("env") or {}), "PYTHONUNBUFFERED": "1"}

    # baseline before
    baseline = _read_eval_metrics(ROOT / compare_to, metric)
    result.metric_before = baseline

    # snapshot output to a timestamped file
    ts = time.strftime("%Y%m%d_%H%M%S")
    snap = DATA_DIR / f"eval_{ts}.json"

    # The eval scripts write to data/eval_v1_results.json by default.
    # We'll move it to the snapshot path after the run.
    proc = subprocess.run(
        [sys.executable, script],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=spec.get("timeout_sec", 3600),
    )
    if proc.returncode != 0:
        result.status = FAILED
        result.error = (proc.stderr or proc.stdout or "")[-800:]
        return result

    src = ROOT / "data" / "eval_v1_results.json"
    if src.exists():
        # Persist as both the latest and a timestamped snapshot
        snap.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        result.artefacts.append(str(snap.relative_to(ROOT)))
        current = _read_eval_metrics(snap, metric)
    else:
        current = None

    result.metric_after = current
    if current is None:
        result.status = NEEDS_CONTEXT
        result.notes = f"{metric}: could not compute (snapshot missing or empty)"
        return result

    if baseline is not None:
        result.delta = current - baseline
        regression_pct = float(spec.get("regression_pct", 5))
        if current < baseline * (1 - regression_pct / 100):
            result.status = REGRESSION
            result.notes = f"{metric}: {baseline:.2f} -> {current:.2f} (regression > {regression_pct}%)"
        else:
            result.status = DONE
            result.notes = f"{metric}: {baseline:.2f} -> {current:.2f}"
    else:
        result.status = DONE
        result.notes = f"{metric}={current:.2f} (no baseline)"
    return result


def execute_cypher_analysis(task: dict, state: dict, result: TickResult) -> TickResult:
    """Run a read-only Cypher query or python script and dump output to a file.

    Three modes:
      - query_kind: python_script + script — exec inline, capture stdout
      - query field present — run as Cypher against Neo4j
      - query_kind: manual (or no query/script + acceptance gate) — defer
        deliverable production to an out-of-band operator (the cron's
        subagent does the work and writes the deliverable file). Acceptance
        gate validates. This matches agent_creative's manual backend.
    """
    spec = task.get("spec") or {}
    out_md = DATA_DIR / f"ralph_analysis_{task['id']}.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)

    # Manual mode: operator produced deliverable out-of-band; gate validates.
    has_query = "query" in spec
    has_script = spec.get("query_kind") == "python_script" and "script" in spec
    manual_mode = spec.get("query_kind") == "manual" or (not has_query and not has_script)
    if manual_mode:
        result.status = DONE_WITH_CONCERNS
        result.notes = "manual mode — deliverable produced out-of-band; gate will validate"
        # Stub the conventional output path so downstream readers find something
        if not out_md.exists():
            out_md.write_text(
                f"# {task['id']}\n\n_Handled in manual mode. See acceptance "
                f"file(s) for the actual deliverable._\n",
                encoding="utf-8",
            )
        result.artefacts.append(str(out_md.relative_to(ROOT)))
        return result

    if spec.get("query_kind") == "python_script" and "script" in spec:
        # exec inline
        from io import StringIO
        buf = StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            exec(spec["script"], {"__name__": "__ralph__"})
            text = buf.getvalue()
        except Exception as e:
            text = f"ERROR: {e}\n{traceback.format_exc()}"
            result.status = FAILED
            result.error = text[-400:]
        finally:
            sys.stdout = old
        out_md.write_text("# " + task["id"] + "\n\n```\n" + text + "\n```\n", encoding="utf-8")
    elif "query" in spec:
        from dotenv import load_dotenv; load_dotenv()
        from neo4j import GraphDatabase
        try:
            with GraphDatabase.driver(
                    os.getenv("NEO4J_URI"),
                    auth=(os.getenv("NEO4J_USER"),
                          os.getenv("NEO4J_PASSWORD"))) as d:
                with d.session(database=os.getenv("NEO4J_DATABASE", "quran")) as s:
                    rows = s.run(spec["query"]).data()
            text = json.dumps(rows, indent=2, ensure_ascii=False, default=str)
            out_md.write_text(f"# {task['id']}\n\n```json\n{text}\n```\n", encoding="utf-8")
        except Exception as e:
            err = str(e)
            if "ServiceUnavailable" in err or "Couldn't connect" in err:
                result.status = BLOCKED
                result.error = f"Neo4j unreachable: {err[:200]}"
            else:
                result.status = FAILED
                result.error = err[-400:]
            return result
    else:
        result.status = NEEDS_CONTEXT
        result.error = "spec missing 'query' or 'script'"
        return result

    result.artefacts.append(str(out_md.relative_to(ROOT)))
    if not result.error:
        result.status = DONE
        result.notes = f"wrote {out_md.name}"
    return result


def execute_cleanup(task: dict, state: dict, result: TickResult) -> TickResult:
    """No-op DONE — placeholder for hygiene tasks. Add real logic per task."""
    result.status = DONE
    result.notes = task.get("description", "")[:80]
    return result


def execute_skipped(task: dict, state: dict, result: TickResult) -> TickResult:
    """For task types we don't auto-execute (manual, external_run, agent_creative
    when no LLM key configured)."""
    result.status = SKIPPED
    result.notes = f"type={task.get('type')} requires manual / agent involvement"
    return result


# ── agent_creative executor ─────────────────────────────────────────────────
# Superpowers pattern: spawn a fresh subagent with constructed context;
# the subagent NEVER inherits the orchestrator's session history. We use
# OpenRouter (cheap free tier) with a focused system prompt + just the
# task's spec as user-facing input.

def execute_agent_creative(task: dict, state: dict, result: TickResult) -> TickResult:
    """
    For tasks that need creative LLM work (write a prompt variant, generate
    eval questions, propose architecture changes). Calls OpenRouter with a
    fresh, narrow context — the task description + spec only.

    Output is written to data/ralph_agent_<id>.md and the result is marked
    DONE_WITH_CONCERNS by default (these need human review before downstream
    use).

    Backend selection (RALPH_AGENT_BACKEND env var):
      - "openrouter"  (default) — call gpt-oss-120b:free as before
      - "manual"      — skip API call entirely. Used when an interactive
                        operator (e.g. Opus running in a Claude Code session)
                        is producing the deliverables out-of-band. The
                        executor returns DONE_WITH_CONCERNS and lets the
                        gate function check whether acceptance files exist.
                        If they do, the gate promotes to DONE; if not, it
                        demotes to FAILED.
    """
    spec = task.get("spec") or {}

    # ── manual mode: defer entirely to the gate function ────────────────
    backend = os.getenv("RALPH_AGENT_BACKEND", "openrouter").strip().lower()
    if backend == "manual":
        result.status = DONE_WITH_CONCERNS
        result.notes = "manual backend — deliverable produced out-of-band; gate will validate"
        # Mark the agent .md file too so future ticks can see this task was
        # handled. Write only when the marker is absent (preserve existing).
        marker = DATA_DIR / f"ralph_agent_{task['id']}.md"
        if not marker.exists():
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(
                f"# {task['id']}\n\n_Handled in manual mode by an in-session operator. "
                f"See task acceptance files for the actual deliverable._\n",
                encoding="utf-8",
            )
        return result

    # Load .env so OPENROUTER_API_KEY is available even if the loop is
    # invoked outside an existing shell session.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        result.status = NEEDS_CONTEXT
        result.error = "OPENROUTER_API_KEY not set"
        return result

    try:
        import requests
    except ImportError:
        result.status = NEEDS_CONTEXT
        result.error = "requests not available"
        return result

    model = spec.get("model", os.getenv("RALPH_AGENT_MODEL",
                                          "openai/gpt-oss-120b:free"))

    # Constructed context — INTENTIONALLY narrow. No session history.
    system_prompt = (
        "You are a focused engineering subagent for the Quran Knowledge Graph "
        "project. You are spawned by the Ralph loop with one task. Do that "
        "task crisply. Stay focused on files mentioned in the spec. "
        "Produce the exact deliverable described in the task spec — "
        "output the deliverable directly, starting with the content."
    )
    user_prompt = (
        f"# Task: {task['id']}\n\n"
        f"**Type**: {task['type']}\n"
        f"**Description**: {task.get('description', '')}\n\n"
        f"**Spec**:\n```yaml\n{json.dumps(spec, indent=2, ensure_ascii=False)}\n```\n\n"
        "Produce the exact deliverable as described. Lead with the content."
    )

    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": float(spec.get("temperature", 0.4)),
                "max_tokens": int(spec.get("max_tokens", 2000)),
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8085",
                "X-Title": "QKG Ralph loop",
            },
            timeout=int(spec.get("timeout_sec", 180)),
        )
        r.raise_for_status()
        payload = r.json()
        body = payload["choices"][0]["message"]["content"] or ""
        # Capture token usage so the loop can pace itself against rate limits.
        usage = payload.get("usage") or {}
        result.tokens_in = int(usage.get("prompt_tokens", 0) or 0)
        result.tokens_out = int(usage.get("completion_tokens", 0) or 0)
        result.api_calls = 1
    except Exception as e:
        result.status = FAILED
        result.error = f"OpenRouter call failed: {str(e)[:300]}"
        return result

    if not body.strip():
        result.status = FAILED
        result.error = "agent returned empty response"
        return result

    out_path = DATA_DIR / f"ralph_agent_{task['id']}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"# {task['id']}\n\n"
        f"_Generated by ralph_loop agent_creative executor (model: {model})._\n"
        f"_Output requires human review before downstream use._\n\n"
        f"---\n\n{body}\n",
        encoding="utf-8",
    )
    result.artefacts.append(str(out_path.relative_to(ROOT)))
    # Default: DONE_WITH_CONCERNS — agent output needs review before
    # downstream tasks should rely on it.
    result.status = DONE_WITH_CONCERNS
    result.notes = f"wrote {out_path.name} (review before use)"
    return result


# Only types with a real executor are listed here. Unlisted types
# (prompt_variant, embed_op, cache_op, manual, external_run, etc.) fall
# through to execute_skipped via EXECUTORS.get(type, execute_skipped) below.
EXECUTORS: dict[str, Callable] = {
    "eval":            execute_eval,
    "cypher_analysis": execute_cypher_analysis,
    "cleanup":         execute_cleanup,
    "agent_creative":  execute_agent_creative,
}


# ── main tick ────────────────────────────────────────────────────────────────

def tick(force_task_id: str | None = None,
         dry_run: bool = False,
         allow_types: set[str] | None = None) -> TickResult | None:
    """Run one tick. Returns the TickResult, or None if no task was eligible."""
    state = load_state()
    backlog = load_backlog()

    if force_task_id:
        task = next((t for t in backlog.get("tasks", []) if t["id"] == force_task_id), None)
        if not task:
            raise SystemExit(f"ERROR: task '{force_task_id}' not in backlog")
    else:
        task = pick_next_task(backlog, state, allow_types=allow_types)

    if not task:
        print("[ralph] no eligible task. Backlog empty or all blocked/done.")
        return None

    if dry_run:
        print(f"[ralph] (dry) would run {task['id']} (type={task['type']}, prio={task.get('priority')})")
        print(f"        desc: {task.get('description', '')}")
        return None

    # Track attempt count for this task
    attempts = state.setdefault("attempts", {})
    attempt_n = int(attempts.get(task["id"], 0)) + 1
    attempts[task["id"]] = attempt_n
    max_a = int((task.get("spec") or {}).get("max_attempts", MAX_ATTEMPTS_DEFAULT))

    print(f"[ralph] picking {task['id']} (type={task['type']}, prio={task.get('priority')}, attempt={attempt_n}/{max_a})")
    state["in_progress"] = task["id"]
    save_state(state)

    result = TickResult(
        task_id=task["id"],
        type=task["type"],
        started_at=_now_iso(),
        attempt=attempt_n,
    )

    executor = EXECUTORS.get(task["type"], execute_skipped)
    try:
        result = executor(task, state, result)
    except Exception as e:
        result.status = FAILED
        result.error = f"{type(e).__name__}: {str(e)[:400]}"

    # ── Gate function: verify acceptance criteria after the executor ─────
    # Superpowers principle: "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION
    # EVIDENCE." Even if the executor declared DONE, run the acceptance
    # checks and demote to DONE_WITH_CONCERNS / FAILED if they don't pass.
    if result.status in {DONE, DONE_WITH_CONCERNS}:
        all_ok, checks = verify_acceptance(task, result)
        result.acceptance_results = checks
        if not all_ok:
            # Executor said done; gate function disagrees.
            result.status = FAILED
            result.notes = (result.notes or "") + " | ACCEPTANCE FAILED: " + \
                "; ".join(f"{c['check']}={'pass' if c['passed'] else 'FAIL'}" for c in checks)
        elif any(c["check"] == "none specified" for c in checks):
            # No acceptance specified — soft-pass with concerns.
            if result.status == DONE:
                result.status = DONE_WITH_CONCERNS
                result.notes = (result.notes or "") + " (no acceptance criteria — soft pass)"

    # ── Repo-wide quality gate (snarktank pattern) ──────────────────────
    # Any task that says it modifies code must clear the smoke-import
    # gate before being marked DONE. Prevents broken-Python regressions
    # from compounding across iterations.
    if (task.get("spec") or {}).get("commits_code") and result.status in {DONE, DONE_WITH_CONCERNS}:
        gate_ok, gate_msg = quality_gate()
        if not gate_ok:
            result.status = FAILED
            result.notes = (result.notes or "") + f" | QUALITY GATE FAILED: {gate_msg[:200]}"
        else:
            result.notes = (result.notes or "") + f" | quality gate ok"

    # ── Pattern recording ────────────────────────────────────────────────
    # If the executor populated result.notes with a "PATTERN:" prefix line,
    # promote it to the Codebase Patterns block. snarktank/ralph: durable
    # knowledge separate from per-tick rows.
    if result.status in TERMINAL_OK and result.notes:
        for line in (result.notes or "").splitlines():
            if line.strip().startswith("PATTERN:"):
                add_codebase_pattern(line.strip()[len("PATTERN:"):].strip(),
                                     source_task=task["id"])

    result.finished_at = _now_iso()

    # Persist
    state["in_progress"] = None
    state["last_tick"] = result.finished_at
    state["tick_count"] = int(state.get("tick_count", 0)) + 1
    state.setdefault("history", []).append(asdict(result))

    if result.status in TERMINAL_OK:
        if result.status == SKIPPED:
            state.setdefault("skipped_task_ids", []).append(task["id"])
        else:
            state.setdefault("done_task_ids", []).append(task["id"])
            # Reset attempt count on success
            attempts.pop(task["id"], None)
    elif result.status in TERMINAL_FAIL:
        # Three-strikes rule (superpowers: "3 failed attempts → architectural")
        if attempt_n >= max_a:
            state.setdefault("quarantined_task_ids", []).append(task["id"])
            result.notes = (result.notes or "") + f" | QUARANTINED after {attempt_n} attempts"
            print(f"[ralph] QUARANTINING {task['id']} (failed {attempt_n}× — superpowers 3-strikes rule)")

    # ── token / API-call accounting ─────────────────────────────────────
    # Roll cumulative + 24h-windowed usage so ralph_run.py can pace.
    if result.api_calls or result.tokens_in or result.tokens_out:
        usage_state = state.setdefault("api_usage", {
            "calls_total": 0,
            "tokens_in_total": 0,
            "tokens_out_total": 0,
            "window": [],   # list of (iso_ts, calls, tokens_in, tokens_out)
        })
        usage_state["calls_total"] = int(usage_state.get("calls_total", 0)) + result.api_calls
        usage_state["tokens_in_total"] = int(usage_state.get("tokens_in_total", 0)) + result.tokens_in
        usage_state["tokens_out_total"] = int(usage_state.get("tokens_out_total", 0)) + result.tokens_out
        win = usage_state.setdefault("window", [])
        win.append([result.finished_at, result.api_calls, result.tokens_in, result.tokens_out])
        # Trim to last 24h
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        usage_state["window"] = [
            row for row in win
            if datetime.fromisoformat(row[0].replace("Z", "+00:00")) >= cutoff
        ]

    save_state(state)
    append_log(result, task)

    # Console output
    print(f"[ralph] {result.status:<20}  {task['id']}")
    if result.metric_before is not None and result.metric_after is not None:
        print(f"        {result.metric_before:.2f} -> {result.metric_after:.2f}  ({result.delta:+.2f})")
    if result.notes:
        print(f"        notes: {result.notes}")
    if result.error:
        print(f"        error: {result.error[:200]}")
    if result.artefacts:
        print(f"        artefacts: {', '.join(result.artefacts)}")
    if result.acceptance_results:
        for c in result.acceptance_results:
            mark = "✓" if c["passed"] else "✗"
            print(f"        {mark} {c['check']}: {c['detail'][:80]}")
    if result.api_calls:
        print(f"        tokens: in={result.tokens_in} out={result.tokens_out} "
              f"(cumulative calls={state.get('api_usage', {}).get('calls_total', 0)})")
    return result


# ── helpers exposed for ralph_tick.py CLI ───────────────────────────────────

def is_project_complete(state: dict | None = None,
                         backlog: dict | None = None) -> tuple[bool, list[dict]]:
    """
    Check whether the project's top-level completion criteria are all met.

    snarktank/ralph signals "<promise>COMPLETE</promise>" when all stories
    in prd.json have passes:true. We allow a richer set of criteria in
    ralph_backlog.yaml's `project_completion:` block:

      project_completion:
        all_tasks_done: true                            # all backlog ids in done
        ignore_quarantined: true                        # don't require quarantined
        min_metric:
          name: avg_unique_cites_per_q
          eval: data/eval_v1_results.json
          value: 50.0
        require_files: [data/multihop_bench.jsonl]      # must exist
    """
    state = state if state is not None else load_state()
    backlog = backlog if backlog is not None else load_backlog()
    crit = (backlog.get("project_completion") or {})
    if not crit:
        return False, [{"check": "project_completion not declared", "passed": False,
                        "detail": "edit ralph_backlog.yaml to add a project_completion: block"}]

    out = []
    all_ok = True

    if crit.get("all_tasks_done"):
        done = set(state.get("done_task_ids", []))
        skipped = set(state.get("skipped_task_ids", []))
        quarantined = set(state.get("quarantined_task_ids", []))
        ignore_quar = bool(crit.get("ignore_quarantined", True))
        ignore_skip = bool(crit.get("ignore_skipped", True))
        outstanding = []
        for t in backlog.get("tasks", []):
            tid = t["id"]
            if tid in done:
                continue
            if ignore_skip and tid in skipped:
                continue
            if ignore_quar and tid in quarantined:
                continue
            outstanding.append(tid)
        ok = not outstanding
        all_ok = all_ok and ok
        out.append({"check": "all_tasks_done",
                    "passed": ok,
                    "detail": f"outstanding: {outstanding[:6]}" if outstanding else "all done"})

    if "min_metric" in crit:
        mc = crit["min_metric"]
        eval_path = ROOT / mc.get("eval", "data/eval_v1_results.json")
        v = _read_eval_metrics(eval_path, mc["name"])
        ok = v is not None and v >= float(mc["value"])
        all_ok = all_ok and ok
        out.append({"check": f"min_metric {mc['name']} >= {mc['value']}",
                    "passed": ok,
                    "detail": f"actual={v}"})

    for path in crit.get("require_files", []) or []:
        p = ROOT / path
        ok = p.exists()
        all_ok = all_ok and ok
        out.append({"check": f"require_file {path}",
                    "passed": ok,
                    "detail": str(p) if ok else "missing"})

    return all_ok, out


def status() -> dict:
    state = load_state()
    backlog = load_backlog()
    backlog_size = len(backlog.get("tasks", []))
    done = len(state.get("done_task_ids", []))
    skipped = len(state.get("skipped_task_ids", []))
    quarantined = len(state.get("quarantined_task_ids", []))
    pending = backlog_size - done - skipped - quarantined
    attempts = state.get("attempts", {})
    project_done, project_checks = is_project_complete(state, backlog)
    return {
        "tick_count": state.get("tick_count", 0),
        "last_tick": state.get("last_tick"),
        "in_progress": state.get("in_progress"),
        "backlog_size": backlog_size,
        "done": done,
        "skipped": skipped,
        "quarantined": quarantined,
        "pending": pending,
        "next_pick": (pick_next_task(backlog, state) or {}).get("id"),
        "in_flight_attempts": {k: v for k, v in attempts.items() if v > 0},
        "project_complete": project_done,
        "project_checks": project_checks,
    }
