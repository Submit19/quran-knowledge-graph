"""LLM-as-judge for eval v2 — 4 dimensions, one judge call per dimension.

Per `docs/PHASE_4_EVAL_PLAN.md` (LLM-as-judge section): scoring each
dimension in isolation reduces anchoring bias. Cost is 4× judge calls
per (question, answer); at 50q production set that's 200 calls per
run, ~$2–5 on Opus.

Each prompt asks for a JSON ``{"score": 0-5, "justification": "..."}``
verdict. In-context examples anchor the scale. The judge runs against
Anthropic by default; a ``stub`` backend is provided for the CI
informational run and for local smoke tests when no key is available.

Calibration against human ratings (Phase 4c) targets Pearson ≥ 0.7
per dimension before judge scores are trusted for gating decisions.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from typing import Any

from .agent_caller import TrajectoryResult


VALID_DIMENSIONS = (
    "citation_accuracy",
    "answer_completeness",
    "tool_path_correctness",
    "framing_appropriateness",
)


# ---------------------------------------------------------------------------
# Dimension prompts.
#
# Each prompt is ~300–500 words with three in-context examples that anchor
# the 0–5 scale. The judge is told to score independently — Phase 4a
# treats each dimension as a separate judge call (no joint scoring) to
# minimise anchoring bias across dimensions.
# ---------------------------------------------------------------------------

_CITATION_ACCURACY_PROMPT = """\
You are an expert evaluator scoring a Quran-research agent's answer on
ONE dimension: citation accuracy. Ignore other quality dimensions
(completeness, tool path, framing) — another grader scores those.

Citation accuracy means: every verse the answer cites (in [S:V] bracket
form) actually supports the claim it appears next to. The agent has
access to Rashad Khalifa's translation; you should accept citations
that align with Khalifa's wording, not require alternative readings.

Score on a 0–5 integer scale.

CALIBRATION ANCHORS

Score 0 — citations are invented (verse doesn't exist), or every cited
verse is unrelated to the claim it's attached to.

Score 2 — some citations are accurate but the most prominent claim
relies on a citation that doesn't support it. Or the agent cites a
correct verse but mischaracterises what it says.

Score 3 — most citations support their claims; one notable mismatch
that a careful reader would catch.

Score 5 — every citation is anchored to a specific claim that the
cited verse genuinely supports. No invented references. No
"citation-for-citation's-sake" decoration.

IN-CONTEXT EXAMPLES

Example A (score 5):
Question: "What does verse 2:255 say?"
Answer: "Verse [2:255] (Ayat al-Kursi) declares that GOD — there is
no other god besides Him, the Living, the Eternal — has no need of
sleep. His knowledge encompasses heavens and earth."
Verdict: {"score": 5, "justification": "Single citation anchored to the
claim it supports; [2:255] is the verse described."}

Example B (score 2):
Question: "Where does the Quran discuss patience?"
Answer: "Patience is a central virtue [2:153], rewarded richly [3:200].
Joseph's story [12:5] is the paradigm of patience."
Verdict: {"score": 2, "justification": "[2:153] and [3:200] are
appropriate, but [12:5] is the verse where Jacob tells Joseph not to
recount his dream — not a patience verse. The most prominent claim
('paradigm of patience') is mis-cited."}

Example C (score 0):
Question: "What does the Quran say about charity?"
Answer: "Charity is commanded [2:999] and rewarded sevenfold [50:50]."
Verdict: {"score": 0, "justification": "[2:999] is invented (sura 2
has 286 verses); [50:50] does not address charity."}

INPUTS

Question: {question}

Agent's answer (citations inline as [S:V]):
{answer}

Citations extracted from the answer: {citations}

CITED VERSE TEXTS (Khalifa translation; may be empty if extraction failed):
{cited_verse_texts}

OUTPUT — JSON only, no other text:
{{"score": <0-5 integer>, "justification": "<one sentence>"}}
"""


_ANSWER_COMPLETENESS_PROMPT = """\
You are an expert evaluator scoring a Quran-research agent's answer on
ONE dimension: answer completeness. Ignore other quality dimensions —
another grader scores those.

Completeness means: does the answer address what the question asked,
including any obvious sub-questions implied by the phrasing? Don't
penalise the answer for missing facts you know from outside the
agent's tools — penalise it for failing to address the question's
scope.

Score on a 0–5 integer scale.

CALIBRATION ANCHORS

Score 0 — answer does not address the question. (E.g. asked about
patience, answer is about prophets.)

Score 2 — answer touches on the question but stops short of the
obvious next step. (E.g. asked "where is Moses mentioned", answer
gives one verse instead of a survey.)

Score 3 — answer addresses the explicit question; obvious implicit
sub-questions are partially handled.

Score 5 — answer fully addresses the explicit question and all
obvious implicit sub-questions, without padding.

IN-CONTEXT EXAMPLES

Example A (score 5):
Question: "What does verse 2:255 say?"
Answer: "[2:255] is Ayat al-Kursi. GOD — there is no other god
besides Him, the Living, the Eternal. He neither slumbers nor sleeps.
His knowledge encompasses the heavens and earth. None can intercede
with Him except as He permits."
Verdict: {"score": 5, "justification": "Full content of the verse
delivered in response to a direct lookup."}

Example B (score 2):
Question: "Where in the Quran is Moses mentioned?"
Answer: "Moses is mentioned in [2:51]."
Verdict: {"score": 2, "justification": "Single citation in answer to a
'where' question that implies survey; Moses is mentioned ~136 times."}

Example C (score 0):
Question: "What does the Quran say about charity?"
Answer: "Prayer is one of the five pillars."
Verdict: {"score": 0, "justification": "Answer is about prayer, not
charity."}

INPUTS

Question: {question}

Agent's answer:
{answer}

OUTPUT — JSON only, no other text:
{{"score": <0-5 integer>, "justification": "<one sentence>"}}
"""


_TOOL_PATH_CORRECTNESS_PROMPT = """\
You are an expert evaluator scoring a Quran-research agent's
retrieval trajectory on ONE dimension: tool path correctness. Ignore
other quality dimensions — another grader scores those.

Tool path correctness means: did the agent call sensible tools in a
sensible order? Not "minimum tools" (efficiency is not the goal here)
but "right tools, no obvious wasted effort". Examples of wasted
effort: calling run_cypher for a trivial lookup that get_verse
handles; semantic_search'ing when an explicit reference is given;
calling the same tool with the same args twice.

The available agent tools include: get_verse, search_keyword,
semantic_search, traverse_topic, hybrid_search, concept_search,
find_path, explore_surah, recall_similar_query, get_verse_words,
query_typed_edges, search_arabic_root, compare_arabic_usage,
lookup_word, explore_root_family, search_semantic_field, lookup_wujuh,
search_morphological_pattern, get_code19_features, run_cypher.

Score on a 0–5 integer scale.

CALIBRATION ANCHORS

Score 0 — no relevant tools called, or many wasted calls (≥3 useless
calls), or the path indicates the agent didn't understand the
question.

Score 2 — the agent eventually reached useful results but only after
2+ obviously wasted calls. Or the right tool was called with wrong
args (e.g. searched for a keyword the question doesn't contain).

Score 3 — sensible path with one minor inefficiency (e.g. a
redundant call near the start).

Score 5 — right tools in a sensible order. No wasted calls. Path
matches what an experienced operator would do.

IN-CONTEXT EXAMPLES

Example A (score 5):
Question: "What does verse 2:255 say?"
Tool calls: [get_verse(verse_id="2:255")]
Verdict: {"score": 5, "justification": "Single targeted lookup for an
explicit reference."}

Example B (score 2):
Question: "What does the Quran say about patience?"
Tool calls: [run_cypher(query="MATCH (v:Verse) RETURN v LIMIT 5"),
run_cypher(query="MATCH (v:Verse) WHERE v.text CONTAINS 'patience'
RETURN v"), semantic_search(query="patience")]
Verdict: {"score": 2, "justification": "Two run_cypher calls before
the right tool (semantic_search) — escape hatch used on a
semantic-search problem."}

Example C (score 0):
Question: "Where is Moses mentioned?"
Tool calls: [get_verse(verse_id="1:1"), get_verse(verse_id="1:2"),
get_verse(verse_id="1:3")]
Verdict: {"score": 0, "justification": "Sequential verse lookups
unrelated to the question; agent never queried for 'Moses'."}

INPUTS

Question: {question}

Tool calls in order (each `name` plus `args_keys`):
{tool_calls}

OUTPUT — JSON only, no other text:
{{"score": <0-5 integer>, "justification": "<one sentence>"}}
"""


_FRAMING_APPROPRIATENESS_PROMPT = """\
You are an expert evaluator scoring a Quran-research agent's answer
on ONE dimension: framing appropriateness. Ignore other quality
dimensions — another grader scores those.

Framing appropriateness means: does the answer hedge correctly when
the data is uncertain? Does it commit when the data is clear?
Over-claiming on a contested question is a failure; refusing to
commit when the verse is unambiguous is also a failure.

The agent uses Rashad Khalifa's translation, which has theological
distinctives (Code-19, rejection of hadith). The answer should
acknowledge when a claim is Khalifa-specific rather than presenting
it as a mainstream view.

Score on a 0–5 integer scale.

CALIBRATION ANCHORS

Score 0 — confidently asserts something the data doesn't support, OR
hedges so heavily that no claim is made when the data is clear.

Score 2 — minor over-claim or undue hedging on one notable claim.

Score 3 — framing is mostly right; one place where the confidence
level doesn't quite match the evidence.

Score 5 — every claim's confidence matches its evidence. Admits when
the data is silent or contested; commits when the data is clear.

IN-CONTEXT EXAMPLES

Example A (score 5):
Question: "Does the Quran explicitly mention the year Muhammad died?"
Answer: "No — the Quran does not state any year. The traditional
date (632 CE) comes from external Islamic sources, not the Quranic
text."
Verdict: {"score": 5, "justification": "Correctly admits the Quran is
silent on this point; doesn't pad with hadith material."}

Example B (score 2):
Question: "Is alcohol forbidden?"
Answer: "Alcohol is absolutely forbidden under all conditions [5:90]."
Verdict: {"score": 2, "justification": "Over-claims; [5:90] declares
intoxicants an abomination but the Quranic position on degrees and
contexts is more nuanced than 'all conditions'."}

Example C (score 0):
Question: "What does verse 2:255 say?"
Answer: "Some scholars believe 2:255 might possibly relate to God's
sovereignty, though interpretations vary widely."
Verdict: {"score": 0, "justification": "The verse is a direct
declaration of God's attributes — wallpaper hedging on an unambiguous
text."}

INPUTS

Question: {question}

Agent's answer:
{answer}

OUTPUT — JSON only, no other text:
{{"score": <0-5 integer>, "justification": "<one sentence>"}}
"""


DIMENSION_PROMPTS: dict[str, str] = {
    "citation_accuracy": _CITATION_ACCURACY_PROMPT,
    "answer_completeness": _ANSWER_COMPLETENESS_PROMPT,
    "tool_path_correctness": _TOOL_PATH_CORRECTNESS_PROMPT,
    "framing_appropriateness": _FRAMING_APPROPRIATENESS_PROMPT,
}


# ---------------------------------------------------------------------------
# Prompt assembly helpers
# ---------------------------------------------------------------------------


def _render_prompt(
    *,
    dimension: str,
    question: dict,
    trajectory: TrajectoryResult,
    cited_verse_texts: dict[str, str] | None = None,
) -> str:
    template = DIMENSION_PROMPTS[dimension]
    fields: dict[str, str] = {
        "question": question.get("question", ""),
        "answer": trajectory.answer_text or "(empty)",
        "citations": ", ".join(trajectory.citations) or "(none)",
        "cited_verse_texts": (
            "\n".join(f"  [{vid}]: {text}" for vid, text in (cited_verse_texts or {}).items())
            or "(verse texts unavailable to judge)"
        ),
        "tool_calls": (
            "\n".join(
                f"  {i + 1}. {tc.get('name')} ({tc.get('args_keys') or 'no args'})"
                for i, tc in enumerate(trajectory.tool_calls)
            )
            or "(no tool calls)"
        ),
    }
    # Defensive .format: prompts contain literal "{" inside JSON examples
    # which we've doubled to "{{" already. Use str.replace for the few
    # named placeholders to avoid the surprise.
    rendered = template
    for key, value in fields.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


# ---------------------------------------------------------------------------
# Score parsing
# ---------------------------------------------------------------------------

_JSON_OBJECT_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def parse_judge_response(raw: str) -> dict[str, Any]:
    """Extract ``{"score": int, "justification": str}`` from a raw LLM response.

    The judge is asked to return JSON only; in practice models sometimes
    wrap it in prose. We pull the first JSON-shaped block and validate.
    """
    candidates = _JSON_OBJECT_RE.findall(raw)
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        score = data.get("score")
        if isinstance(score, (int, float)) and 0 <= score <= 5:
            return {
                "score": int(score),
                "justification": str(data.get("justification", "")),
            }
    # Last resort: regex out an integer in 0–5 range so we don't fail the run.
    fallback_score = re.search(r"\b([0-5])\b", raw)
    if fallback_score:
        return {
            "score": int(fallback_score.group(1)),
            "justification": "(judge response unparseable; score extracted by regex)",
        }
    return {
        "score": 0,
        "justification": "(judge response unparseable; defaulted to 0)",
    }


# ---------------------------------------------------------------------------
# Public scoring entry
# ---------------------------------------------------------------------------


def score_dimension(
    *,
    dimension: str,
    question: dict,
    trajectory: TrajectoryResult,
    client: Any,
    model: str = "claude-opus-4-7",
    cited_verse_texts: dict[str, str] | None = None,
    max_tokens: int = 256,
) -> dict[str, Any]:
    """Call the judge LLM for one dimension and parse the result.

    Args:
        dimension: one of ``VALID_DIMENSIONS``.
        question: the YAML question dict.
        trajectory: the agent's run output.
        client: Anthropic-style client with ``.messages.create(...)``.
        model: judge model id (Opus 4.x or Sonnet 4.x recommended).
        cited_verse_texts: optional map of verse_id -> text, included
            in the prompt so the judge sees what's actually cited
            rather than only the bracket references.
        max_tokens: cap on judge response. 256 is comfortable for a
            JSON object with one-sentence justification.

    Returns:
        ``{"score": int 0-5, "justification": str}``.
    """
    if dimension not in VALID_DIMENSIONS:
        raise ValueError(f"unknown dimension: {dimension!r}")

    prompt = _render_prompt(
        dimension=dimension,
        question=question,
        trajectory=trajectory,
        cited_verse_texts=cited_verse_texts,
    )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = _extract_text(response)
    return parse_judge_response(raw)


def _extract_text(response: Any) -> str:
    """Pull the text out of an Anthropic Message response, defensively."""
    content = getattr(response, "content", None)
    if isinstance(content, list):
        parts = []
        for block in content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                parts.append(text)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
        return "".join(parts)
    if isinstance(content, str):
        return content
    return str(response)


# ---------------------------------------------------------------------------
# Factory: make a judge_caller bound to a backend
# ---------------------------------------------------------------------------


def make_judge_caller(
    *,
    backend: str = "anthropic",
    model: str = "claude-opus-4-7",
) -> Callable[..., dict[str, Any]]:
    """Build a judge_caller for the runner.

    Backends:
        * ``anthropic``: real judge calls. Requires ``ANTHROPIC_API_KEY``.
        * ``stub``: returns ``{"score": 0, "justification": "stub backend"}``
          for every dimension. Used in CI when no key is configured and
          in smoke tests.

    The returned callable is keyword-only: ``(dimension, question, trajectory)``.
    Bind extra context (e.g. ``cited_verse_texts``) via closures if needed.
    """
    if backend == "stub" or model == "none":
        return _make_stub_caller()

    if backend != "anthropic":
        raise ValueError(f"unknown judge backend: {backend!r}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Soft-degrade in unconfigured environments. The CI workflow
        # surfaces a clear message rather than failing on a missing
        # optional secret.
        return _make_stub_caller(reason="ANTHROPIC_API_KEY not set")

    import anthropic  # imported lazily so unit tests don't need the sdk

    client = anthropic.Anthropic(api_key=api_key)

    def _caller(
        *,
        dimension: str,
        question: dict,
        trajectory: TrajectoryResult,
        cited_verse_texts: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return score_dimension(
            dimension=dimension,
            question=question,
            trajectory=trajectory,
            client=client,
            model=model,
            cited_verse_texts=cited_verse_texts,
        )

    return _caller


def _make_stub_caller(reason: str = "stub backend") -> Callable[..., dict[str, Any]]:
    def _caller(
        *,
        dimension: str,
        question: dict,
        trajectory: TrajectoryResult,
        cited_verse_texts: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "score": 0,
            "justification": f"({reason})",
            "judge_skipped": True,
        }

    return _caller
