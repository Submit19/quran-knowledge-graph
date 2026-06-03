"""Executable spec for composer-rewire design §b — Composition-constraint layer.

Design doc: data/research/composer_rewire/02_design_proposal_2026-05-28.md §b.

xfail(strict=True) regression-guards for the not-yet-built source audit that
enforces the context-only composition contract ("no source chunk, no claim").

Today: source_audit does not exist → ImportError inside the body → expected
xfail. When implemented: the assertions run for real → XPASS → strict failure
→ implementer removes the marker in the implementing commit.

The intended API (this IS the spec):

    from source_audit import audit_answer
    result = audit_answer(
        answer_text: str,
        retrieved_verses: dict,            # {verseId: {"text": ...}}
        retrieved_corpus_chunks: list[dict],  # [{chunk_id, title, text}, ...]
    )
    # result.claims               -> list[{"text", "provenance", "evidence_id"}]
    #   provenance in {"verse-grounded", "corpus-grounded", "unsupported"}
    # result.unsupported_claims   -> list[str]  (spans with no retrieved source)
    # result.passed               -> bool       (True iff no unsupported claims
    #                                            and no no-surface violations)
"""

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="design §b: source_audit.audit_answer not implemented — composer "
    "cannot yet flag claims with no retrieved source (leak L2). "
    "See 02_design_proposal_2026-05-28.md §b.",
)
def test_composer_rejects_non_source_claim():
    """§b: a claim grounded in neither a retrieved verse nor a Khalifa-corpus
    chunk must be labeled `unsupported` and fail the audit.

    This is the structural block on training-knowledge fill: the composer is
    handed verses + corpus chunks and may assert ONLY what they support.
    """
    from source_audit import audit_answer

    answer = (
        "Charity purifies wealth, as stated in [2:261]. "
        "Fasting was practiced by all ancient civilizations across the world."
    )
    retrieved_verses = {
        "2:261": {
            "text": "The example of those who spend their money in the "
            "cause of GOD is that of a grain that produces seven "
            "spikes, with a hundred grains in each spike."
        }
    }
    retrieved_corpus_chunks = []  # nothing supports the second sentence

    result = audit_answer(answer, retrieved_verses, retrieved_corpus_chunks)

    assert not result.passed, (
        "design §b NOT met: the audit passed an answer containing an "
        "unsupported claim ('Fasting was practiced by all ancient "
        "civilizations…') that has no retrieved verse or corpus support — "
        "exactly the training-knowledge fill the Khalifa-only rule forbids."
    )
    assert any("ancient civilizations" in c for c in result.unsupported_claims), (
        "design §b NOT met: the unsupported claim was not isolated in "
        "result.unsupported_claims, so the revise/abstain loop has nothing to "
        "act on."
    )


@pytest.mark.xfail(
    strict=True,
    reason="design §b: per-claim provenance labelling not implemented — "
    "verse- and corpus-grounded claims are not yet distinguished from "
    "unsupported ones. See 02_design_proposal_2026-05-28.md §b/§c.",
)
def test_composer_cites_every_claim():
    """§b: every assertable claim must trace to a verse OR a Khalifa-corpus
    chunk; a fully-grounded answer passes with zero unsupported claims.

    Mirror image of the rejection test: an answer whose every claim is backed
    by retrieved material must be accepted, and each claim must carry a
    concrete provenance label (not just an overall verdict).
    """
    from source_audit import audit_answer

    answer = (
        "God's mercy encompasses all things, as declared in [7:156]. "
        "Khalifa explained that the mathematical structure of the Quran is "
        "based on the number nineteen."
    )
    retrieved_verses = {"7:156": {"text": "My mercy encompasses all things."}}
    retrieved_corpus_chunks = [
        {
            "chunk_id": "appendix_01#3",
            "title": "Appendix 1",
            "text": "The Quran's mathematical composition is based on the number "
            "nineteen, a common denominator throughout.",
        }
    ]

    result = audit_answer(answer, retrieved_verses, retrieved_corpus_chunks)

    assert result.passed, (
        "design §b NOT met: a fully-grounded answer (one verse-backed claim, "
        "one corpus-backed claim) did not pass the audit."
    )
    provenances = {c["provenance"] for c in result.claims}
    assert provenances <= {"verse-grounded", "corpus-grounded"}, (
        "design §b NOT met: a grounded answer produced a non-grounded "
        f"provenance label; saw {provenances}. Every claim must be either "
        "verse-grounded or corpus-grounded."
    )
    assert result.unsupported_claims == [], (
        "design §b NOT met: a fully-grounded answer reported unsupported "
        f"claims: {result.unsupported_claims}."
    )
