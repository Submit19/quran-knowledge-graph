"""
Comparator & Explorer API — endpoints for parallel passages and tension explorer.

Provides a FastAPI APIRouter mountable from app.py:

    from comparator_api import comparator_router
    app.include_router(comparator_router)
"""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

# ── paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
AUTORESEARCH = ROOT / "autoresearch"

# ── helpers ───────────────────────────────────────────────────────────────────


def _load_json(path: Path, default=None):
    """Load a JSON file, returning *default* if missing or malformed."""
    if default is None:
        default = []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


# ── router ────────────────────────────────────────────────────────────────────

comparator_router = APIRouter()


# 1. Serve HTML pages ─────────────────────────────────────────────────────────


@comparator_router.get("/comparator")
async def comparator_page():
    html_path = ROOT / "comparator.html"
    try:
        html = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        html = "<h1>comparator.html not found</h1>"
    return HTMLResponse(html)


@comparator_router.get("/explorer")
async def explorer_page():
    html_path = ROOT / "explorer.html"
    try:
        html = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        html = "<h1>explorer.html not found</h1>"
    return HTMLResponse(html)


# 2. Parallel passages API ────────────────────────────────────────────────────


@comparator_router.get("/api/comparator/parallels")
async def comparator_parallels(entity: str = Query("moses", description="Entity name to filter parallels")):
    """Return parallel passages for a given entity (prophet/figure)."""
    raw = _load_json(AUTORESEARCH / "parallel_passages.json", [])
    entity_lower = entity.lower().strip()

    results = []
    for item in raw:
        item_entity = item.get("entity", "").lower().strip()
        if item_entity != entity_lower:
            continue
        results.append({
            "verse_a": item.get("verse_a", ""),
            "verse_b": item.get("verse_b", ""),
            "surah_a": item.get("surah_a", ""),
            "surah_b": item.get("surah_b", ""),
            "shared_words": item.get("shared_words", []),
            "overlap_score": item.get("overlap_score", 0),
            "text_a": item.get("text_a", ""),
            "text_b": item.get("text_b", ""),
        })

    # Sort by overlap score descending
    results.sort(key=lambda x: x["overlap_score"], reverse=True)

    return {"entity": entity, "parallels": results}


# 3. Tensions / contradictions API ────────────────────────────────────────────


@comparator_router.get("/api/explorer/tensions")
async def explorer_tensions(
    type: Optional[str] = Query(None, description="Filter by tension type"),
    sort: str = Query("score", description="Sort field: score, keyword_overlap, sentiment_divergence"),
    limit: int = Query(50, description="Max results to return"),
):
    """Return tension pairs, optionally filtered by type."""
    raw = _load_json(AUTORESEARCH / "contradictions.json", [])

    results = []
    for item in raw:
        primary = item.get("primary_type", "")
        if type and primary != type:
            continue
        results.append({
            "verse_a": item.get("verse_a", ""),
            "verse_b": item.get("verse_b", ""),
            "surah_a": item.get("surah_a", ""),
            "surah_b": item.get("surah_b", ""),
            "text_a": item.get("text_a", ""),
            "text_b": item.get("text_b", ""),
            "primary_type": primary,
            "opposite_pairs": item.get("opposite_pairs", []),
            "shared_keywords": item.get("shared_keywords", []),
            "keyword_overlap": item.get("keyword_overlap", 0),
            "sentiment_divergence": item.get("sentiment_divergence", 0),
            "score": item.get("score", 0),
        })

    # Sort
    sort_key = sort if sort in ("score", "keyword_overlap", "sentiment_divergence") else "score"
    results.sort(key=lambda x: x.get(sort_key, 0), reverse=True)

    return {"tensions": results[:limit]}
