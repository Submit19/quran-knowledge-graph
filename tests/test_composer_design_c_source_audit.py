"""Executable spec for composer-rewire design §c — Output-validation layer.

Design doc: data/research/composer_rewire/02_design_proposal_2026-05-28.md §c.

xfail(strict=True) regression-guards for the runtime output gate: the
no-surface scrub on 9:128/9:129 and the provenance audit that catches
hadith-derived (and any other unauthorized-source) claims.

Today: source_audit does not exist → ImportError inside the body → expected
xfail. When implemented → XPASS → strict failure → remove marker in the
implementing commit.

Intended API (the spec):

    from source_audit import scrub_no_surface, audit_answer
    clean_text, violations = scrub_no_surface(text)
    # violations -> list[{"location": "bracket"|"prose", "match": str}]
    # clean_text -> text with every 9:128 / 9:129 surface removed/neutralised
"""

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="design §c: runtime no-surface scrub not implemented — "
    "check_no_surface_rule.py is offline-only and unwired. "
    "See 02_design_proposal_2026-05-28.md §c.",
)
def test_composer_never_surfaces_9_128_129():
    """§c: the output gate must catch and remove every 9:128/9:129 surface —
    bracket form `[9:128]` AND prose form `9:129` — from user-facing text.

    The corpus may CONTAIN these references (Appendix 24); the composer's
    OUTPUT may not. This is the runtime promotion of
    scripts/check_no_surface_rule.py, applied to the answer the user sees.
    A surface is a HARD FAIL: never shipped, never cached.
    """
    from source_audit import scrub_no_surface

    dirty = (
        "Khalifa demonstrated that two verses were later additions; "
        "specifically [9:128] and the following 9:129 break the count of 19."
    )

    clean_text, violations = scrub_no_surface(dirty)

    assert len(violations) >= 2, (
        "design §c NOT met: scrub_no_surface missed a 9:128/9:129 surface. "
        f"Expected >=2 violations (bracket + prose), saw {violations!r}."
    )
    assert "[9:128]" not in clean_text and "9:129" not in clean_text, (
        "design §c NOT met: a 9:128/9:129 reference survived into the scrubbed "
        f"output text: {clean_text!r}. This is a HARD FAIL — these references "
        "must never reach the user (binding rule + COMPOSER_CONSTRAINTS.md)."
    )


@pytest.mark.xfail(
    strict=True,
    reason="design §c: provenance audit not implemented — a hadith-derived "
    "claim consistent with a verse still passes (leak L5: the existing "
    "verifier is provenance-blind). See 02_design_proposal_2026-05-28.md §c.",
)
def test_composer_blocks_hadith_reference():
    """§c: a claim sourced from hadith must be labeled `unsupported` even when
    it is broadly consistent with a retrieved verse.

    This is the provenance-blind gap (L5): NLI-against-verses alone passes a
    hadith claim that happens not to contradict scripture. The source audit
    must classify by *where the claim came from* (retrieved verse / retrieved
    corpus / neither), so an unsupported hadith framing is caught and routed to
    revise-or-abstain — consistent with Khalifa's rejection of hadith as a
    religious source.
    """
    from source_audit import audit_answer

    answer = (
        "Prayer is prescribed for believers [2:43]. "
        "A well-known hadith in Sahih Bukhari records that the Prophet said "
        "prayer is the pillar of religion."
    )
    retrieved_verses = {
        "2:43": {
            "text": "You shall observe the Contact Prayers (Salat) and "
            "give the obligatory charity (Zakat), and bow down "
            "with those who bow down."
        }
    }
    retrieved_corpus_chunks = []  # no Khalifa-corpus chunk supports the hadith claim

    result = audit_answer(answer, retrieved_verses, retrieved_corpus_chunks)

    assert not result.passed, (
        "design §c NOT met: the audit passed an answer that cites a hadith "
        "from Sahih Bukhari. Hadith is an excluded source under the "
        "Khalifa-only rule; the claim has no retrieved verse/corpus backing "
        "and must fail the gate."
    )
    assert any(
        "hadith" in c.lower() or "bukhari" in c.lower()
        for c in result.unsupported_claims
    ), (
        "design §c NOT met: the hadith-derived claim was not isolated as "
        "unsupported, so the revise/abstain loop cannot remove it. A "
        "verse-only NLI check (the current verifier) would wrongly pass it "
        "because it does not contradict [2:43] — that is exactly leak L5."
    )
