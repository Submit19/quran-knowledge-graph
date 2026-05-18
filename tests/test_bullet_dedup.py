"""Regression: post-stream BulletDedup suppresses verbatim verse-explanation
duplicates without disturbing clean answers.

The 2026-05-17 baseline (`data/research/repetition_bug_baseline_2026-05-17/
REPORT.md`) measured a 31% verbatim verse-explanation duplicate rate on
qwen3:14b for thematic ABSTRACT questions. Every flagged duplicate was
character-identical on the first ~150 chars of the explanation, so the
strict-identity dedup in :mod:`bullet_dedup` should catch every one and
leave clean answers byte-for-byte unchanged. These tests pin both
properties.

Fixtures in ``tests/fixtures/dedup/`` are the concatenated text events
extracted from three real BUG_VERBATIM SSE runs:

* ``q_003`` — gratitude, MD-table bullet shape, dup verse 2:172.
* ``q_007`` — repentance, dash-bullet shape, multiple dup verses
  (4:17, 3:89, 5:39, 66:8, 58:13).
* ``q_018`` — Satan whisperings, dup verse 23:97 across 3 sections.
"""

from __future__ import annotations

import pathlib

import pytest

from bullet_dedup import BulletDedup

FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "dedup"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_empty_answer_returns_empty_no_suppressions():
    cleaned, suppressed = BulletDedup().filter_text("")
    assert cleaned == ""
    assert suppressed == []


def test_clean_answer_passes_through_byte_for_byte():
    """Backwards-compat guarantee: answers without verbatim dups must be untouched."""
    clean_answer = (
        "## 1. Charity in the Quran\n"
        "\n"
        '- **[2:177]** – *"Righteousness is not turning your faces toward '
        'the east or the west; righteous are those who believe in GOD ..."*\n'
        '- **[2:271]** – *"If you declare your charities, they are still good; '
        'but if you keep them secret and give them to the poor, it is better ..."*\n'
        "\n"
        "## 2. Charity as ongoing duty\n"
        "\n"
        '- **[9:103]** – *"Take from their money a charity to purify them and '
        'sanctify them ..."*\n'
    )
    cleaned, suppressed = BulletDedup().filter_text(clean_answer)
    assert cleaned == clean_answer, "clean answer must round-trip unchanged"
    assert suppressed == []


def test_q003_single_table_row_duplicate_is_suppressed():
    """q_003 (gratitude): baseline flagged 2:172 verbatim across sections 0 and 4.

    The fixture is a real Ollama answer that triggered BUG_VERBATIM. After
    dedup, every remaining bullet line is unique on (verse_id, first
    150 chars), and 2:172 is in the suppression list.
    """
    text = _load("q_003.answer.txt")
    cleaned, suppressed = BulletDedup().filter_text(text)

    assert len(cleaned) < len(text), "expected at least one bullet to be dropped"
    assert "2:172" in suppressed, (
        "baseline-flagged dup verse 2:172 must appear in suppressed list"
    )

    # Idempotency: re-running dedup over cleaned output should suppress nothing.
    cleaned_twice, suppressed_twice = BulletDedup().filter_text(cleaned)
    assert cleaned_twice == cleaned
    assert suppressed_twice == []


def test_q007_multiple_verbatim_duplicates_are_all_suppressed():
    """q_007 (repentance): baseline flagged 4:17, 3:89, 5:39, 66:8, 58:13.

    The verbatim-match pairs span at least these five verses. After dedup
    none of them have two bullet lines with the same first-150-chars
    explanation.
    """
    text = _load("q_007.answer.txt")
    cleaned, suppressed = BulletDedup().filter_text(text)

    # The baseline `duplicate_pairs` for q_007 lists verbatim pairs on
    # 3:89, 5:39, 58:13, 66:8 (and a verbatim 4:17 pair too); at least
    # four of these distinct verses should surface in `suppressed`.
    expected_dup_verses = {"3:89", "5:39", "58:13", "66:8", "4:17"}
    assert len(expected_dup_verses & set(suppressed)) >= 4, (
        f"expected ≥4 of {expected_dup_verses} in suppressed, got {suppressed!r}"
    )

    # And cleaned output must itself be dedup-stable.
    cleaned_twice, suppressed_twice = BulletDedup().filter_text(cleaned)
    assert cleaned_twice == cleaned
    assert suppressed_twice == []


def test_same_verse_different_angle_is_preserved():
    """Triangulation: two bullets citing the same verse with DIFFERENT
    explanations must both survive — strict-identity dedup must not
    collapse legitimate re-use under a new angle.
    """
    angles_answer = (
        "## 1. Acceptance\n"
        '- **[4:17]** – *"Repentance is acceptable by GOD from those who '
        "fall in sin out of ignorance, then repent immediately thereafter. "
        'GOD redeems them."*\n'
        "\n"
        "## 2. Conditions\n"
        "- **[4:17]** – Note that the same verse stresses the immediacy of "
        'the repentance, not merely its occurrence — *"...repent IMMEDIATELY '
        'thereafter"* qualifies the timing of the act.\n'
        "\n"
        "## 3. Mercy\n"
        "- **[4:17]** – Read with 4:18, the contrast clarifies who is "
        "outside acceptance: deathbed repentance is not the same as "
        "immediate repentance.\n"
    )
    cleaned, suppressed = BulletDedup().filter_text(angles_answer)
    assert cleaned == angles_answer, (
        "three different angles on 4:17 must all survive — only verbatim "
        "first-150-char matches may be suppressed"
    )
    assert suppressed == []


@pytest.mark.parametrize(
    "fixture_name", ["q_003.answer.txt", "q_007.answer.txt", "q_018.answer.txt"]
)
def test_cleaned_output_has_no_remaining_verbatim_duplicates(fixture_name: str):
    """Property: after one pass of dedup, no two bullet lines share the
    same (verse_id, first-150-chars) signature in the cleaned output.
    """
    from bullet_dedup import _BULLET_LINE

    text = _load(fixture_name)
    cleaned, _ = BulletDedup().filter_text(text)

    seen: set[tuple[str, str]] = set()
    for line in cleaned.split("\n"):
        m = _BULLET_LINE.match(line)
        if m is None:
            continue
        key = (m.group("verse"), (m.group("rest") or "").strip()[:150])
        assert key not in seen, (
            f"leftover duplicate in {fixture_name}: verse={key[0]} line={line[:120]!r}"
        )
        seen.add(key)
