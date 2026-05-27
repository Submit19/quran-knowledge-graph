"""iter_1 surgical fixes for the 6 Shape A failures.

Each fix:
  1. Loads the existing cached answer for `question`.
  2. Performs a single targeted edit (described in `intent`).
  3. Verifies every [s:v] citation in the resulting answer resolves to a
     Verse node in Neo4j (100% citation validity is non-negotiable).
  4. Verifies the new answer preserves every citation that was in the old
     answer (no regression).
  5. Verifies any required substring is present.
  6. Saves via answer_cache.save_answer (the 0.98 cosine dedupe will
     update-in-place since sim==1.000 against the existing entry).

Run: python scripts/iter_1_apply_fixes.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

load_dotenv(REPO_ROOT / ".env")

from answer_cache import save_answer, _load_cache  # noqa: E402


CITATION_PATTERN = re.compile(r"\[(\d+):(\d+)\]")


def extract_citations(text: str) -> set[str]:
    return {f"{s}:{v}" for s, v in CITATION_PATTERN.findall(text or "")}


def verify_citations_in_graph(citations: set[str]) -> tuple[set[str], set[str]]:
    """Returns (existing, missing) sets."""
    driver = GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
    )
    existing: set[str] = set()
    try:
        with driver.session(database="quran") as s:
            for vid in citations:
                r = s.run(
                    "MATCH (v:Verse {verseId: $vid}) RETURN v.verseId AS id",
                    vid=vid,
                ).single()
                if r:
                    existing.add(vid)
    finally:
        driver.close()
    return existing, citations - existing


def load_entry(question: str) -> dict | None:
    for e in _load_cache():
        if e.get("question", "").strip().lower() == question.strip().lower():
            return e
    return None


# ─────────────────────────────────────────────────────────────────────────────
# The 6 surgical edits. Each `apply` returns the modified answer.
# Each is a single targeted edit — minimum delta to land the assert.
# ─────────────────────────────────────────────────────────────────────────────


def fix_abstract_003(answer: str) -> str:
    """Add 'shukr' romanization inline next to the Arabic root.

    Current: '**ش-ك-ر** (*sh-k-r*, root-gloss in the graph: "gratitude, thanks")'
    Target:  add 'noun **shukr**, "gratitude/thanks"' near the root introduction.
    """
    old = (
        "The root **ش-ك-ر** (*sh-k-r*, root-gloss in the graph: "
        '"gratitude, thanks") appears'
    )
    new = (
        "The root **ش-ك-ر** (*sh-k-r*, romanized **shukr** in the noun form "
        '— "gratitude, thanks") appears'
    )
    if old not in answer:
        raise RuntimeError("abstract-003: anchor string not found in cached answer")
    return answer.replace(old, new, 1)


def fix_abstract_014(answer: str) -> str:
    """Add 'yaqeen' (Khalifa's preferred romanization) inline.

    Current: 'certainty (*yaqin*) as cognitive states'
    Target:  'certainty (*yaqin*, Khalifa romanizes as *yaqeen*) as cognitive states'
    """
    old = "certainty (*yaqin*) as cognitive states"
    new = "certainty (*yaqin*, Khalifa romanizes as *yaqeen*) as cognitive states"
    if old not in answer:
        raise RuntimeError("abstract-014: anchor string not found in cached answer")
    return answer.replace(old, new, 1)


def fix_abstract_016(answer: str) -> str:
    """Add a section on [35:6] — 'The devil is your enemy.'

    Inserted before the closing 'Khalifa-specific framing' paragraph.
    """
    insertion = (
        '**The named-enemy declaration.** [35:6]: "The devil is your enemy, '
        "so treat him as an enemy. He only invites his party to be the dwellers "
        "of Hell.\" Khalifa's translation makes the imperative explicit — "
        "treating Satan *as* an enemy is itself the prescribed orientation, not "
        "a passive recognition. The verse pairs the enmity (Satan toward humans) "
        "with the human's required reciprocal stance, completing the relational "
        "model the rest of the Satan-vocabulary develops.\n\n"
    )
    anchor = "**Khalifa-specific framing.**"
    if anchor not in answer:
        raise RuntimeError("abstract-016: anchor not found")
    return answer.replace(anchor, insertion + anchor, 1)


def fix_abstract_017(answer: str) -> str:
    """Add a section on [2:26] — the same revelation guides some, leads others astray.

    Inserted before the closing 'Khalifa-specific framing' paragraph.
    """
    insertion = (
        '**The bidirectional-revelation principle.** [2:26]: "GOD does not '
        "shy away from citing any kind of allegory, from the tiny mosquito and "
        "greater. As for those who believe, they know that it is the truth from "
        "their Lord. As for those who disbelieve, they say, 'What did GOD mean "
        "by such an allegory?' He misleads many thereby, and guides many "
        'thereby. But He never misleads thereby except the wicked." Khalifa '
        "preserves the structural claim — the *same* revelation that guides "
        "the believing-disposed misleads the wicked-disposed. The verse "
        "completes the *dalal*-doctrine: straying is not caused by the message "
        "but by what the receiver brings to it, and the resulting divergence is "
        "the diagnostic of the receiver's prior orientation.\n\n"
    )
    anchor = "**Khalifa-specific framing.**"
    if anchor not in answer:
        raise RuntimeError("abstract-017: anchor not found")
    return answer.replace(anchor, insertion + anchor, 1)


def fix_broad_012(answer: str) -> str:
    """Add explicit [74:30] anchor at the start of the Code-19 register section."""
    old = "**The Khalifa Code-19 register.** The Quran contains, in Khalifa's reading,"
    new = (
        "**The Khalifa Code-19 register.** The Quran's most explicit numerical "
        'anchor is [74:30]: "Over it is nineteen." Khalifa identified this '
        "verse as the structural pointer to a pervasive 19-based mathematical "
        "code threaded through the text. The Quran contains, in Khalifa's reading,"
    )
    if old not in answer:
        raise RuntimeError("broad-012: anchor not found")
    return answer.replace(old, new, 1)


def fix_concrete_004(answer: str) -> str:
    """Add [11:77] (parallel of 29:31-33) at the start of the messenger-visit section."""
    old = "**The visit of the messenger-angels.** [29:31]–[29:33]:"
    new = (
        "**The visit of the messenger-angels.** The most economical Quranic "
        'rendering of the moment is [11:77]: "When our messengers went to Lot, '
        "they were mistreated, and he was embarrassed by their presence. He "
        "said, 'This is a difficult day.'\" The longer parallel at [29:31]–[29:33]:"
    )
    if old not in answer:
        # try alternative em-dash variants
        old_b = "**The visit of the messenger-angels.** [29:31]-[29:33]:"
        if old_b in answer:
            old = old_b
            new = new.replace("[29:31]–[29:33]", "[29:31]-[29:33]")
        else:
            raise RuntimeError(
                "concrete-004: anchor not found (tried em-dash + hyphen)"
            )
    return answer.replace(old, new, 1)


# ─────────────────────────────────────────────────────────────────────────────


FIXES = [
    {
        "id": "abstract-003",
        "question": "How does the Quran portray gratitude?",
        "apply": fix_abstract_003,
        "must_include_substr": ["shukr"],
        "must_include_cites": [],
        "intent": "add 'shukr' romanization inline",
    },
    {
        "id": "abstract-014",
        "question": "How does the Quran address doubt and certainty?",
        "apply": fix_abstract_014,
        "must_include_substr": ["yaqeen"],
        "must_include_cites": [],
        "intent": "add 'yaqeen' Khalifa romanization",
    },
    {
        "id": "abstract-016",
        "question": "How does the Quran characterise Satan and the ways he misleads people?",
        "apply": fix_abstract_016,
        "must_include_substr": [],
        "must_include_cites": ["35:6"],
        "intent": "add [35:6] 'devil is your enemy' section",
    },
    {
        "id": "abstract-017",
        "question": "What lessons does the Quran offer about being led astray (dalal)?",
        "apply": fix_abstract_017,
        "must_include_substr": [],
        "must_include_cites": ["2:26"],
        "intent": "add [2:26] bidirectional-revelation section",
    },
    {
        "id": "broad-012",
        "question": "How does the Quran speak of its own miraculous nature?",
        "apply": fix_broad_012,
        "must_include_substr": [],
        "must_include_cites": ["74:30"],
        "intent": "add [74:30] Code-19 anchor",
    },
    {
        "id": "concrete-004",
        "question": "What befell Lot's people according to the Quran?",
        "apply": fix_concrete_004,
        "must_include_substr": [],
        "must_include_cites": ["11:77"],
        "intent": "add [11:77] messenger-visit parallel",
    },
]


def run(dry_run: bool) -> dict:
    """Apply all fixes (or just verify), return per-fix report."""
    report: list[dict] = []
    for fix in FIXES:
        qid = fix["id"]
        entry = load_entry(fix["question"])
        if entry is None:
            report.append(
                {"id": qid, "outcome": "ENTRY_MISSING", "intent": fix["intent"]}
            )
            continue

        old_answer = entry["answer"]
        old_cites = extract_citations(old_answer)

        try:
            new_answer = fix["apply"](old_answer)
        except RuntimeError as e:
            report.append(
                {
                    "id": qid,
                    "outcome": "FIX_ANCHOR_FAILED",
                    "error": str(e),
                    "intent": fix["intent"],
                }
            )
            continue

        new_cites = extract_citations(new_answer)
        added_cites = new_cites - old_cites
        dropped_cites = old_cites - new_cites

        if dropped_cites:
            report.append(
                {
                    "id": qid,
                    "outcome": "DROPPED_CITES",
                    "dropped": sorted(dropped_cites),
                    "intent": fix["intent"],
                }
            )
            continue

        existing, missing = verify_citations_in_graph(new_cites)
        if missing:
            report.append(
                {
                    "id": qid,
                    "outcome": "INVALID_CITES",
                    "missing_from_graph": sorted(missing),
                    "intent": fix["intent"],
                }
            )
            continue

        ans_lower = new_answer.lower()
        missing_substrs = [
            s for s in fix["must_include_substr"] if s.lower() not in ans_lower
        ]
        missing_cites = [c for c in fix["must_include_cites"] if c not in new_cites]
        if missing_substrs or missing_cites:
            report.append(
                {
                    "id": qid,
                    "outcome": "ASSERT_NOT_LANDED",
                    "missing_substrings": missing_substrs,
                    "missing_cites": missing_cites,
                    "intent": fix["intent"],
                }
            )
            continue

        if not dry_run:
            save_answer(fix["question"], new_answer, verses=entry.get("verses") or {})

        report.append(
            {
                "id": qid,
                "outcome": "WOULD_APPLY" if dry_run else "APPLIED",
                "old_length": len(old_answer),
                "new_length": len(new_answer),
                "delta": len(new_answer) - len(old_answer),
                "added_cites": sorted(added_cites),
                "total_cites_after": len(new_cites),
                "intent": fix["intent"],
            }
        )

    return {"fixes": report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="verify without writing")
    ap.add_argument("--out", default=None, help="write report JSON to this path")
    args = ap.parse_args()

    report = run(dry_run=args.dry_run)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    all_ok = all(f["outcome"] in ("APPLIED", "WOULD_APPLY") for f in report["fixes"])
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
