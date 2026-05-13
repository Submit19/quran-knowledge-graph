# QKG tests

Beck-style test infrastructure built in Phase 1 of `docs/QKG_RETROFIT_PLAN.md`.

## Run all tests

```bash
python -m pytest tests/ -v
```

## Run with coverage

```bash
python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Run in parallel (after pytest-xdist is installed)

```bash
python -m pytest tests/ -n auto
```

## Layout

```
tests/
├── conftest.py           # shared pytest fixtures (mock Neo4j sessions)
├── fakes/
│   ├── neo4j_session.py  # FakeNeo4jSession — Beck "Fake It" double for neo4j.Session
│   └── llm_client.py     # FakeLLMClient — Self-Shunt for the agent loop (Phase 1 item 6)
├── test_get_verse.py     # First failing test → first green bar (Phase 1 item 5)
└── test_agent_loop.py    # Agent loop end-to-end with fake LLM (Phase 1 item 6)
```

## Fixtures

- `empty_session` — FakeNeo4jSession backed by an empty graph. Used for red-bar
  tests: tools should report "not found" structurally rather than crash.
- `fatiha_session` — FakeNeo4jSession with verse 1:1 (Al-Fatihah opening) only.
  Used for green-bar tests against `tool_get_verse`.

When a test needs a richer graph, build it inline in the test or add a new
named fixture to `conftest.py`. When a test needs real Cypher semantics
(e.g. complex traversals the fake can't replicate), swap in
[testcontainers-python](https://testcontainers-python.readthedocs.io) with a
Neo4j container — same `session` shape, just slower. The fake is deliberately
small so the substitution is cheap when you outgrow it.

## Adding a new test

Follow Beck's Red/Green/Refactor:

1. Write the failing test first. Run it. Confirm it fails (red bar).
2. Write the minimum code (or extend the fixture) to make it pass.
3. Confirm green. Refactor freely while staying green.
4. Commit each step as a separate commit.

## What's intentionally out of scope here (Phase 1)

- Tests for `app.py`, `app_full.py`, `app_lite.py`, `app_free.py` — those wait
  for the four-apps refactor in Phase 3.
- Tests against real Neo4j — fixture wires up testcontainers in Phase 4 if needed.
- `mypy` over the legacy `chat.py` — too many existing violations; mypy runs
  on `tests/` and new files only via pre-commit.

## Why this exists

Per `docs/QKG_AUDIT.md`: the project had one real test file (an A/B harness,
not unit tests). That meant every code change was a live-fire test against
production. Phase 1 of the retrofit plan establishes pytest infrastructure
and the first green bar so future work can converge to a defined attractor
(Beck's term) instead of moving in any direction the loop's gradient points.
