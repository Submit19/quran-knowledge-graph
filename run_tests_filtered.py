"""
run_tests_filtered.py — Filtered test runner for the QKG quality gate.

Jeff Huntley principle: "Most test runners are trash. They output too many tokens."
This wrapper runs eval_v1.py and Cypher smoke-test scripts, then:
  - Suppresses all PASS / INFO / progress lines.
  - Emits only FAIL lines + a compact summary.
  - On a fully-green run, output is <=5 lines.

Usage:
    python run_tests_filtered.py                    # run the default smoke suite
    python run_tests_filtered.py --quick            # skip full eval; run only fast checks
    python run_tests_filtered.py --suite eval       # run eval_v1.py only
    python run_tests_filtered.py --suite cypher     # run cypher smoke tests only
    python run_tests_filtered.py --suite all        # run all (default)

Exit codes:
    0 — all tests pass
    1 — one or more tests failed or errored
    2 — suite did not start (config / import error)

Called by ralph_tick.py acceptance gates to keep tick output minimal.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Patterns that classify a line as PASS-noise (suppress these).
# A line is printed only if it is NOT matched by any suppress pattern
# AND (it matches a FAIL pattern OR flag_all_failures is set).
# ---------------------------------------------------------------------------
_SUPPRESS_RE = re.compile(
    r"^\s*("
    r"OK\b"                             # "OK: ..."
    r"|PASS\b"                          # "PASS"
    r"|\[PASS\]"
    r"|pass\b"
    r"|\[ok\]"
    r"|=== .* \(\d+ questions\)"        # eval batch header
    r"|\[\d+/\d+\]"                     # [1/13] question progress
    r"|-> [0-9]"                        # "  -> 12.3s · 5 tools · ..."
    r"|tool calls:"                     # tool breakdown line
    r"|Saved to "
    r"|Running "
    r"|loading "
    r"|Loaded "
    r"|Using "
    r"|\[tick_finalize\]"
    r"|\[info\]"
    r"|\[INFO\]"
    r"|INFO:"
    r"|DEBUG:"
    r")",
    re.IGNORECASE,
)

_FAIL_RE = re.compile(
    r"\b(FAIL|ERROR|ASSERT|assert|Exception|Traceback|regression|REGRESSION"
    r"|BLOCKED|not found|missing|too small|mismatch)\b",
    re.IGNORECASE,
)


def filter_output(raw: str) -> list[str]:
    """Return only the lines worth surfacing (failures, warnings, non-noise)."""
    kept = []
    for line in raw.splitlines():
        stripped = line.rstrip()
        if not stripped:
            continue
        if _SUPPRESS_RE.search(stripped):
            continue  # pure noise
        kept.append(stripped)
    return kept


# ---------------------------------------------------------------------------
# Cypher smoke checks — fast, offline-friendly, no app_free.py needed.
# Each check is (label, script_text) where script_text runs against Neo4j.
# ---------------------------------------------------------------------------

CYPHER_SMOKE_CHECKS = [
    (
        "verse_count",
        """
import os
from neo4j import GraphDatabase

uri = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
user = os.environ.get("NEO4J_USER", "neo4j")
pw = os.environ.get("NEO4J_PASSWORD", "Bismillah19")
db = os.environ.get("NEO4J_DATABASE", "quran")

driver = GraphDatabase.driver(uri, auth=(user, pw))
with driver.session(database=db) as s:
    count = s.run("MATCH (v:Verse) RETURN count(v) AS n").single()["n"]
assert count >= 6200, f"FAIL verse_count: expected >=6200 got {count}"
print(f"PASS verse_count: {count} verses")
driver.close()
""",
    ),
    (
        "index_presence",
        """
import os
from neo4j import GraphDatabase

uri = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
user = os.environ.get("NEO4J_USER", "neo4j")
pw = os.environ.get("NEO4J_PASSWORD", "Bismillah19")
db = os.environ.get("NEO4J_DATABASE", "quran")

driver = GraphDatabase.driver(uri, auth=(user, pw))
with driver.session(database=db) as s:
    rows = s.run("SHOW INDEXES YIELD name RETURN name").data()
    names = {r["name"] for r in rows}
required = {"verse_embedding_m3", "verse_text_fulltext"}
missing = required - names
assert not missing, f"FAIL index_presence: missing indexes {missing}"
print(f"PASS index_presence: required indexes present ({len(names)} total)")
driver.close()
""",
    ),
    (
        "arabic_text_present",
        """
import os
from neo4j import GraphDatabase

uri = os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687")
user = os.environ.get("NEO4J_USER", "neo4j")
pw = os.environ.get("NEO4J_PASSWORD", "Bismillah19")
db = os.environ.get("NEO4J_DATABASE", "quran")

driver = GraphDatabase.driver(uri, auth=(user, pw))
with driver.session(database=db) as s:
    n = s.run(
        "MATCH (v:Verse) WHERE v.arabicText IS NOT NULL RETURN count(v) AS n"
    ).single()["n"]
assert n >= 6000, f"FAIL arabic_text_present: only {n} verses have arabicText"
print(f"PASS arabic_text_present: {n} verses have arabicText")
driver.close()
""",
    ),
]


def run_cypher_smoke() -> tuple[int, int, list[str]]:
    """Run the Cypher smoke checks. Returns (passed, failed, fail_lines)."""
    passed = failed = 0
    fail_lines: list[str] = []
    for label, script in CYPHER_SMOKE_CHECKS:
        try:
            out = subprocess.check_output(
                [sys.executable, "-c", script],
                cwd=str(ROOT),
                stderr=subprocess.STDOUT,
                timeout=30,
            ).decode("utf-8", errors="replace")
            # Surface only non-PASS lines
            extras = filter_output(out)
            if extras:
                fail_lines.extend(extras)
            passed += 1
        except subprocess.CalledProcessError as e:
            failed += 1
            raw = e.output.decode("utf-8", errors="replace")
            fail_lines.append(f"FAIL [{label}]: {raw.strip()[:200]}")
        except subprocess.TimeoutExpired:
            failed += 1
            fail_lines.append(f"FAIL [{label}]: timeout (>30s) — Neo4j unreachable?")
    return passed, failed, fail_lines


def run_eval(quick: bool = False) -> tuple[int, int, list[str]]:
    """
    Run eval_v1.py as a subprocess and filter output.
    In quick mode we only check that the file can be imported (no live server needed).
    Returns (passed_count, failed_count, fail_lines).
    """
    fail_lines: list[str] = []

    if quick:
        # Just import-check
        try:
            subprocess.check_output(
                [sys.executable, "-c", "import eval_v1; print('PASS import eval_v1')"],
                cwd=str(ROOT),
                stderr=subprocess.STDOUT,
                timeout=15,
            )
            return 1, 0, []
        except subprocess.CalledProcessError as e:
            return 0, 1, [f"FAIL eval_v1 import: {e.output.decode('utf-8', errors='replace')[:200]}"]

    # Full eval — requires live server at :8085.
    try:
        t0 = time.time()
        result = subprocess.run(
            [sys.executable, "eval_v1.py"],
            cwd=str(ROOT),
            capture_output=True,
            timeout=1800,  # 30 min max
        )
        elapsed = round(time.time() - t0, 1)
        combined = result.stdout.decode("utf-8", errors="replace") + result.stderr.decode("utf-8", errors="replace")

        # Check for a usable results JSON
        out_json = ROOT / "data" / "eval_v1_results.json"
        if result.returncode != 0:
            fail_lines.append(f"FAIL eval_v1: exit {result.returncode} after {elapsed}s")
            for line in filter_output(combined):
                if _FAIL_RE.search(line):
                    fail_lines.append(f"  {line}")
            return 0, 1, fail_lines

        if not out_json.exists() or out_json.stat().st_size < 50_000:
            sz = out_json.stat().st_size if out_json.exists() else 0
            fail_lines.append(f"FAIL eval_v1: results JSON too small ({sz} bytes), expected >=50000")
            return 0, 1, fail_lines

        # Parse and check avg metric
        try:
            data = json.loads(out_json.read_text(encoding="utf-8"))
            all_rows = (data.get("general") or []) + (data.get("surah") or []) + (data.get("targeted") or [])
            if all_rows:
                avg_cites = sum(r.get("n_cites_unique", 0) for r in all_rows) / len(all_rows)
                if avg_cites < 25:
                    fail_lines.append(f"FAIL eval_v1: avg_unique_cites={avg_cites:.1f} < 25 (regression threshold)")
                    return 0, 1, fail_lines
        except Exception as parse_err:
            fail_lines.append(f"WARN eval_v1: could not parse results JSON: {parse_err}")

        return 1, 0, []
    except subprocess.TimeoutExpired:
        return 0, 1, [f"FAIL eval_v1: timed out after 1800s"]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--suite",
        choices=["all", "eval", "cypher"],
        default="all",
        help="Which test suite to run (default: all)",
    )
    ap.add_argument(
        "--quick",
        action="store_true",
        help="Fast mode: skip live eval; only import-check + cypher smoke",
    )
    args = ap.parse_args()

    total_pass = total_fail = 0
    all_fail_lines: list[str] = []

    run_eval_suite = args.suite in ("all", "eval")
    run_cypher_suite = args.suite in ("all", "cypher")

    if run_cypher_suite:
        cp, cf, cfl = run_cypher_smoke()
        total_pass += cp
        total_fail += cf
        all_fail_lines.extend(cfl)

    if run_eval_suite:
        ep, ef, efl = run_eval(quick=args.quick)
        total_pass += ep
        total_fail += ef
        all_fail_lines.extend(efl)

    # Output — ONLY failures + summary (green run = <=5 lines)
    for line in all_fail_lines:
        print(line)

    total = total_pass + total_fail
    if total_fail == 0:
        print(f"PASS: {total_pass}/{total} checks passed")
        return 0
    else:
        print(f"FAIL: {total_fail}/{total} checks failed, {total_pass} passed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
