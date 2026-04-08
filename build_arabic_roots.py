"""
Build Arabic Root layer for the Quran Knowledge Graph.

Reads the Quranic Arabic Corpus morphology data (mustafa0x fork with Arabic
script roots) and creates:
  1. ArabicRoot nodes with root, Buckwalter transliteration, and English gloss
  2. MENTIONS_ROOT edges from Verse to ArabicRoot with count, positions, and forms
  3. (Optional) RELATED_BY_ROOT edges between verses sharing rare roots (TF-IDF)

Data source: data/quran-morphology.txt (130K rows, tab-separated)
Format: surah:verse:word:segment  arabic_form  POS  features

Usage:
    py build_arabic_roots.py                   # build CSVs + import to Neo4j
    py build_arabic_roots.py --csv-only        # just build CSVs, skip Neo4j
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))
import config as cfg

PROJECT_ROOT = Path(__file__).parent
MORPH_FILE = PROJECT_ROOT / "data" / "quran-morphology.txt"
DATA_DIR = PROJECT_ROOT / "data"

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB       = os.getenv("NEO4J_DATABASE", "quran")

# Verses excluded from Khalifa's translation
SKIP_VERSES = {(9, 128), (9, 129)}

# Common roots that are too frequent to be useful as discriminators
DEFAULT_STOP_ROOTS = {"قول", "كون", "أله"}  # say, be, God

_ROOT_RE = re.compile(r'ROOT:([^|]+)')
_LEM_RE  = re.compile(r'LEM:([^|]+)')

# ── Buckwalter transliteration table ─────────────────────────────────────────

_AR2BW = str.maketrans({
    'ا': 'A', 'ب': 'b', 'ت': 't', 'ث': 'v', 'ج': 'j', 'ح': 'H',
    'خ': 'x', 'د': 'd', 'ذ': '*', 'ر': 'r', 'ز': 'z', 'س': 's',
    'ش': '$', 'ص': 'S', 'ض': 'D', 'ط': 'T', 'ظ': 'Z', 'ع': 'E',
    'غ': 'g', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm',
    'ن': 'n', 'ه': 'h', 'و': 'w', 'ي': 'y', 'ء': "'", 'أ': '>',
    'إ': '<', 'آ': '|', 'ؤ': '&', 'ئ': '}', 'ة': 'p', 'ى': 'Y',
    'ٱ': '{',
})

def to_buckwalter(arabic: str) -> str:
    return arabic.translate(_AR2BW)

# ── simple English glosses for common roots ──────────────────────────────────

# This is a seed set; can be expanded later
ROOT_GLOSSES = {
    "رحم": "mercy, compassion",
    "علم": "knowledge, know",
    "كتب": "write, prescribe, book",
    "سمو": "name, heaven",
    "حمد": "praise",
    "ربب": "lord, sustain",
    "ملك": "king, own, possess",
    "يوم": "day",
    "عبد": "worship, serve",
    "هدي": "guide, guidance",
    "صرط": "path",
    "نعم": "blessing, grace",
    "غضب": "anger, wrath",
    "ضلل": "stray, go astray",
    "أمن": "believe, security",
    "كفر": "disbelieve, cover",
    "صلو": "prayer, contact",
    "زكو": "charity, purity",
    "صبر": "patience, persevere",
    "شكر": "gratitude, thanks",
    "توب": "repent, repentance",
    "غفر": "forgive",
    "ظلم": "wrong, oppress",
    "عدل": "justice, fairness",
    "حقق": "truth, right",
    "باطل": "falsehood, vain",
    "جنن": "paradise, garden, jinn",
    "نار": "fire, hell",
    "موت": "death, die",
    "حيو": "life, live",
    "خلق": "create, creation",
    "أرض": "earth, land",
    "سمو": "name, heaven, sky",
    "بصر": "sight, see",
    "سمع": "hear, listen",
    "قلب": "heart",
    "نفس": "soul, self",
    "ولد": "child, born",
    "أهل": "family, people",
    "قوم": "people, stand",
    "رسل": "messenger, send",
    "نبأ": "prophet, news",
    "أيي": "sign, verse",
    "سلم": "peace, submit, Islam",
    "جهد": "strive, jihad",
    "فتن": "trial, test",
    "عذب": "punish, torment",
    "حسب": "reckon, account",
    "شرك": "associate, polytheism",
    "وحد": "one, unity",
}

# ── parse morphology file ────────────────────────────────────────────────────

def parse_morphology():
    """Parse quran-morphology.txt → per-verse root data.

    Returns:
        verse_roots: dict[str, list[dict]] — verseId → [{root, form, lemma, pos, word_pos}]
        all_roots: set[str] — all unique roots found
    """
    verse_roots = defaultdict(list)
    all_roots = set()

    with open(MORPH_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) < 4:
                continue

            pos_str, form, tag, features = parts[0], parts[1], parts[2], parts[3]

            # Parse position: surah:verse:word:segment
            loc = pos_str.split(":")
            if len(loc) < 4:
                continue
            surah, verse_num, word_pos = int(loc[0]), int(loc[1]), int(loc[2])

            if (surah, verse_num) in SKIP_VERSES:
                continue

            # Extract root
            root_match = _ROOT_RE.search(features)
            if not root_match:
                continue  # particles, prefixes without roots

            root = root_match.group(1)
            lemma_match = _LEM_RE.search(features)
            lemma = lemma_match.group(1) if lemma_match else form

            vid = f"{surah}:{verse_num}"
            verse_roots[vid].append({
                "root": root,
                "form": form,
                "lemma": lemma,
                "pos": tag,
                "word_pos": word_pos,
            })
            all_roots.add(root)

    return dict(verse_roots), all_roots


# ── build root nodes and edges ───────────────────────────────────────────────

def build_root_data(verse_roots, all_roots):
    """Compute root statistics and TF-IDF for root-based verse similarity.

    Returns:
        root_nodes: list[dict] — one per root (root, rootBW, gloss, verse_count)
        verse_root_edges: list[dict] — (verseId, root, count, positions, forms)
        root_idf: dict[str, float] — IDF values per root
    """
    # Load stop roots from config or use defaults
    try:
        stop_roots = set(cfg.raw().get("arabic", {}).get("root_stoplist", []))
    except Exception:
        stop_roots = set()
    stop_roots.update(DEFAULT_STOP_ROOTS)

    try:
        min_verses = cfg.raw().get("arabic", {}).get("root_min_verses", 2)
        max_verses = cfg.raw().get("arabic", {}).get("root_max_verses", 500)
    except Exception:
        min_verses, max_verses = 2, 500

    # Count how many verses each root appears in
    root_verse_count = Counter()
    for vid, entries in verse_roots.items():
        roots_in_verse = set(e["root"] for e in entries)
        for r in roots_in_verse:
            root_verse_count[r] += 1

    N = len(verse_roots)  # total verses with root data

    # Filter roots
    valid_roots = set()
    for root, count in root_verse_count.items():
        if root in stop_roots:
            continue
        if count < min_verses or count > max_verses:
            continue
        valid_roots.add(root)

    print(f"  Total unique roots: {len(all_roots)}")
    print(f"  After filtering (min={min_verses}, max={max_verses}, {len(stop_roots)} stop roots): {len(valid_roots)}")

    # Build root nodes
    root_nodes = []
    for root in sorted(valid_roots):
        root_nodes.append({
            "root": root,
            "rootBW": to_buckwalter(root),
            "gloss": ROOT_GLOSSES.get(root, ""),
            "verse_count": root_verse_count[root],
        })

    # Build verse-root edges
    verse_root_edges = []
    for vid, entries in verse_roots.items():
        # Group by root within this verse
        root_groups = defaultdict(lambda: {"count": 0, "positions": [], "forms": set()})
        for e in entries:
            r = e["root"]
            if r not in valid_roots:
                continue
            rg = root_groups[r]
            rg["count"] += 1
            rg["positions"].append(e["word_pos"])
            rg["forms"].add(e["form"])

        for root, rg in root_groups.items():
            verse_root_edges.append({
                "verseId": vid,
                "root": root,
                "count": rg["count"],
                "positions": sorted(rg["positions"]),
                "forms": sorted(rg["forms"]),
            })

    # IDF for root-based similarity
    root_idf = {}
    for root in valid_roots:
        root_idf[root] = math.log(N / root_verse_count[root])

    return root_nodes, verse_root_edges, root_idf


def build_related_by_root(verse_roots, root_idf, valid_roots, max_edges_per_verse=12):
    """Compute verse-verse similarity based on shared Arabic roots (TF-IDF).

    Returns list of (verseId1, verseId2, score) tuples.
    """
    # Build verse → {root: tf-idf score}
    verse_vectors = {}
    for vid, entries in verse_roots.items():
        root_counts = Counter()
        for e in entries:
            if e["root"] in valid_roots:
                root_counts[e["root"]] += 1
        total = sum(root_counts.values())
        if total == 0:
            continue
        vec = {}
        for root, count in root_counts.items():
            tf = count / total
            idf = root_idf.get(root, 0)
            vec[root] = tf * idf
        verse_vectors[vid] = vec

    print(f"  Computing root-based verse similarity for {len(verse_vectors)} verses...")

    # Build inverted index: root → [verseIds]
    root_to_verses = defaultdict(list)
    for vid, vec in verse_vectors.items():
        for root in vec:
            root_to_verses[root].append(vid)

    # Find candidate pairs and score them
    edges = []
    seen = set()

    for vid, vec in verse_vectors.items():
        # Candidates: verses sharing at least one root
        candidates = Counter()
        for root in vec:
            for other_vid in root_to_verses[root]:
                if other_vid != vid:
                    candidates[other_vid] += 1

        # Score top candidates
        scored = []
        for other_vid, shared_count in candidates.most_common(max_edges_per_verse * 3):
            pair = tuple(sorted([vid, other_vid]))
            if pair in seen:
                continue
            other_vec = verse_vectors[other_vid]
            # Dot product of TF-IDF vectors (shared roots only)
            score = sum(vec.get(r, 0) * other_vec.get(r, 0) for r in vec if r in other_vec)
            if score > 0.01:
                scored.append((other_vid, score))

        scored.sort(key=lambda x: -x[1])
        for other_vid, score in scored[:max_edges_per_verse]:
            pair = tuple(sorted([vid, other_vid]))
            if pair not in seen:
                seen.add(pair)
                edges.append((vid, other_vid, round(score, 4)))

    print(f"  Generated {len(edges)} RELATED_BY_ROOT edges")
    return edges


# ── CSV export ───────────────────────────────────────────────────────────────

def export_csvs(root_nodes, verse_root_edges, related_edges):
    """Write CSVs for Neo4j import."""
    # Root nodes
    root_csv = DATA_DIR / "arabic_root_nodes.csv"
    with open(root_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["root", "rootBW", "gloss", "verse_count"])
        w.writeheader()
        w.writerows(root_nodes)
    print(f"  Wrote {len(root_nodes)} roots to {root_csv.name}")

    # Verse-root edges
    vr_csv = DATA_DIR / "verse_root_rels.csv"
    with open(vr_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["verseId", "root", "count", "positions", "forms"])
        for e in verse_root_edges:
            w.writerow([
                e["verseId"], e["root"], e["count"],
                json.dumps(e["positions"]), json.dumps(e["forms"], ensure_ascii=False)
            ])
    print(f"  Wrote {len(verse_root_edges)} verse-root edges to {vr_csv.name}")

    # Related-by-root edges
    rr_csv = DATA_DIR / "verse_related_by_root.csv"
    with open(rr_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["verseId1", "verseId2", "score"])
        for v1, v2, score in related_edges:
            w.writerow([v1, v2, score])
    print(f"  Wrote {len(related_edges)} related-by-root edges to {rr_csv.name}")


# ── Neo4j import ─────────────────────────────────────────────────────────────

def import_to_neo4j(root_nodes, verse_root_edges, related_edges):
    """Import root data into Neo4j."""
    from neo4j import GraphDatabase

    print(f"\nImporting to Neo4j ({NEO4J_URI}, database: {NEO4J_DB})...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()

    batch_size = 500

    with driver.session(database=NEO4J_DB) as session:
        # Create constraints and indexes
        print("  Creating constraints and indexes...")
        session.run("CREATE CONSTRAINT arabic_root_id IF NOT EXISTS FOR (r:ArabicRoot) REQUIRE r.root IS UNIQUE")
        session.run("CREATE INDEX arabic_root_bw IF NOT EXISTS FOR (r:ArabicRoot) ON (r.rootBW)")

        # Import root nodes
        print(f"  Importing {len(root_nodes)} ArabicRoot nodes...")
        for i in range(0, len(root_nodes), batch_size):
            batch = root_nodes[i:i + batch_size]
            session.run("""
                UNWIND $batch AS row
                MERGE (r:ArabicRoot {root: row.root})
                SET r.rootBW = row.rootBW,
                    r.gloss = row.gloss,
                    r.verseCount = row.verse_count
            """, batch=batch)
        print(f"    Done.")

        # Import MENTIONS_ROOT edges
        print(f"  Importing {len(verse_root_edges)} MENTIONS_ROOT edges...")
        for i in range(0, len(verse_root_edges), batch_size):
            batch = verse_root_edges[i:i + batch_size]
            params = [{
                "vid": e["verseId"],
                "root": e["root"],
                "count": e["count"],
                "positions": e["positions"],
                "forms": e["forms"],
            } for e in batch]
            session.run("""
                UNWIND $batch AS row
                MATCH (v:Verse {verseId: row.vid})
                MATCH (r:ArabicRoot {root: row.root})
                MERGE (v)-[rel:MENTIONS_ROOT]->(r)
                SET rel.count = row.count,
                    rel.positions = row.positions,
                    rel.forms = row.forms
            """, batch=params)
            if (i // batch_size + 1) % 10 == 0:
                print(f"    Batch {i // batch_size + 1}...")
        print(f"    Done.")

        # Import RELATED_BY_ROOT edges
        print(f"  Importing {len(related_edges)} RELATED_BY_ROOT edges...")
        for i in range(0, len(related_edges), batch_size):
            batch = [{"v1": v1, "v2": v2, "score": s} for v1, v2, s in related_edges[i:i + batch_size]]
            session.run("""
                UNWIND $batch AS row
                MATCH (v1:Verse {verseId: row.v1})
                MATCH (v2:Verse {verseId: row.v2})
                MERGE (v1)-[r:RELATED_BY_ROOT]-(v2)
                SET r.score = row.score
            """, batch=batch)
            if (i // batch_size + 1) % 10 == 0:
                print(f"    Batch {i // batch_size + 1}...")
        print(f"    Done.")

        # Verify
        root_count = session.run("MATCH (r:ArabicRoot) RETURN count(r) AS c").single()["c"]
        mr_count = session.run("MATCH ()-[r:MENTIONS_ROOT]->() RETURN count(r) AS c").single()["c"]
        rr_count = session.run("MATCH ()-[r:RELATED_BY_ROOT]-() RETURN count(r) AS c").single()["c"]
        print(f"\n  Verification:")
        print(f"    ArabicRoot nodes: {root_count}")
        print(f"    MENTIONS_ROOT edges: {mr_count}")
        print(f"    RELATED_BY_ROOT edges: {rr_count}")

        # Sample check
        sample = session.run("""
            MATCH (r:ArabicRoot {root: 'رحم'})<-[m:MENTIONS_ROOT]-(v:Verse)
            RETURN v.verseId AS vid, m.count AS cnt, m.forms AS forms
            ORDER BY m.count DESC LIMIT 5
        """).data()
        if sample:
            print(f"\n  Sample — root 'رحم' (mercy):")
            for s in sample:
                print(f"    [{s['vid']}] count={s['cnt']}, forms={s['forms']}")

    driver.close()


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-only", action="store_true", help="Only export CSVs, skip Neo4j import")
    parser.add_argument("--skip-related", action="store_true", help="Skip computing RELATED_BY_ROOT edges")
    args = parser.parse_args()

    print("Arabic Root Extraction Pipeline")
    print("=" * 60)

    # 1. Parse morphology
    print("\n[1] Parsing morphology data...")
    verse_roots, all_roots = parse_morphology()
    print(f"  Parsed {len(verse_roots)} verses with root data")
    print(f"  Found {len(all_roots)} unique roots")

    # 2. Build root nodes and edges
    print("\n[2] Building root nodes and verse-root edges...")
    root_nodes, verse_root_edges, root_idf = build_root_data(verse_roots, all_roots)
    valid_roots = {r["root"] for r in root_nodes}
    print(f"  Root nodes: {len(root_nodes)}")
    print(f"  Verse-root edges: {len(verse_root_edges)}")

    # 3. Build related-by-root edges
    related_edges = []
    if not args.skip_related:
        print("\n[3] Computing root-based verse similarity...")
        try:
            max_edges = cfg.raw().get("arabic", {}).get("related_by_root_max_edges", 12)
        except Exception:
            max_edges = 12
        related_edges = build_related_by_root(verse_roots, root_idf, valid_roots, max_edges)
    else:
        print("\n[3] Skipping RELATED_BY_ROOT edges (--skip-related)")

    # 4. Export CSVs
    print("\n[4] Exporting CSVs...")
    export_csvs(root_nodes, verse_root_edges, related_edges)

    # 5. Import to Neo4j
    if not args.csv_only:
        import_to_neo4j(root_nodes, verse_root_edges, related_edges)
    else:
        print("\n[5] Skipping Neo4j import (--csv-only)")

    print("\nDone.")


if __name__ == "__main__":
    main()
