"""
Typed Edge Classification — Adds REPEATS, ELABORATES, SUPPORTS, QUALIFIES,
CONTRASTS edges alongside existing RELATED_TO.

Phase 1: REPEATS     (algorithmic — Jaccard + embedding cosine)
Phase 2: ELABORATES  (algorithmic — length ratio + embedding)
Phase 3: SUPPORTS / QUALIFIES / CONTRASTS  (LLM-assisted, high-score edges)

Usage:
    py classify_edges.py

Idempotent — safe to re-run. Existing typed edges are skipped (MERGE).
"""

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ── env ───────────────────────────────────────────────────────────────────────

def _load_env():
    path = Path(__file__).parent / ".env"
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                if v.strip():
                    os.environ[k.strip()] = v.strip()

load_dotenv()
_load_env()

NEO4J_URI  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB   = os.getenv("NEO4J_DATABASE", "quran")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

CONFIDENCE_THRESHOLD = 0.7

# ── helpers ───────────────────────────────────────────────────────────────────

def _count(session, cypher, **params):
    return session.run(cypher, **params).single()[0]


def _print_phase(n, title):
    print(f"\n{'='*60}")
    print(f"  Phase {n}: {title}")
    print(f"{'='*60}")


def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    dot = np.dot(a, b)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(dot / (na * nb))


def jaccard(text_a, text_b):
    ta = set(text_a.lower().split())
    tb = set(text_b.lower().split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# ── Phase 0: Load all verse data ─────────────────────────────────────────────

def load_verses(session):
    """Load all verse texts and embeddings into memory."""
    _print_phase(0, "Loading verse data")
    rows = list(session.run("""
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        RETURN v.verseId AS id, v.text AS text, v.embedding AS emb
    """))
    verses = {}
    for r in rows:
        verses[r["id"]] = {
            "text": r["text"] or "",
            "emb": r["emb"],  # may be list or None
        }
    print(f"  Loaded {len(verses)} verses")
    return verses


def load_related_edges(session):
    """Load all RELATED_TO edges."""
    rows = list(session.run("""
        MATCH (a:Verse)-[r:RELATED_TO]-(b:Verse)
        WHERE a.verseId < b.verseId
        RETURN a.verseId AS v1, b.verseId AS v2, r.score AS score
    """))
    edges = [(r["v1"], r["v2"], r["score"]) for r in rows]
    print(f"  Loaded {len(edges)} RELATED_TO edges")
    return edges


# ── Phase 1: REPEATS ─────────────────────────────────────────────────────────

def phase_1_repeats(session, edges, verses):
    _print_phase(1, "Classify REPEATS (algorithmic)")

    repeats = []
    for v1, v2, score in edges:
        t1 = verses.get(v1, {}).get("text", "")
        t2 = verses.get(v2, {}).get("text", "")
        e1 = verses.get(v1, {}).get("emb")
        e2 = verses.get(v2, {}).get("emb")

        jac = jaccard(t1, t2)
        emb_sim = cosine_sim(e1, e2) if (e1 and e2) else 0.0

        if jac > 0.70 or emb_sim > 0.92:
            repeats.append({
                "v1": v1, "v2": v2, "score": score,
                "text_similarity": round(max(jac, emb_sim), 4),
            })

    print(f"  Found {len(repeats)} REPEATS pairs")

    # Write to Neo4j in batches
    batch_size = 500
    for i in range(0, len(repeats), batch_size):
        batch = repeats[i:i+batch_size]
        session.run("""
            UNWIND $batch AS b
            MATCH (a:Verse {verseId: b.v1}), (z:Verse {verseId: b.v2})
            MERGE (a)-[r:REPEATS]-(z)
            ON CREATE SET r.score = b.score, r.text_similarity = b.text_similarity
        """, batch=batch)

    created = _count(session, "MATCH ()-[r:REPEATS]->() RETURN count(r)")
    print(f"  REPEATS edges in graph: {created}")

    return set((r["v1"], r["v2"]) for r in repeats)


# ── Phase 2: ELABORATES ──────────────────────────────────────────────────────

def phase_2_elaborates(session, edges, verses, classified):
    _print_phase(2, "Classify ELABORATES (algorithmic)")

    elaborates = []
    for v1, v2, score in edges:
        if (v1, v2) in classified:
            continue

        t1 = verses.get(v1, {}).get("text", "")
        t2 = verses.get(v2, {}).get("text", "")
        e1 = verses.get(v1, {}).get("emb")
        e2 = verses.get(v2, {}).get("emb")

        len1, len2 = len(t1), len(t2)
        if min(len1, len2) == 0:
            continue

        ratio = max(len1, len2) / min(len1, len2)
        emb_sim = cosine_sim(e1, e2) if (e1 and e2) else 0.0

        if ratio > 1.5 and emb_sim > 0.75:
            # Longer verse elaborates the shorter one
            if len1 > len2:
                detail, summary = v1, v2
            else:
                detail, summary = v2, v1

            elaborates.append({
                "detail": detail, "summary": summary, "score": score,
                "confidence": round(min(emb_sim, ratio / 3.0), 4),
                "basis": "length_ratio",
            })

    print(f"  Found {len(elaborates)} ELABORATES pairs")

    batch_size = 500
    for i in range(0, len(elaborates), batch_size):
        batch = elaborates[i:i+batch_size]
        session.run("""
            UNWIND $batch AS b
            MATCH (d:Verse {verseId: b.detail}), (s:Verse {verseId: b.summary})
            MERGE (d)-[r:ELABORATES]->(s)
            ON CREATE SET r.score = b.score, r.confidence = b.confidence, r.basis = b.basis
        """, batch=batch)

    created = _count(session, "MATCH ()-[r:ELABORATES]->() RETURN count(r)")
    print(f"  ELABORATES edges in graph: {created}")

    return classified | set(
        (min(e["detail"], e["summary"]), max(e["detail"], e["summary"]))
        for e in elaborates
    )


# ── Phase 3: LLM Classification ──────────────────────────────────────────────

def phase_3_llm(session, edges, verses, classified):
    _print_phase(3, "Classify SUPPORTS / QUALIFIES / CONTRASTS (LLM)")

    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    # Only classify high-score unclassified edges
    candidates = [
        (v1, v2, score) for v1, v2, score in edges
        if (v1, v2) not in classified and score >= 1.0
    ]
    print(f"  Candidates (score >= 1.0, unclassified): {len(candidates)}")

    if not candidates:
        print("  Nothing to classify.")
        return classified

    # Build batches of 30 pairs each
    BATCH = 30
    all_results = []
    total_batches = (len(candidates) + BATCH - 1) // BATCH

    for bi in range(0, len(candidates), BATCH):
        batch = candidates[bi:bi+BATCH]
        batch_num = bi // BATCH + 1

        # Build the prompt
        pairs_text = []
        for idx, (v1, v2, score) in enumerate(batch):
            t1 = verses.get(v1, {}).get("text", "")[:300]
            t2 = verses.get(v2, {}).get("text", "")[:300]
            pairs_text.append(
                f"PAIR {idx+1}:\n"
                f"  [{v1}]: {t1}\n"
                f"  [{v2}]: {t2}"
            )

        prompt = (
            "Classify each verse pair's relationship. For each pair, respond with EXACTLY one line:\n"
            "PAIR N: TYPE confidence\n\n"
            "Types:\n"
            "- SUPPORTS: A provides independent evidence/reinforcement for B's claim\n"
            "- QUALIFIES: A adds a condition, exception, or limitation to B\n"
            "- CONTRASTS: A and B present complementary perspectives or apparent tension\n"
            "- THEME_ONLY: Just topical overlap, no structural relationship\n\n"
            "Confidence: a decimal 0.0-1.0\n\n"
            "Rules:\n"
            "- SUPPORTS means both verses independently affirm the same point from different angles\n"
            "- QUALIFIES means one verse restricts/conditions the other (look for 'except', 'unless', 'if', 'but')\n"
            "- CONTRASTS means apparent tension (mercy vs punishment, permission vs prohibition) — NOT contradiction\n"
            "- THEME_ONLY is the default if the relationship is just shared vocabulary\n"
            "- Be conservative. When unsure, use THEME_ONLY\n\n"
            + "\n\n".join(pairs_text)
        )

        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text

            # Parse responses
            for line in text.strip().split("\n"):
                line = line.strip()
                if not line.startswith("PAIR"):
                    continue
                try:
                    parts = line.split(":")
                    pair_num = int(parts[0].replace("PAIR", "").strip())
                    rest = parts[1].strip().split()
                    rel_type = rest[0].upper()
                    conf = float(rest[1]) if len(rest) > 1 else 0.8

                    if rel_type not in ("SUPPORTS", "QUALIFIES", "CONTRASTS", "THEME_ONLY"):
                        continue
                    if rel_type == "THEME_ONLY":
                        continue
                    if conf < CONFIDENCE_THRESHOLD:
                        continue

                    idx = pair_num - 1
                    if 0 <= idx < len(batch):
                        v1, v2, score = batch[idx]
                        all_results.append({
                            "v1": v1, "v2": v2, "score": score,
                            "type": rel_type, "confidence": round(conf, 2),
                        })
                except (ValueError, IndexError):
                    continue

            print(f"  Batch {batch_num}/{total_batches}: classified {len(batch)} pairs")

        except Exception as e:
            print(f"  Batch {batch_num}/{total_batches}: ERROR — {e}")
            continue

        # Small delay to respect rate limits
        if batch_num < total_batches:
            time.sleep(0.5)

    # Group results by type and write to Neo4j
    by_type = {}
    for r in all_results:
        by_type.setdefault(r["type"], []).append(r)

    for rel_type, items in by_type.items():
        print(f"  Writing {len(items)} {rel_type} edges...")

        batch_size = 500
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]

            if rel_type == "SUPPORTS":
                session.run("""
                    UNWIND $batch AS b
                    MATCH (a:Verse {verseId: b.v1}), (z:Verse {verseId: b.v2})
                    MERGE (a)-[r:SUPPORTS]-(z)
                    ON CREATE SET r.score = b.score, r.confidence = b.confidence
                """, batch=batch)
            elif rel_type == "QUALIFIES":
                session.run("""
                    UNWIND $batch AS b
                    MATCH (a:Verse {verseId: b.v1}), (z:Verse {verseId: b.v2})
                    MERGE (a)-[r:QUALIFIES]-(z)
                    ON CREATE SET r.score = b.score, r.confidence = b.confidence
                """, batch=batch)
            elif rel_type == "CONTRASTS":
                session.run("""
                    UNWIND $batch AS b
                    MATCH (a:Verse {verseId: b.v1}), (z:Verse {verseId: b.v2})
                    MERGE (a)-[r:CONTRASTS]-(z)
                    ON CREATE SET r.score = b.score, r.confidence = b.confidence
                """, batch=batch)

    new_classified = set()
    for r in all_results:
        pair = (min(r["v1"], r["v2"]), max(r["v1"], r["v2"]))
        new_classified.add(pair)

    print(f"\n  LLM classified {len(all_results)} edges total:")
    for t, items in by_type.items():
        print(f"    {t}: {len(items)}")

    return classified | new_classified


# ── Phase 4: Create indexes ──────────────────────────────────────────────────

def phase_4_indexes(session):
    _print_phase(4, "Create Indexes + Update Metadata")

    for rel in ["REPEATS", "ELABORATES", "SUPPORTS", "QUALIFIES", "CONTRASTS"]:
        try:
            session.run(f"""
                CREATE INDEX rel_{rel.lower()}_score IF NOT EXISTS
                FOR ()-[r:{rel}]-() ON (r.score)
            """)
            print(f"  Index on {rel}.score: OK")
        except Exception as e:
            print(f"  Index on {rel}.score: {e}")

    session.run("""
        MERGE (m:GraphMeta {key: 'edge_schema'})
        SET m.version = '2.0',
            m.typed_edges = ['REPEATS', 'ELABORATES', 'SUPPORTS', 'QUALIFIES', 'CONTRASTS'],
            m.generic_edge = 'RELATED_TO',
            m.note = 'Typed edges are additive overlays on RELATED_TO. Absence of a typed edge means SHARES_THEME (generic).',
            m.classification_date = datetime()
    """)
    print("  GraphMeta updated.")


# ── Final verification ────────────────────────────────────────────────────────

def verify(session):
    _print_phase("OK", "Final Verification")

    checks = [
        ("RELATED_TO (original)",    "MATCH ()-[r:RELATED_TO]->() RETURN count(r)"),
        ("REPEATS",                  "MATCH ()-[r:REPEATS]->() RETURN count(r)"),
        ("ELABORATES",               "MATCH ()-[r:ELABORATES]->() RETURN count(r)"),
        ("SUPPORTS",                 "MATCH ()-[r:SUPPORTS]->() RETURN count(r)"),
        ("QUALIFIES",                "MATCH ()-[r:QUALIFIES]->() RETURN count(r)"),
        ("CONTRASTS",                "MATCH ()-[r:CONTRASTS]->() RETURN count(r)"),
        ("Total typed edges",        """
            MATCH ()-[r]->() WHERE type(r) IN ['REPEATS','ELABORATES','SUPPORTS','QUALIFIES','CONTRASTS']
            RETURN count(r)
        """),
        ("Unclassified (SHARES_THEME)", """
            MATCH (a:Verse)-[r:RELATED_TO]-(b:Verse)
            WHERE a.verseId < b.verseId
            AND NOT (a)-[:REPEATS]-(b)
            AND NOT (a)-[:ELABORATES]-(b)
            AND NOT (a)-[:SUPPORTS]-(b)
            AND NOT (a)-[:QUALIFIES]-(b)
            AND NOT (a)-[:CONTRASTS]-(b)
            RETURN count(r)
        """),
    ]

    print(f"  {'Metric':<35s} {'Count':>8s}")
    print(f"  {'---'*15} {'---'*3}")
    for label, cypher in checks:
        val = _count(session, cypher)
        print(f"  {label:<35s} {val:>8,}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Quran Knowledge Graph -- Typed Edge Classification")
    print(f"Database: {NEO4J_DB} at {NEO4J_URI}")
    print()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    driver.verify_connectivity()
    print("Connected to Neo4j.")

    t0 = time.time()

    with driver.session(database=NEO4J_DB) as s:
        verses = load_verses(s)
        edges = load_related_edges(s)

        classified = phase_1_repeats(s, edges, verses)
        classified = phase_2_elaborates(s, edges, verses, classified)
        classified = phase_3_llm(s, edges, verses, classified)
        phase_4_indexes(s)
        verify(s)

    driver.close()
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
