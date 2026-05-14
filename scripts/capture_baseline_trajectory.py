"""Capture an SSE trajectory from an app's _agent_stream as a structural baseline.

Phase 3a safety net (docs/PHASE_3A_PLAN.md). Before extracting shared_agent.py
from each app, this harness records the shape of one canonical chat turn:
the sequence of SSE event types, the tool calls made, and the final answer's
fingerprint. After the refactor, the same harness re-runs and we diff against
the v0 trace to confirm no observable behaviour change.

Outputs:
  data/baseline_trajectory[_<app>]_v0.json — full event sequence + summary
  data/baseline_trajectory[_<app>]_v0.summary.txt — human-readable summary

The full sequence is non-deterministic across runs (LLM sampling, model
warm-up), but the *structural* summary should match v0 vs v1 — same event
types in the same order, same tool names called, similar text lengths.

Usage:
  python scripts/capture_baseline_trajectory.py [--output v0] [--app app_free]
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


BASELINE_QUESTION = "What does verse 2:255 say?"
OUTPUT_DIR = ROOT / "data"


def _parse_sse_frame(frame: str) -> dict | None:
    """Pull the JSON payload out of an 'data: {...}\\n\\n' SSE line."""
    if not frame.startswith("data: "):
        return None
    body = frame[len("data: ") :].rstrip("\n").rstrip()
    if not body:
        return None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


async def _drive_agent_stream(app_module, question: str) -> list[dict]:
    """Run _agent_stream end-to-end and collect every event."""
    events: list[dict] = []
    async for raw_frame in app_module._agent_stream(question, history=[]):
        payload = _parse_sse_frame(raw_frame)
        if payload is None:
            continue
        events.append(payload)
    return events


def _summarise(events: list[dict]) -> dict:
    """Structural fingerprint we can compare across runs."""
    event_types: list[str] = []
    tool_calls: list[dict] = []
    text_chars = 0
    verse_ids_in_done: list[str] = []
    has_error = False
    has_done = False

    for ev in events:
        t = ev.get("t")
        if t is None:
            continue
        event_types.append(t)
        if t == "tool":
            raw_args = ev.get("args")
            args_keys = None
            if isinstance(raw_args, str) and raw_args.startswith("{"):
                try:
                    args_keys = sorted(json.loads(raw_args))
                except (json.JSONDecodeError, TypeError):
                    # Tool-call args strings are truncated to ~80 chars + "...".
                    # Truncated JSON is unparseable; that's fine for the
                    # structural fingerprint — we just record the name.
                    args_keys = None
            tool_calls.append({"name": ev.get("name"), "args_keys": args_keys})
        elif t == "text":
            text_chars += len(ev.get("d") or "")
        elif t == "done":
            has_done = True
            verses = ev.get("verses") or []
            if isinstance(verses, dict):
                verse_ids_in_done = sorted(verses.keys())
            elif isinstance(verses, list):
                verse_ids_in_done = [
                    v.get("verseId")
                    for v in verses
                    if isinstance(v, dict) and v.get("verseId")
                ]
        elif t == "error":
            has_error = True

    citation_refs = sorted(
        set(
            re.findall(
                r"\[(\d+):(\d+)\]",
                "".join(ev.get("d", "") for ev in events if ev.get("t") == "text"),
            )
        )
    )

    return {
        "n_events": len(events),
        "event_types_in_order": event_types,
        "event_type_counts": {t: event_types.count(t) for t in set(event_types)},
        "tool_names_in_order": [tc["name"] for tc in tool_calls],
        "n_tool_calls": len(tool_calls),
        "text_total_chars": text_chars,
        "n_verse_citations_in_text": len(citation_refs),
        "verse_ids_in_done": verse_ids_in_done,
        "has_done": has_done,
        "has_error": has_error,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="v0",
        help="Output suffix: 'v0' for pre-refactor baseline, 'v1' for post-refactor.",
    )
    parser.add_argument(
        "--app",
        default="app_free",
        help="App module to drive (e.g. app_free, app_lite). Must expose "
        "_agent_stream(message, history).",
    )
    parser.add_argument(
        "--question",
        default=BASELINE_QUESTION,
        help=f"Question to drive the agent with (default: {BASELINE_QUESTION!r}).",
    )
    args = parser.parse_args()

    # Importing the app is heavy (Neo4j connect, model imports). The harness
    # pays this cost once; the captured trajectory has none of it.
    print(f"[capture] importing {args.app} …", flush=True)
    app_module = importlib.import_module(args.app)

    OUTPUT_DIR.mkdir(exist_ok=True)
    # Default app (app_free) preserves the original filename for backwards-
    # compat with earlier baselines; other apps get a tagged filename.
    if args.app == "app_free":
        stem = f"baseline_trajectory_{args.output}"
    else:
        stem = f"baseline_trajectory_{args.app}_{args.output}"
    output_json = OUTPUT_DIR / f"{stem}.json"
    output_summary = OUTPUT_DIR / f"{stem}.summary.txt"

    print(f"[capture] question: {args.question!r}", flush=True)
    print("[capture] driving _agent_stream …", flush=True)
    started = time.monotonic()
    events = asyncio.run(_drive_agent_stream(app_module, args.question))
    elapsed = time.monotonic() - started
    print(f"[capture] {len(events)} events in {elapsed:.1f}s", flush=True)

    summary = _summarise(events)
    summary["elapsed_seconds"] = round(elapsed, 1)
    summary["question"] = args.question

    output_json.write_text(
        json.dumps(
            {"summary": summary, "events": events}, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    print(f"[capture] wrote {output_json}", flush=True)

    summary_text = "\n".join(
        [
            f"question           : {summary['question']!r}",
            f"elapsed            : {summary['elapsed_seconds']}s",
            f"n_events           : {summary['n_events']}",
            f"event types        : {summary['event_types_in_order']}",
            f"event_type_counts  : {summary['event_type_counts']}",
            f"tool calls         : {summary['tool_names_in_order']}",
            f"n_tool_calls       : {summary['n_tool_calls']}",
            f"text_total_chars   : {summary['text_total_chars']}",
            f"citations in text  : {summary['n_verse_citations_in_text']}",
            f"verses_in_done     : {summary['verse_ids_in_done']}",
            f"has_done           : {summary['has_done']}",
            f"has_error          : {summary['has_error']}",
        ]
    )
    output_summary.write_text(summary_text + "\n", encoding="utf-8")
    print(f"[capture] wrote {output_summary}", flush=True)
    print("---SUMMARY---")
    print(summary_text)


if __name__ == "__main__":
    main()
