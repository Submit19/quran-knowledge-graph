"""
Deductions API — endpoints for the deductions UI.

Provides a FastAPI APIRouter mountable from app.py:

    from deductions_api import deductions_router
    app.include_router(deductions_router)
"""

import json
import subprocess
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

# ── paths ─────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
AUTORESEARCH = ROOT / "autoresearch"
VERSES_PATH = ROOT / "data" / "verses.json"

# ── category colours ──────────────────────────────────────────────────────────

CATEGORY_COLORS = {
    "monotheism_and_gods_nature": "#10b981",
    "prophecy_and_revelation": "#3b82f6",
    "moral_law_and_ethics": "#f59e0b",
    "worship_and_ritual": "#8b5cf6",
    "afterlife_and_judgment": "#ef4444",
    "creation_and_cosmology": "#06b6d4",
    "prophetic_narratives": "#f97316",
    "social_law": "#ec4899",
    "covenant_and_obedience": "#14b8a6",
    "divine_mercy_and_forgiveness": "#a3e635",
    "warfare_and_struggle": "#dc2626",
    "knowledge_and_wisdom": "#818cf8",
    "mathematical_miracle": "#fbbf24",
    "uncategorized": "#475569",
}

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


def _load_verses_lookup() -> dict:
    """Return {verse_id: {text, surah_name}} from data/verses.json."""
    raw = _load_json(VERSES_PATH, [])
    lookup: dict = {}
    for v in raw:
        vid = v.get("verse_id") or f"{v.get('surah')}:{v.get('verse')}"
        lookup[vid] = {
            "text": v.get("text", ""),
            "surah_name": v.get("surah_name", ""),
        }
    return lookup


def _verse_texts_for(verse_ids: list, lookup: dict) -> dict:
    """Given a list of verse id strings, return {id: text}."""
    return {vid: lookup[vid]["text"] for vid in verse_ids if vid in lookup}


def _is_process_running(script_name: str) -> bool:
    """Check whether a Python script is currently running."""
    try:
        out = subprocess.check_output(
            ["pgrep", "-af", script_name],
            text=True,
            timeout=5,
        )
        for line in out.strip().splitlines():
            if script_name in line and "pgrep" not in line:
                return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


# ── router ────────────────────────────────────────────────────────────────────

deductions_router = APIRouter()


# 1. Graph data for 3D visualisation ──────────────────────────────────────────

@deductions_router.get("/api/deductions/graph")
async def deductions_graph():
    data = _load_json(AUTORESEARCH / "meta_knowledge_graph.json", {"nodes": [], "edges": []})

    nodes = []
    for n in data.get("nodes", []):
        cat_id = n.get("id", "uncategorized")
        nodes.append({
            "id": cat_id,
            "label": n.get("label", cat_id),
            "description": n.get("description", ""),
            "verse_count": n.get("verse_count", 0),
            "color": CATEGORY_COLORS.get(cat_id, CATEGORY_COLORS["uncategorized"]),
        })

    edges = []
    for e in data.get("edges", []):
        edges.append({
            "source": e.get("source", ""),
            "target": e.get("target", ""),
            "weight": e.get("weight", 0),
            "avg_quality": e.get("avg_quality", 0),
        })

    return {"nodes": nodes, "edges": edges}


# 2. Top insights with verse texts ────────────────────────────────────────────

@deductions_router.get("/api/deductions/insights")
async def deductions_insights():
    raw = _load_json(AUTORESEARCH / "synthesized_insights.json", [])
    lookup = _load_verses_lookup()

    # Sort by avg_quality descending, take top 100
    raw.sort(key=lambda x: x.get("avg_quality", 0), reverse=True)
    top = raw[:100]

    insights = []
    for item in top:
        verse_pair = item.get("verse_pair", [])
        insights.append({
            "category": item.get("category", "uncategorized"),
            "verse_pair": verse_pair,
            "bridge_keywords": item.get("bridge_keywords", []),
            "conclusion": item.get("best_conclusion", ""),
            "quality": item.get("avg_quality", 0),
            "verse_texts": _verse_texts_for(verse_pair, lookup),
        })

    return {"insights": insights}


# 3. Pipeline status ──────────────────────────────────────────────────────────

@deductions_router.get("/api/deductions/status")
async def deductions_status():
    # Count total deductions
    total_deductions = 0
    jsonl_path = AUTORESEARCH / "all_deductions.jsonl"
    if jsonl_path.exists():
        try:
            with open(jsonl_path, encoding="utf-8") as f:
                for _ in f:
                    total_deductions += 1
        except Exception:
            pass

    # Discover categories from categorized_deductions.json
    cat_data = _load_json(AUTORESEARCH / "categorized_deductions.json", [])
    categories: set = set()
    for item in cat_data:
        for cat_pair in item.get("categories", []):
            if isinstance(cat_pair, list) and cat_pair:
                categories.add(cat_pair[0])

    # Last round info from deduction_rounds.tsv
    last_round_time = None
    tsv_path = AUTORESEARCH / "deduction_rounds.tsv"
    if tsv_path.exists():
        try:
            with open(tsv_path, encoding="utf-8") as f:
                lines = f.readlines()
            # Last non-empty line (skip header)
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith("round"):
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        last_round_time = parts[1]
                    break
        except Exception:
            pass

    is_running = _is_process_running("infinite_deduction.py")

    return {
        "total_deductions": total_deductions,
        "categories_found": len(categories),
        "last_round_time": last_round_time,
        "is_running": is_running,
    }


# 4. Deductions by category ───────────────────────────────────────────────────

@deductions_router.get("/api/deductions/category/{category_name}")
async def deductions_by_category(category_name: str):
    cat_data = _load_json(AUTORESEARCH / "categorized_deductions.json", [])
    lookup = _load_verses_lookup()

    results = []
    for item in cat_data:
        item_cats = [
            c[0] for c in item.get("categories", []) if isinstance(c, list) and c
        ]
        if category_name not in item_cats:
            continue

        verse_ids = item.get("premise_verses", [])
        results.append({
            "timestamp": item.get("timestamp", ""),
            "quality_score": item.get("quality_score", 0),
            "novelty_score": item.get("novelty_score", 0),
            "coherence_score": item.get("coherence_score", 0),
            "rule": item.get("rule", ""),
            "premise_verses": verse_ids,
            "bridge_keywords": item.get("bridge_keywords", []),
            "conclusion": item.get("conclusion", ""),
            "graph_distance": item.get("graph_distance", 0),
            "verse_texts": _verse_texts_for(verse_ids, lookup),
        })

    return {"category": category_name, "deductions": results}


# 5. Serve the deductions HTML page ───────────────────────────────────────────

@deductions_router.get("/deductions")
async def deductions_page():
    html_path = ROOT / "deductions.html"
    try:
        html = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        html = "<h1>deductions.html not found</h1>"
    return HTMLResponse(html)


@deductions_router.get("/visualizations")
async def visualizations_page():
    html_path = ROOT / "visualizations.html"
    try:
        html = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        html = "<h1>visualizations.html not found</h1>"
    return HTMLResponse(html)


@deductions_router.get("/presentation")
async def presentation_page():
    html_path = ROOT / "presentation.html"
    try:
        html = html_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        html = "<h1>presentation.html not found</h1>"
    return HTMLResponse(html)


# 6. Additional data endpoints for visualizations ────────────────────────────

@deductions_router.get("/api/deductions/stats")
async def deductions_stats():
    """Comprehensive stats for the visualizations dashboard."""
    import csv as csv_mod
    csv_mod.field_size_limit(2**31 - 1)

    # Load all deductions for stats
    jsonl_path = AUTORESEARCH / "all_deductions.jsonl"
    rule_counts = {}
    bridge_freq = {}
    surah_pairs = {}
    quality_buckets = {f"{i*10}-{i*10+9}": 0 for i in range(10)}
    total = 0
    rounds_data = []

    if jsonl_path.exists():
        try:
            with open(jsonl_path, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line.strip())
                    total += 1

                    # Rule counts
                    rule = d.get("rule", "unknown")
                    rule_counts[rule] = rule_counts.get(rule, 0) + 1

                    # Bridge keywords
                    for kw in d.get("bridge_keywords", []):
                        bridge_freq[kw] = bridge_freq.get(kw, 0) + 1

                    # Surah pairs
                    verses = d.get("premise_verses", [])
                    if len(verses) >= 2:
                        s1 = verses[0].split(":")[0]
                        s2 = verses[-1].split(":")[0]
                        if s1 != s2:
                            pair = f"{min(s1,s2)}-{max(s1,s2)}"
                            surah_pairs[pair] = surah_pairs.get(pair, 0) + 1

                    # Quality distribution
                    ns = d.get("novelty_score", 0)
                    bucket = min(9, int(ns / 10)) * 10
                    key = f"{bucket}-{bucket+9}"
                    quality_buckets[key] = quality_buckets.get(key, 0) + 1
        except Exception:
            pass

    # Rounds timeline
    tsv_path = AUTORESEARCH / "deduction_rounds.tsv"
    if tsv_path.exists():
        try:
            with open(tsv_path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split("\t")
                    if len(parts) >= 4 and parts[0] != "round":
                        rounds_data.append({
                            "round": int(parts[0]),
                            "novel": int(parts[2]),
                            "total": int(parts[3]),
                        })
        except Exception:
            pass

    # Top bridge keywords
    top_bridges = sorted(bridge_freq.items(), key=lambda x: -x[1])[:50]

    # Top surah pairs
    top_surah_pairs = sorted(surah_pairs.items(), key=lambda x: -x[1])[:30]

    return {
        "total_deductions": total,
        "rule_counts": rule_counts,
        "quality_distribution": quality_buckets,
        "top_bridge_keywords": [{"keyword": k, "count": v} for k, v in top_bridges],
        "top_surah_pairs": [{"pair": k, "count": v} for k, v in top_surah_pairs],
        "rounds_timeline": rounds_data[-200:],  # last 200 rounds
        "optimization_results": {
            "graph_before": 75.47,
            "graph_after": 81.74,
            "retrieval_before": 58.99,
            "retrieval_after": 68.44,
            "cluster_coherence_before": 35.53,
            "cluster_coherence_after": 59.87,
        },
    }
