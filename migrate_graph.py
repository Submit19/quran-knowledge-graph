"""
Quran Knowledge Graph — Schema Migration & Quality Improvements

Improvements:
  1. Merge two isolated Verse populations into a unified schema
  2. Rebuild structural relationships (CONTAINS, NEXT_VERSE) on unified nodes
  3. Connect 33 orphan verses (Muqatta'at) to neighbours
  4. Filter generic stopword keywords
  5. Generate embeddings for any verses missing them
  6. Document the 9:128-129 translation choice

Usage:
    py migrate_graph.py

Run ONCE. Each phase is idempotent and prints verification counts.
"""

import os
import sys
import time
from pathlib import Path
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

# Extended stopword list — function words that slipped through TF-IDF filtering
GRAPH_STOPWORDS = {
    "may", "would", "make", "among", "know", "send",
    "everything", "good", "see", "come", "give", "take",
    "like", "thing", "let", "tell", "turn", "bring",
    "call", "keep", "find", "put", "set", "get",
    "much", "many", "also", "even", "one", "two",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _count(session, cypher, **params):
    return session.run(cypher, **params).single()[0]


def _print_phase(n, title):
    print(f"\n{'='*60}")
    print(f"  Phase {n}: {title}")
    print(f"{'='*60}")


# ── Phase 0: Pre-flight checks ───────────────────────────────────────────────

def phase_0(session):
    _print_phase(0, "Pre-flight Checks")

    old_count = _count(session,
        "MATCH (v:Verse) WHERE v.reference IS NOT NULL AND v.verseId IS NULL RETURN count(v)")
    new_count = _count(session,
        "MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.reference IS NULL RETURN count(v)")
    merged_count = _count(session,
        "MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.reference IS NOT NULL RETURN count(v)")
    sura_count = _count(session, "MATCH (s:Sura) RETURN count(s)")
    total_verses = _count(session, "MATCH (v:Verse) RETURN count(v)")

    print(f"  Old-schema verses (reference only):  {old_count}")
    print(f"  New-schema verses (verseId only):    {new_count}")
    print(f"  Already merged (both props):         {merged_count}")
    print(f"  Sura nodes:                          {sura_count}")
    print(f"  Total Verse nodes:                   {total_verses}")

    if old_count == 0 and merged_count > 0:
        print("\n  >> Migration already completed. Skipping phases 1-3.")
        return {"already_migrated": True}

    if old_count == 0 and new_count > 0 and merged_count == 0:
        print("\n  >> Only new-schema verses exist (no old-schema to merge).")
        return {"already_migrated": True}

    if new_count != 6234:
        print(f"\n  !! WARNING: Expected 6,234 new-schema verses, found {new_count}")
        print("  !! Aborting — investigate manually.")
        sys.exit(1)

    return {
        "already_migrated": False,
        "old_count": old_count,
        "new_count": new_count,
        "sura_count": sura_count,
    }


# ── Phase 1: Merge properties ────────────────────────────────────────────────

def phase_1(session):
    _print_phase(1, "Merge Old-Schema Properties onto New-Schema Nodes")

    # Drop the reference uniqueness constraint to avoid conflicts
    constraints = [r["name"] for r in session.run("SHOW CONSTRAINTS")]
    if "verse_ref" in constraints:
        print("  Dropping 'verse_ref' uniqueness constraint...")
        session.run("DROP CONSTRAINT verse_ref")

    # Copy reference, sura, number from old to new where verseId matches reference
    result = session.run("""
        MATCH (new:Verse) WHERE new.verseId IS NOT NULL AND new.reference IS NULL
        MATCH (old:Verse {reference: new.verseId})
        WHERE old.verseId IS NULL
        SET new.reference = old.reference,
            new.sura      = old.sura,
            new.number     = old.number
        RETURN count(new) AS merged
    """)
    merged = result.single()["merged"]
    print(f"  Merged properties onto {merged} verses")

    # Verify
    still_missing = _count(session,
        "MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.reference IS NULL RETURN count(v)")
    print(f"  New-schema verses still missing 'reference': {still_missing}")

    # For any that didn't match (edge case), set reference = verseId
    if still_missing > 0:
        session.run("""
            MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.reference IS NULL
            SET v.reference = v.verseId,
                v.sura      = v.surah,
                v.number     = v.verseNum
        """)
        print(f"  Filled {still_missing} remaining verses with reference = verseId")

    return merged


# ── Phase 2: Migrate structural relationships ────────────────────────────────

def phase_2(session):
    _print_phase(2, "Rebuild Structural Relationships on Unified Nodes")

    # 2a: CONTAINS — connect Sura nodes to unified verses
    print("  Creating CONTAINS relationships...")
    result = session.run("""
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        MATCH (s:Sura {number: v.surah})
        MERGE (s)-[:CONTAINS]->(v)
        RETURN count(v) AS linked
    """)
    contains_count = result.single()["linked"]
    print(f"  CONTAINS edges created/verified: {contains_count}")

    # 2b: NEXT_VERSE — within each surah
    print("  Building NEXT_VERSE chains (within surahs)...")
    result = session.run("""
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        WITH v ORDER BY v.surah, v.verseNum
        WITH v.surah AS surah, collect(v) AS verses
        UNWIND range(0, size(verses)-2) AS i
        WITH verses[i] AS a, verses[i+1] AS b
        MERGE (a)-[:NEXT_VERSE]->(b)
        RETURN count(*) AS chained
    """)
    within_count = result.single()["chained"]
    print(f"  Within-surah NEXT_VERSE edges: {within_count}")

    # 2c: NEXT_VERSE — cross-surah (last verse of N -> first verse of N+1)
    print("  Building NEXT_VERSE chains (cross-surah)...")
    result = session.run("""
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        WITH v ORDER BY v.surah, v.verseNum
        WITH v.surah AS surah, collect(v) AS verses
        WITH surah, verses[size(verses)-1] AS lastV, verses[0] AS firstV
        ORDER BY surah
        WITH collect({last: lastV, first: firstV}) AS pairs
        UNWIND range(0, size(pairs)-2) AS i
        WITH pairs[i].last AS prevLast, pairs[i+1].first AS nextFirst
        MERGE (prevLast)-[:NEXT_VERSE]->(nextFirst)
        RETURN count(*) AS cross
    """)
    cross_count = result.single()["cross"]
    print(f"  Cross-surah NEXT_VERSE edges: {cross_count}")

    total_nv = _count(session, "MATCH ()-[r:NEXT_VERSE]->() RETURN count(r)")
    print(f"  Total NEXT_VERSE edges now: {total_nv}")

    return {"contains": contains_count, "next_verse": total_nv}


# ── Phase 3: Delete old-schema nodes ─────────────────────────────────────────

def phase_3(session):
    _print_phase(3, "Delete Old-Schema Verse Nodes")

    old_count = _count(session,
        "MATCH (v:Verse) WHERE v.reference IS NOT NULL AND v.verseId IS NULL RETURN count(v)")
    print(f"  Old-schema verses to delete: {old_count}")

    if old_count == 0:
        print("  Nothing to delete.")
        return 0

    # Batch delete to avoid memory issues
    total_deleted = 0
    while True:
        result = session.run("""
            MATCH (old:Verse)
            WHERE old.reference IS NOT NULL AND old.verseId IS NULL
            WITH old LIMIT 1000
            DETACH DELETE old
            RETURN count(*) AS deleted
        """)
        batch = result.single()["deleted"]
        if batch == 0:
            break
        total_deleted += batch
        print(f"    Deleted batch: {batch} (total: {total_deleted})")

    # Re-create uniqueness constraint on reference
    print("  Re-creating 'verse_ref' uniqueness constraint...")
    session.run("CREATE CONSTRAINT verse_ref IF NOT EXISTS FOR (v:Verse) REQUIRE v.reference IS UNIQUE")

    remaining = _count(session, "MATCH (v:Verse) RETURN count(v)")
    print(f"  Total Verse nodes remaining: {remaining}")

    return total_deleted


# ── Phase 4: Connect orphan verses ───────────────────────────────────────────

def phase_4(session):
    _print_phase(4, "Connect Orphan Verses")

    orphan_count = _count(session, """
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        AND NOT (v)-[:RELATED_TO]-()
        AND NOT (v)-[:MENTIONS]->()
        RETURN count(v)
    """)
    print(f"  Orphan verses (no RELATED_TO or MENTIONS): {orphan_count}")

    if orphan_count == 0:
        print("  No orphans to fix.")
        return 0

    # Connect orphans to their NEXT_VERSE neighbours with a low-score RELATED_TO
    result = session.run("""
        MATCH (orphan:Verse) WHERE orphan.verseId IS NOT NULL
        AND NOT (orphan)-[:RELATED_TO]-()
        AND NOT (orphan)-[:MENTIONS]->()
        OPTIONAL MATCH (prev:Verse)-[:NEXT_VERSE]->(orphan)
        OPTIONAL MATCH (orphan)-[:NEXT_VERSE]->(next:Verse)
        WITH orphan, prev, next
        FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
            MERGE (prev)-[r:RELATED_TO]-(orphan)
            ON CREATE SET r.score = 0.1
        )
        FOREACH (_ IN CASE WHEN next IS NOT NULL THEN [1] ELSE [] END |
            MERGE (orphan)-[r:RELATED_TO]-(next)
            ON CREATE SET r.score = 0.1
        )
        RETURN count(orphan) AS fixed
    """)
    fixed = result.single()["fixed"]
    print(f"  Connected {fixed} orphan verses to neighbours")

    # Verify
    still_orphan = _count(session, """
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL
        AND NOT (v)-[:RELATED_TO]-()
        AND NOT (v)-[:MENTIONS]->()
        AND NOT (v)<-[:NEXT_VERSE]-()
        AND NOT (v)-[:NEXT_VERSE]->()
        RETURN count(v)
    """)
    print(f"  Remaining fully isolated verses: {still_orphan}")

    return fixed


# ── Phase 5: Filter generic keywords ─────────────────────────────────────────

def phase_5(session):
    _print_phase(5, "Filter Generic Stopword Keywords")

    # Check which stopwords actually exist in the graph
    existing = session.run("""
        UNWIND $words AS w
        OPTIONAL MATCH (k:Keyword {keyword: w})
        WITH w, k WHERE k IS NOT NULL
        OPTIONAL MATCH (v)-[r:MENTIONS]->(k)
        RETURN w AS word, count(r) AS mentions
        ORDER BY mentions DESC
    """, words=list(GRAPH_STOPWORDS))

    found = []
    for r in existing:
        if r["mentions"] > 0:
            found.append((r["word"], r["mentions"]))

    if not found:
        print("  No matching stopword keywords found in graph.")
        return 0

    print(f"  Found {len(found)} stopword keywords to remove:")
    for word, mentions in found:
        print(f"    {word:20s} — {mentions} MENTIONS edges")

    total_mentions = sum(m for _, m in found)
    words_to_remove = [w for w, _ in found]

    # Delete MENTIONS edges and then the keyword nodes
    session.run("""
        UNWIND $words AS w
        MATCH (k:Keyword {keyword: w})
        OPTIONAL MATCH ()-[r:MENTIONS]->(k)
        DELETE r
        WITH k
        DETACH DELETE k
    """, words=words_to_remove)

    print(f"  Removed {len(words_to_remove)} keyword nodes and ~{total_mentions} MENTIONS edges")

    remaining_kw = _count(session, "MATCH (k:Keyword) RETURN count(k)")
    remaining_mentions = _count(session, "MATCH ()-[r:MENTIONS]->() RETURN count(r)")
    print(f"  Keywords remaining: {remaining_kw}")
    print(f"  MENTIONS edges remaining: {remaining_mentions}")

    return len(words_to_remove)


# ── Phase 6: Check/generate embeddings ────────────────────────────────────────

def phase_6(session):
    _print_phase(6, "Verify Embeddings")

    missing = _count(session,
        "MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.embedding IS NULL RETURN count(v)")
    print(f"  Verses missing embeddings: {missing}")

    if missing == 0:
        print("  All verses have embeddings. Nothing to do.")
        return 0

    print(f"  Generating embeddings for {missing} verses...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("  !! sentence-transformers not installed. Skipping.")
        print("  !! Run: pip install sentence-transformers")
        return -1

    model = SentenceTransformer("all-MiniLM-L6-v2")

    rows = list(session.run("""
        MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND v.embedding IS NULL
        RETURN v.verseId AS id, v.text AS text
    """))

    texts = [r["text"] for r in rows]
    ids = [r["id"] for r in rows]
    embeddings = model.encode(texts, batch_size=256, show_progress_bar=True)

    for vid, emb in zip(ids, embeddings):
        session.run(
            "MATCH (v:Verse {verseId: $id}) SET v.embedding = $emb",
            id=vid, emb=emb.tolist()
        )

    print(f"  Generated and stored {len(ids)} embeddings")
    return len(ids)


# ── Phase 7: Document translation choice ─────────────────────────────────────

def phase_7(session):
    _print_phase(7, "Document Translation Metadata")

    session.run("""
        MERGE (m:GraphMeta {key: 'translation'})
        SET m.name = 'Rashad Khalifa — The Final Testament (Authorized English Version)',
            m.note_9_128_129 = 'Verses 9:128-129 are intentionally excluded. Rashad Khalifa considered these two verses to be later additions not part of the original Quran text, consistent with his analysis of the mathematical structure based on the number 19.',
            m.total_verses = 6234,
            m.surahs = 114,
            m.migration_date = datetime()
    """)
    print("  GraphMeta node created/updated with translation details.")


# ── Final verification ────────────────────────────────────────────────────────

def verify_final(session):
    _print_phase("OK", "Final Verification")

    checks = [
        ("Total Verse nodes",
         "MATCH (v:Verse) RETURN count(v)"),
        ("Verses with verseId",
         "MATCH (v:Verse) WHERE v.verseId IS NOT NULL RETURN count(v)"),
        ("Verses with reference",
         "MATCH (v:Verse) WHERE v.reference IS NOT NULL RETURN count(v)"),
        ("Verses with embedding",
         "MATCH (v:Verse) WHERE v.embedding IS NOT NULL RETURN count(v)"),
        ("Old-schema only (should be 0)",
         "MATCH (v:Verse) WHERE v.verseId IS NULL RETURN count(v)"),
        ("Sura nodes",
         "MATCH (s:Sura) RETURN count(s)"),
        ("Keyword nodes",
         "MATCH (k:Keyword) RETURN count(k)"),
        ("CONTAINS edges",
         "MATCH ()-[r:CONTAINS]->() RETURN count(r)"),
        ("NEXT_VERSE edges",
         "MATCH ()-[r:NEXT_VERSE]->() RETURN count(r)"),
        ("RELATED_TO edges",
         "MATCH ()-[r:RELATED_TO]->() RETURN count(r)"),
        ("MENTIONS edges",
         "MATCH ()-[r:MENTIONS]->() RETURN count(r)"),
        ("Orphan verses (no rels)",
         "MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND NOT (v)-[]-() RETURN count(v)"),
        ("GraphMeta nodes",
         "MATCH (m:GraphMeta) RETURN count(m)"),
    ]

    print(f"  {'Metric':<40s} {'Value':>8s}")
    print(f"  {'─'*40} {'─'*8}")
    for label, cypher in checks:
        val = _count(session, cypher)
        print(f"  {label:<40s} {val:>8,}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Quran Knowledge Graph — Migration Script")
    print(f"Database: {NEO4J_DB} at {NEO4J_URI}")
    print()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    driver.verify_connectivity()
    print("Connected to Neo4j.")

    t0 = time.time()

    with driver.session(database=NEO4J_DB) as s:
        state = phase_0(s)

        if not state.get("already_migrated"):
            phase_1(s)
            phase_2(s)
            phase_3(s)
        else:
            # Still rebuild structural rels if needed
            contains = _count(s, """
                MATCH (v:Verse) WHERE v.verseId IS NOT NULL AND NOT (v)<-[:CONTAINS]-()
                RETURN count(v)
            """)
            if contains > 0:
                print(f"\n  {contains} verses missing CONTAINS — rebuilding...")
                phase_2(s)

        phase_4(s)
        phase_5(s)
        phase_6(s)
        phase_7(s)
        verify_final(s)

    driver.close()
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
