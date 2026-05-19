"""
Regression guard: every canonical verse the project claims to ship MUST be
present as a :Verse node in Neo4j.

In May 2026 a manual Neo4j inspection turned up just 6,231 :Verse nodes
when the project ships 6,234 (the canonical 6,236 minus the two
Khalifa-excluded verses 9:128 and 9:129). Three iconic verses were
silently absent:

  - 2:255  Ayat al-Kursi  (the Throne Verse)
  - 2:286  closing du'a of Al-Baqarah
  - 24:35  Ayat an-Nur    (the Verse of Light)

Their text exists in `data/verses.json` and in `data/verse_nodes.csv` (which
import_neo4j.py loads with `MERGE`), so the loss happened post-import. We do
not yet know whether a stray DELETE, an old-schema cleanup pass, or an
operator-typed Cypher dropped them — but a regression guard at the graph
layer pins down the desired state regardless of the entry point.

Tests are skipped when Neo4j is unreachable so CI without infrastructure
still passes. When Neo4j IS reachable the tests are authoritative.

Note: `data/verses.json` is already post-Khalifa-exclusion (6,234 entries,
9:128 and 9:129 absent from the source file itself), so the per-surah
coverage test does not need to subtract them. The KHALIFA_EXCLUDED guard
below is a defence-in-depth check in case a future revision re-adds them
to verses.json without updating the translation policy.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

# Verses Khalifa flagged as forged via the 19-based mathematical code. The
# project's translation choice excludes them; the system prompt and the
# GraphMeta node both document the rationale.
KHALIFA_EXCLUDED = {(9, 128), (9, 129)}

# Three famous verses confirmed missing from Neo4j on 2026-05-19. These are
# the regression guard the operator will recognise on sight.
ICONIC_VERSES = ["2:255", "2:286", "24:35"]


@pytest.fixture(scope="module")
def neo4j_session():
    """Yield a Neo4j session against the live `quran` database, or skip."""
    try:
        from dotenv import load_dotenv
        from neo4j import GraphDatabase
    except ImportError as exc:  # pragma: no cover — defensive
        pytest.skip(f"neo4j/python-dotenv not installed: {exc}")

    load_dotenv()
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "quran")

    if not password:
        pytest.skip("NEO4J_PASSWORD not set — skipping live-graph regression")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except Exception as exc:  # pragma: no cover — env-dependent
        driver.close()
        pytest.skip(f"Neo4j unreachable at {uri}: {exc}")

    session = driver.session(database=database)
    try:
        yield session
    finally:
        session.close()
        driver.close()


def test_three_iconic_verses_present(neo4j_session):
    """Direct lookups for the three iconic verses must return non-empty text."""
    missing = []
    for vid in ICONIC_VERSES:
        record = neo4j_session.run(
            "MATCH (v:Verse {verseId: $vid}) "
            "RETURN v.text AS text, v.arabicPlain AS arabicPlain",
            vid=vid,
        ).single()
        if record is None:
            missing.append((vid, "no Verse node"))
            continue
        if not record["text"] or not record["text"].strip():
            missing.append((vid, "empty .text"))
            continue
        if not record["arabicPlain"] or not record["arabicPlain"].strip():
            missing.append((vid, "empty .arabicPlain"))

    assert not missing, "Canonical-verse regression: " + "; ".join(
        f"{v}: {why}" for v, why in missing
    )


def test_no_canonical_verse_missing(neo4j_session):
    """Every Khalifa-canonical (surah, verseNum) pair must exist as a Verse node.

    Source of truth: data/verses.json. The file already excludes the two
    Khalifa-rejected verses (9:128, 9:129) — it ships 6,234 entries, and we
    expect every one of them as a :Verse node, not just the count.
    """
    verses_json = Path(__file__).resolve().parent.parent / "data" / "verses.json"
    with verses_json.open(encoding="utf-8") as f:
        canonical = json.load(f)

    expected_pairs = {
        (item["surah"], item["verse"])
        for item in canonical
        if (item["surah"], item["verse"]) not in KHALIFA_EXCLUDED
    }
    assert len(expected_pairs) == 6234, (
        f"data/verses.json count drift: expected 6,234, got {len(expected_pairs)}. "
        f"If the translation policy changed, update both the count and "
        f"KHALIFA_EXCLUDED."
    )

    present_rows = neo4j_session.run(
        "MATCH (v:Verse) WHERE v.verseId IS NOT NULL "
        "RETURN v.surah AS surah, v.verseNum AS verseNum"
    )
    present_pairs = {(row["surah"], row["verseNum"]) for row in present_rows}

    missing = sorted(expected_pairs - present_pairs)
    unexpected = sorted(present_pairs - expected_pairs)

    detail_lines = []
    if missing:
        sample = ", ".join(f"{s}:{n}" for s, n in missing[:10])
        more = f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""
        detail_lines.append(f"missing {len(missing)} verses: {sample}{more}")
    if unexpected:
        sample = ", ".join(f"{s}:{n}" for s, n in unexpected[:10])
        more = f" (+{len(unexpected) - 10} more)" if len(unexpected) > 10 else ""
        detail_lines.append(f"unexpected {len(unexpected)} verses: {sample}{more}")

    assert not missing and not unexpected, "Canonical coverage drift: " + "; ".join(
        detail_lines
    )
