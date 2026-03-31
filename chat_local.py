"""
Quran Graph Chat — In-memory version (NO Neo4j required).

Loads all graph data from CSVs into memory and provides the same
tool interface as the Neo4j version. Only requires ANTHROPIC_API_KEY.

Usage:
    python chat_local.py          # CLI chat
    python app_local.py           # Web UI at http://localhost:8081
"""

import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(2**31 - 1)

ROOT = Path(__file__).parent
DATA = ROOT / "data"

sys.path.insert(0, str(ROOT))
from build_graph import tokenize_and_lemmatize

# ══════════════════════════════════════════════════════════════════════════════
# Load graph into memory from CSVs
# ══════════════════════════════════════════════════════════════════════════════

print("Loading graph data from CSVs...")

VERSES = {}
with open(DATA / "verse_nodes.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        VERSES[row["verseId"]] = {
            "surah": int(row["surah"]),
            "verseNum": int(row["verseNum"]),
            "surahName": row["surahName"],
            "text": row["text"],
        }

KEYWORD_VERSES = defaultdict(list)   # keyword -> [(verseId, score)]
VERSE_KEYWORDS = defaultdict(list)   # verseId -> [(keyword, score)]
with open(DATA / "verse_keyword_rels.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        vid, kw, score = row["verseId"], row["keyword"], float(row["score"])
        KEYWORD_VERSES[kw].append((vid, score))
        VERSE_KEYWORDS[vid].append((kw, score))

RELATED = defaultdict(list)  # verseId -> [(otherVerseId, score)]
with open(DATA / "verse_related_rels.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        v1, v2, score = row["verseId1"], row["verseId2"], float(row["score"])
        RELATED[v1].append((v2, score))
        RELATED[v2].append((v1, score))

ALL_KEYWORDS = set(KEYWORD_VERSES.keys())

print(f"  {len(VERSES):,} verses, {len(ALL_KEYWORDS):,} keywords, "
      f"{sum(len(v) for v in RELATED.values()) // 2:,} edges")

# ══════════════════════════════════════════════════════════════════════════════
# Tool implementations (same interface as chat.py, but in-memory)
# ══════════════════════════════════════════════════════════════════════════════

def tool_search_keyword(keyword: str) -> dict:
    lemmas = tokenize_and_lemmatize(keyword)
    if not lemmas:
        return {"error": f"'{keyword}' is a stopword or too short — try a different word"}
    kw = lemmas[0]

    if kw not in ALL_KEYWORDS:
        similar = [k for k in ALL_KEYWORDS if k.startswith(kw[:4])][:8]
        return {"error": f"Keyword '{kw}' not in graph", "suggestions": similar}

    rows = sorted(KEYWORD_VERSES[kw], key=lambda x: -x[1])
    by_surah = {}
    for vid, score in rows:
        v = VERSES.get(vid, {})
        sname = f"Surah {v.get('surah', '?')}: {v.get('surahName', '?')}"
        by_surah.setdefault(sname, []).append({
            "verse_id": vid, "score": round(score, 4), "text": v.get("text", "")
        })

    return {"keyword": kw, "total_verses": len(rows), "by_surah": by_surah}


def tool_get_verse(verse_id: str) -> dict:
    verse_id = verse_id.strip().replace(" ", ":")
    v = VERSES.get(verse_id)
    if not v:
        return {"error": f"Verse [{verse_id}] not found. Format: surah:verse e.g. 2:255"}

    keywords = [kw for kw, _ in sorted(VERSE_KEYWORDS.get(verse_id, []),
                                         key=lambda x: -x[1])[:15]]

    neighbours = sorted(RELATED.get(verse_id, []), key=lambda x: -x[1])[:12]
    connected = []
    for other_id, score in neighbours:
        ov = VERSES.get(other_id, {})
        # shared keywords
        my_kws = set(kw for kw, _ in VERSE_KEYWORDS.get(verse_id, []))
        other_kws = set(kw for kw, _ in VERSE_KEYWORDS.get(other_id, []))
        shared = sorted(my_kws & other_kws)[:5]
        connected.append({
            "verse_id": other_id, "surah_name": ov.get("surahName", ""),
            "text": ov.get("text", ""), "shared_keywords": shared,
            "connection_score": round(score, 4),
        })

    return {
        "verse_id": verse_id, "surah": v["surah"], "surah_name": v["surahName"],
        "text": v["text"], "keywords": keywords, "connected_verses": connected,
    }


def tool_traverse_topic(keywords: list, hops: int = 1) -> dict:
    hops = max(1, min(hops, 2))
    lemmas = list(set(l for kw in keywords for l in tokenize_and_lemmatize(kw)))
    if not lemmas:
        return {"error": "All keywords were stopwords. Use more specific terms."}

    # Direct matches
    direct = {}
    for kw in lemmas:
        for vid, score in KEYWORD_VERSES.get(kw, []):
            if vid not in direct:
                direct[vid] = {"score": 0, "matched": []}
            direct[vid]["score"] += score
            if kw not in direct[vid]["matched"]:
                direct[vid]["matched"].append(kw)

    sorted_direct = sorted(direct.items(), key=lambda x: -x[1]["score"])
    direct_ids = set(direct.keys())
    direct_results = [{
        "verse_id": vid, "surah_name": VERSES.get(vid, {}).get("surahName", ""),
        "text": VERSES.get(vid, {}).get("text", ""),
        "matched_keywords": info["matched"], "score": round(info["score"], 4),
    } for vid, info in sorted_direct]

    seed_ids = [vid for vid, _ in sorted_direct[:30]]

    # 1-hop
    hop1 = defaultdict(float)
    for sid in seed_ids:
        for neighbor, score in RELATED.get(sid, []):
            if neighbor not in direct_ids:
                hop1[neighbor] += score

    sorted_hop1 = sorted(hop1.items(), key=lambda x: -x[1])[:60]
    hop1_ids = set(vid for vid, _ in sorted_hop1)
    hop1_results = [{
        "verse_id": vid, "surah_name": VERSES.get(vid, {}).get("surahName", ""),
        "text": VERSES.get(vid, {}).get("text", ""), "score": round(score, 4),
    } for vid, score in sorted_hop1]

    # 2-hop
    hop2_results = []
    if hops >= 2:
        exclude = direct_ids | hop1_ids
        hop2 = defaultdict(int)
        for h1_id, _ in sorted_hop1:
            for neighbor, _ in RELATED.get(h1_id, []):
                if neighbor not in exclude:
                    hop2[neighbor] += 1
        sorted_hop2 = sorted(hop2.items(), key=lambda x: -x[1])[:40]
        hop2_results = [{
            "verse_id": vid, "surah_name": VERSES.get(vid, {}).get("surahName", ""),
            "text": VERSES.get(vid, {}).get("text", ""),
        } for vid, _ in sorted_hop2]

    return {
        "keywords_used": lemmas, "direct_matches": direct_results,
        "hop_1_connections": hop1_results, "hop_2_connections": hop2_results,
        "total_verses_found": len(direct_results) + len(hop1_results) + len(hop2_results),
    }


def tool_find_path(verse_id_1: str, verse_id_2: str) -> dict:
    v1 = verse_id_1.strip().replace(" ", ":")
    v2 = verse_id_2.strip().replace(" ", ":")
    for vid in [v1, v2]:
        if vid not in VERSES:
            return {"error": f"Verse [{vid}] not found"}

    # BFS shortest path up to 6 hops
    from collections import deque
    visited = {v1: None}
    queue = deque([v1])
    found = False
    while queue:
        current = queue.popleft()
        if current == v2:
            found = True
            break
        # Check depth
        depth = 0
        node = current
        while visited.get(node) is not None:
            node = visited[node]
            depth += 1
        if depth >= 6:
            continue
        for neighbor, _ in RELATED.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = current
                queue.append(neighbor)

    if not found:
        return {"error": f"No path found between [{v1}] and [{v2}] within 6 hops"}

    # Reconstruct path
    path_ids = []
    node = v2
    while node is not None:
        path_ids.append(node)
        node = visited[node]
    path_ids.reverse()

    steps = []
    for i, vid in enumerate(path_ids):
        v = VERSES.get(vid, {})
        step = {
            "step": i + 1, "verse_id": vid,
            "surah_name": v.get("surahName", ""), "text": v.get("text", ""),
        }
        if i < len(path_ids) - 1:
            next_vid = path_ids[i + 1]
            my_kws = set(kw for kw, _ in VERSE_KEYWORDS.get(vid, []))
            next_kws = set(kw for kw, _ in VERSE_KEYWORDS.get(next_vid, []))
            step["bridge_keywords"] = sorted(my_kws & next_kws)[:5]
        steps.append(step)

    return {"from": v1, "to": v2, "hops": len(path_ids) - 1, "path": steps}


def tool_explore_surah(surah_number: int) -> dict:
    verses = [(vid, v) for vid, v in VERSES.items() if v["surah"] == surah_number]
    if not verses:
        return {"error": f"Surah {surah_number} not found (valid range: 1-114)"}

    verses.sort(key=lambda x: x[1]["verseNum"])
    surah_name = verses[0][1]["surahName"]
    verse_ids = [vid for vid, _ in verses]

    # Cross-surah connections
    cross = defaultdict(lambda: {"name": "", "count": 0})
    for vid in verse_ids:
        for neighbor, _ in RELATED.get(vid, []):
            nv = VERSES.get(neighbor, {})
            ns = nv.get("surah", 0)
            if ns != surah_number:
                cross[ns]["name"] = nv.get("surahName", "")
                cross[ns]["count"] += 1

    top_cross = sorted(cross.items(), key=lambda x: -x[1]["count"])[:10]

    return {
        "surah": surah_number, "surah_name": surah_name,
        "verse_count": len(verses),
        "verses": [{"verse_id": vid, "text": v["text"]} for vid, v in verses],
        "top_cross_surah_connections": [
            {"surah": s, "surah_name": info["name"], "connections": info["count"]}
            for s, info in top_cross
        ],
    }


def tool_semantic_search(query: str, top_k: int = 40) -> dict:
    """Fallback: keyword-based search when no embedding model available."""
    words = set(re.findall(r'[a-z]+', query.lower()))
    scored = {}
    for vid, kw_list in VERSE_KEYWORDS.items():
        overlap = sum(1 for kw, _ in kw_list if kw in words or any(w in kw for w in words))
        if overlap > 0:
            scored[vid] = overlap

    results = sorted(scored.items(), key=lambda x: -x[1])[:top_k]
    by_surah = {}
    for vid, score in results:
        v = VERSES.get(vid, {})
        sname = f"Surah {v.get('surah', '?')}: {v.get('surahName', '?')}"
        by_surah.setdefault(sname, []).append({
            "verse_id": vid, "similarity": round(score / 10, 4), "text": v.get("text", ""),
        })

    return {
        "query": query, "total_verses": len(results),
        "note": "Using keyword fallback (no embedding model). Results ranked by keyword overlap.",
        "by_surah": by_surah,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Tool schema + dispatch (same as chat.py)
# ══════════════════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "search_keyword",
        "description": "Search for all Quran verses that mention a specific keyword. Results are grouped by surah and ranked by relevance.",
        "input_schema": {
            "type": "object",
            "properties": {"keyword": {"type": "string", "description": "A single word to search for"}},
            "required": ["keyword"]
        }
    },
    {
        "name": "get_verse",
        "description": "Get a specific verse by its ID, along with its keywords and connected verses.",
        "input_schema": {
            "type": "object",
            "properties": {"verse_id": {"type": "string", "description": "Verse ID e.g. '2:255'"}},
            "required": ["verse_id"]
        }
    },
    {
        "name": "traverse_topic",
        "description": "Explore a topic using multiple keywords + graph traversal. Finds direct matches then expands through connections.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Keywords describing the topic"},
                "hops": {"type": "integer", "description": "Graph hops: 1 or 2", "default": 1}
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "find_path",
        "description": "Find the shortest thematic path between two verses through the knowledge graph.",
        "input_schema": {
            "type": "object",
            "properties": {
                "verse_id_1": {"type": "string", "description": "Starting verse ID"},
                "verse_id_2": {"type": "string", "description": "Ending verse ID"}
            },
            "required": ["verse_id_1", "verse_id_2"]
        }
    },
    {
        "name": "explore_surah",
        "description": "Get all verses in a surah and its top cross-surah thematic connections.",
        "input_schema": {
            "type": "object",
            "properties": {"surah_number": {"type": "integer", "description": "Surah number 1-114"}},
            "required": ["surah_number"]
        }
    },
    {
        "name": "semantic_search",
        "description": "Find verses conceptually similar to a query. Catches verses using different vocabulary for the same idea.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Concept to search for"},
                "top_k": {"type": "integer", "description": "Number of results", "default": 40}
            },
            "required": ["query"]
        }
    },
]

SYSTEM_PROMPT = """You are a knowledgeable Quran scholar and graph analyst with access to a \
knowledge graph of all 6,234 verses from Rashad Khalifa's translation of the Quran \
(The Final Testament). The graph connects verses through shared rare keywords using TF-IDF \
weighting, revealing thematic relationships across surahs.

You have 6 tools to explore the graph:
- search_keyword:  find ALL verses that mention a keyword
- semantic_search: find verses conceptually related to a query
- get_verse:       deep-dive into a specific verse and its connections
- traverse_topic:  multi-keyword search + graph traversal
- find_path:       shortest thematic path between two verses
- explore_surah:   map a surah's content and cross-surah connections

EXHAUSTIVE SEARCH MANDATE — for every topical question:
1. Identify ALL relevant keyword variants and call search_keyword for each
2. ALWAYS also call semantic_search with a descriptive phrase
3. Also call traverse_topic with all keywords combined
4. Deduplicate and report the TOTAL unique verse count upfront
5. Organise your answer by theme

CITATION RULES — MANDATORY:
- EVERY claim MUST cite specific verses using [surah:verse] notation
- NEVER make a theological statement without a verse citation
- If you cannot find a verse to support a point, do NOT make the point

This is Khalifa's translation — note where topics relate to his unique interpretations."""


def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "search_keyword":
            result = tool_search_keyword(**tool_input)
        elif tool_name == "get_verse":
            result = tool_get_verse(**tool_input)
        elif tool_name == "traverse_topic":
            result = tool_traverse_topic(**tool_input)
        elif tool_name == "find_path":
            result = tool_find_path(**tool_input)
        elif tool_name == "explore_surah":
            result = tool_explore_surah(**tool_input)
        elif tool_name == "semantic_search":
            result = tool_semantic_search(**tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        result = {"error": str(e)}
    return json.dumps(result, ensure_ascii=False)
