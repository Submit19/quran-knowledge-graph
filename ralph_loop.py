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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent
BACKLOG_PATH = ROOT / "ralph_backlog.yaml"
STATE_PATH = ROOT / "ralph_state.json"
LOG_PATH = ROOT / "ralph_log.md"
DATA_DIR = ROOT / "data"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── state I/O ────────────────────────────────────────────────────────────────

@dataclass
class TickResult:
    task_id: str
    type: str
    started_at: str
    finished_at: str = ""
    status: str = "running"          # running | success | regression | failed | skipped
    metric_before: float | None = None
    metric_after: float | None = None
    delta: float | None = None
    notes: str = ""
    artefacts: list[str] = field(default_factory=list)   # filenames written
    new_tasks: list[str] = field(default_factory=list)   # task_ids appended to backlog
    error: str | None = None


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
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict):
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


def save_backlog(backlog: dict):
    """Persist backlog (used when adding discovered follow-up tasks)."""
    import yaml
    BACKLOG_PATH.write_text(
        yaml.safe_dump(backlog, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def append_log(result: TickResult, task: dict):
    """Append a markdown row to ralph_log.md."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text(
            "# Ralph Loop — tick log\n\n"
            "| ts | task_id | type | status | metric Δ | notes |\n"
            "|----|---------|------|--------|----------|-------|\n",
            encoding="utf-8",
        )
    delta_s = ""
    if result.delta is not None:
        delta_s = f"{result.delta:+.2f}"
    notes = (result.notes or result.error or "")[:160].replace("\n", " ").replace("|", "/")
    row = f"| {result.started_at[:16]} | {result.task_id} | {result.type} | {result.status} | {delta_s} | {notes} |\n"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(row)


# ── task picker ──────────────────────────────────────────────────────────────

def pick_next_task(backlog: dict, state: dict, allow_types: set[str] | None = None) -> dict | None:
    """
    Return the highest-priority task that:
      - is not already done
      - is not in_progress
      - has no unfinished blockers
      - is in `allow_types` if specified (default: skip 'manual' and 'external_run')
    """
    skip_types = {"manual", "external_run"}
    if allow_types is not None:
        skip_types -= allow_types
    done = set(state.get("done_task_ids", []))
    skipped = set(state.get("skipped_task_ids", []))
    in_prog = state.get("in_progress")

    candidates = []
    for t in backlog.get("tasks", []):
        if t["id"] in done or t["id"] in skipped or t["id"] == in_prog:
            continue
        if t.get("type") in skip_types:
            continue
        if any(b not in done for b in (t.get("blockers") or [])):
            continue
        candidates.append(t)

    candidates.sort(key=lambda t: -int(t.get("priority", 0)))
    return candidates[0] if candidates else None


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
        result.status = "failed"
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
    if current is not None and baseline is not None:
        result.delta = current - baseline
        regression_pct = float(spec.get("regression_pct", 5))
        if current < baseline * (1 - regression_pct / 100):
            result.status = "regression"
            result.notes = f"{metric}: {baseline:.2f} -> {current:.2f} (regression > {regression_pct}%)"
        else:
            result.status = "success"
            result.notes = f"{metric}: {baseline:.2f} -> {current:.2f}"
    else:
        result.status = "success" if current is not None else "failed"
        result.notes = f"{metric}={current}"
    return result


def execute_cypher_analysis(task: dict, state: dict, result: TickResult) -> TickResult:
    """Run a read-only Cypher query or python script and dump output to a file."""
    spec = task.get("spec") or {}
    out_md = DATA_DIR / f"ralph_analysis_{task['id']}.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)
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
            result.status = "failed"
            result.error = text[-400:]
        finally:
            sys.stdout = old
        out_md.write_text("# " + task["id"] + "\n\n```\n" + text + "\n```\n", encoding="utf-8")
    elif "query" in spec:
        from dotenv import load_dotenv; load_dotenv()
        from neo4j import GraphDatabase
        d = GraphDatabase.driver(os.getenv("NEO4J_URI"),
                                  auth=(os.getenv("NEO4J_USER"),
                                        os.getenv("NEO4J_PASSWORD")))
        try:
            with d.session(database=os.getenv("NEO4J_DATABASE", "quran")) as s:
                rows = s.run(spec["query"]).data()
            text = json.dumps(rows, indent=2, ensure_ascii=False, default=str)
            out_md.write_text(f"# {task['id']}\n\n```json\n{text}\n```\n", encoding="utf-8")
        except Exception as e:
            result.status = "failed"
            result.error = str(e)[-400:]
        finally:
            d.close()
    else:
        result.status = "failed"
        result.error = "spec missing 'query' or 'script'"
        return result

    result.artefacts.append(str(out_md.relative_to(ROOT)))
    if not result.error:
        result.status = "success"
        result.notes = f"wrote {out_md.name}"
    return result


def execute_cleanup(task: dict, state: dict, result: TickResult) -> TickResult:
    """No-op success — placeholder for hygiene tasks. Add real logic per task."""
    result.status = "success"
    result.notes = task.get("description", "")[:80]
    return result


def execute_skipped(task: dict, state: dict, result: TickResult) -> TickResult:
    """For task types we don't auto-execute (manual, external_run, agent_creative
    when no LLM key configured)."""
    result.status = "skipped"
    result.notes = f"type={task.get('type')} requires manual / agent involvement"
    return result


EXECUTORS: dict[str, Callable] = {
    "eval": execute_eval,
    "cypher_analysis": execute_cypher_analysis,
    "cleanup": execute_cleanup,
    # Stubs — will skip with a clear note until proper executors are added:
    "prompt_variant":  execute_skipped,
    "embed_op":        execute_skipped,
    "cache_op":        execute_skipped,
    "agent_creative":  execute_skipped,
    "manual":          execute_skipped,
    "external_run":    execute_skipped,
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
            print(f"ERROR: task '{force_task_id}' not in backlog")
            return None
    else:
        task = pick_next_task(backlog, state, allow_types=allow_types)

    if not task:
        print("[ralph] no eligible task. Backlog empty or all blocked/done.")
        return None

    if dry_run:
        print(f"[ralph] (dry) would run {task['id']} (type={task['type']}, prio={task.get('priority')})")
        print(f"        desc: {task.get('description', '')}")
        return None

    print(f"[ralph] picking {task['id']} (type={task['type']}, prio={task.get('priority')})")
    state["in_progress"] = task["id"]
    save_state(state)

    result = TickResult(
        task_id=task["id"],
        type=task["type"],
        started_at=_now_iso(),
    )

    executor = EXECUTORS.get(task["type"], execute_skipped)
    try:
        result = executor(task, state, result)
    except Exception as e:
        result.status = "failed"
        result.error = str(e)[:600]

    result.finished_at = _now_iso()

    # Persist
    state["in_progress"] = None
    state["last_tick"] = result.finished_at
    state["tick_count"] = int(state.get("tick_count", 0)) + 1
    state.setdefault("history", []).append(asdict(result))
    if result.status == "success":
        state.setdefault("done_task_ids", []).append(task["id"])
    elif result.status == "skipped":
        state.setdefault("skipped_task_ids", []).append(task["id"])
    elif result.status in ("regression", "failed"):
        # leave the task in the queue (not added to done) but record the attempt
        pass
    save_state(state)
    append_log(result, task)

    # Console output
    print(f"[ralph] {result.status:<10}  {task['id']}")
    if result.metric_before is not None and result.metric_after is not None:
        print(f"        {result.metric_before:.2f} -> {result.metric_after:.2f}  ({result.delta:+.2f})")
    if result.notes:
        print(f"        notes: {result.notes}")
    if result.error:
        print(f"        error: {result.error[:200]}")
    if result.artefacts:
        print(f"        artefacts: {', '.join(result.artefacts)}")
    return result


# ── helpers exposed for ralph_tick.py CLI ───────────────────────────────────

def status() -> dict:
    state = load_state()
    backlog = load_backlog()
    backlog_size = len(backlog.get("tasks", []))
    done = len(state.get("done_task_ids", []))
    skipped = len(state.get("skipped_task_ids", []))
    pending = backlog_size - done - skipped
    return {
        "tick_count": state.get("tick_count", 0),
        "last_tick": state.get("last_tick"),
        "in_progress": state.get("in_progress"),
        "backlog_size": backlog_size,
        "done": done,
        "skipped": skipped,
        "pending": pending,
        "next_pick": (pick_next_task(backlog, state) or {}).get("id"),
    }
