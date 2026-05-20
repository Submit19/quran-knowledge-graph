"""
Pass 3 — additive metadata enrichment of data/answer_cache.json.

For every cache entry, attach the following fields without modifying any
existing field:
  - quality_score        (from Pass 1)
  - cite_count           (from Pass 1)
  - has_arabic           (from Pass 1)
  - model_estimated      (opus | qwen3-like | haiku-like | unknown)
  - model_confidence     (0..1)

Heuristic for model_estimated:
  - "opus":        cite_count >= 10  AND  answer_len >= 6000  AND  not repetitive
                   confidence rises if Arabic present and/or Khalifa-distinctive
                   framings show up (Code-19, Messenger of the Covenant,
                   muqatta'at, hadith-rejection language).
  - "qwen3-like":  has_repetition == True. Older Qwen3 / Ollama outputs
                   commonly repeat sentences verbatim under generation
                   pressure; this is the strongest single signal.
  - "haiku-like":  answer_len < 500 AND cite_count <= 3. Short, shallow.
  - "unknown":     anything that doesn't fit cleanly. confidence = 0.

Reads the Pass-1 audit sidecar to avoid recomputing per-entry scores.
Writes via answer_cache._save_cache to keep the on-disk format consistent.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402

CACHE_FILE = ROOT / "data" / "answer_cache.json"
AUDIT_FILE = ROOT / "data" / "research" / "cache_quality_audit_2026-05-21.json"

KHALIFA_PATTERNS = [
    re.compile(r"\bcode[- ]?19\b", re.IGNORECASE),
    re.compile(r"\brashad khalifa\b", re.IGNORECASE),
    re.compile(r"\bsubmitter[s]?\b", re.IGNORECASE),
    re.compile(r"\bmessenger of the covenant\b", re.IGNORECASE),
    re.compile(r"\bmuqatta", re.IGNORECASE),
    re.compile(r"\b(?:numerical miracle|19[- ]based)\b", re.IGNORECASE),
    re.compile(r"\bfinal testament\b", re.IGNORECASE),
]


def khalifa_signal(answer: str) -> int:
    """How many distinct Khalifa-distinctive patterns fire."""
    return sum(1 for rx in KHALIFA_PATTERNS if rx.search(answer))


def estimate_model(
    answer: str,
    answer_len: int,
    cite_count: int,
    has_repetition: bool,
    has_arabic: bool,
) -> tuple[str, float]:
    # Strongest single negative signal first — repetition.
    if has_repetition:
        # Weaker open models (Qwen3, some Ollama defaults) repeat sentences
        # under generation pressure. Confidence modest because Opus *can*
        # occasionally repeat in long enumerations.
        return "qwen3-like", 0.6

    # Short + shallow → haiku-tier.
    if answer_len < 500 and cite_count <= 3:
        return "haiku-like", 0.55

    # Opus signature: long, multi-cited, no repetition, ideally Khalifa-aware.
    if answer_len >= 6000 and cite_count >= 10:
        k = khalifa_signal(answer)
        # Base 0.65; +0.10 per Khalifa pattern up to 3, +0.05 if Arabic.
        conf = 0.65 + min(k, 3) * 0.10 + (0.05 if has_arabic else 0.0)
        return "opus", min(conf, 0.95)

    # Mid-length, mid-cite — could be any of several models. Be honest.
    return "unknown", 0.0


def main() -> int:
    if not AUDIT_FILE.exists():
        print(
            "Pass 1 sidecar missing — run scripts/audit_cache_quality.py first.",
            file=sys.stderr,
        )
        return 2

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))["scored"]
    score_by_q: dict[str, dict] = {a["question"]: a for a in audit}

    print(f"Cache entries: {len(cache)}")
    print(f"Audit rows:    {len(audit)}")

    original_field_set: set[str] = set()
    for rec in cache:
        original_field_set.update(rec.keys())
    print(f"Original fields: {sorted(original_field_set)}")

    enriched = 0
    missing_audit = 0
    new_fields = [
        "quality_score",
        "cite_count",
        "has_arabic",
        "model_estimated",
        "model_confidence",
    ]
    by_model: dict[str, int] = {}

    for rec in cache:
        q = rec.get("question", "")
        audit_row = score_by_q.get(q)
        if not audit_row:
            missing_audit += 1
            # Be defensive: skip rather than write None.
            continue

        # Compute model estimate fresh — needs full answer text, not just score.
        answer = rec.get("answer", "") or ""
        model, conf = estimate_model(
            answer,
            audit_row["answer_len"],
            audit_row["cite_count"],
            audit_row["has_repetition"],
            audit_row["has_arabic"],
        )

        # Additive only: write only if not already present.
        rec.setdefault("quality_score", audit_row["quality_score"])
        rec.setdefault("cite_count", audit_row["cite_count"])
        rec.setdefault("has_arabic", audit_row["has_arabic"])
        rec.setdefault("model_estimated", model)
        rec.setdefault("model_confidence", round(conf, 3))

        by_model[model] = by_model.get(model, 0) + 1
        enriched += 1

    # Confirm original fields still present on every record.
    for rec in cache:
        for orig in ("question", "answer", "verses", "embedding", "timestamp"):
            assert orig in rec, (
                f"Lost field {orig} on record q={rec.get('question', '?')[:60]!r}"
            )

    print(f"Enriched: {enriched}")
    print(f"No audit row (skipped): {missing_audit}")
    print(f"Model distribution: {by_model}")
    print(f"New fields per entry: {new_fields}")

    answer_cache._save_cache(cache)
    print("Saved.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
