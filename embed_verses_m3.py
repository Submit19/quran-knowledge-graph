"""
embed_verses_m3.py — re-embed Verse nodes with BGE-M3 (1024-dim multilingual).

This is ADDITIVE — it does NOT touch the existing 384-dim `embedding`
property or the `verse_embedding` index. Instead it adds:

  - v.embedding_m3       (1024-dim BGE-M3 dense vector of v.text — English)
  - v.embedding_m3_ar    (1024-dim BGE-M3 dense vector of v.arabicPlain)
  - v.embedding_m3_model
  - v.embedding_m3_dim
  - v.embedding_m3_source_hash      (en)
  - v.embedding_m3_ar_source_hash   (ar)
  - v.embedded_m3_at

And two vector indexes:
  - verse_embedding_m3      (1024-dim cosine, on v.embedding_m3)
  - verse_embedding_m3_ar   (1024-dim cosine, on v.embedding_m3_ar)

To switch chat.py's tool_semantic_search to use the new index without code
changes, set env: SEMANTIC_SEARCH_INDEX=verse_embedding_m3

Usage:
  python embed_verses_m3.py                # idempotent — skips already-current
  python embed_verses_m3.py --force        # re-embed everything
  python embed_verses_m3.py --skip-arabic  # English only (faster)
"""

import argparse
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
USER     = os.getenv("NEO4J_USER",     "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")
DB       = os.getenv("NEO4J_DATABASE", "quran")
MODEL_NAME = "BAAI/bge-m3"
MODEL_DIM  = 1024
BATCH      = 8      # BGE-M3 attention is huge — keep tight on CPU
WRITE_BATCH = 50    # smaller writes to avoid pgsize limits
MAX_SEQ_LEN = 512   # cap input length; verses are short, this is plenty


def source_hash(model_name: str, dim: int, text: str) -> str:
    payload = f"{model_name}|{dim}|{text}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="Re-embed every verse regardless of existing source hashes")
    ap.add_argument("--skip-arabic", action="store_true",
                    help="Only embed English text (faster for first pass)")
    args = ap.parse_args()

    print(f"Connecting to Neo4j ({URI}, db={DB})...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("  OK")

    print(f"\nLoading BGE-M3 (one-time download ~2.3GB if not cached)...")
    import time
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    # Cap max sequence length — Quran verses are short and this prevents OOM
    # on the attention matrix (which scales O(n^2))
    model.max_seq_length = MAX_SEQ_LEN
    dim = model.get_sentence_embedding_dimension()
    assert dim == MODEL_DIM, f"unexpected dim {dim}, expected {MODEL_DIM}"
    print(f"  loaded in {time.time()-t0:.1f}s, dim={dim}, max_seq={MAX_SEQ_LEN}")

    # ── load verses + existing M3 hashes ─────────────────────────────────────
    print("\nLoading verses + existing M3 provenance...")
    with driver.session(database=DB) as s:
        rows = s.run("""
            MATCH (v:Verse) WHERE v.verseId IS NOT NULL
            RETURN v.verseId AS id, v.text AS text, v.arabicPlain AS ap,
                   v.embedding_m3_source_hash AS en_hash,
                   v.embedding_m3_ar_source_hash AS ar_hash
            ORDER BY v.verseId
        """).data()
    print(f"  loaded {len(rows):,} verses")

    # Decide which need (re-)embedding
    todo_en = []
    todo_ar = []
    for r in rows:
        en_target = source_hash(MODEL_NAME, dim, r["text"] or "")
        if args.force or r.get("en_hash") != en_target:
            todo_en.append(r)
        if not args.skip_arabic:
            ap = r.get("ap") or ""
            if ap:
                ar_target = source_hash(MODEL_NAME, dim, ap)
                if args.force or r.get("ar_hash") != ar_target:
                    todo_ar.append(r)

    print(f"  english to embed:  {len(todo_en):,}  (skipped: {len(rows)-len(todo_en):,})")
    print(f"  arabic to embed:   {len(todo_ar):,}  (skipped: {len(rows)-len(todo_ar):,})"
          if not args.skip_arabic else "  arabic embedding: skipped via --skip-arabic")

    if not todo_en and not todo_ar:
        print("\n  Everything is up to date. Nothing to do.")
        driver.close()
        return

    # ── ensure vector indexes exist ──────────────────────────────────────────
    print("\nEnsuring vector indexes...")
    with driver.session(database=DB) as s:
        try:
            s.run(f"""
                CREATE VECTOR INDEX verse_embedding_m3 IF NOT EXISTS
                FOR (v:Verse) ON (v.embedding_m3)
                OPTIONS {{indexConfig: {{
                  `vector.dimensions`: {dim},
                  `vector.similarity_function`: 'cosine'
                }}}}
            """)
            print("  verse_embedding_m3 OK")
        except Exception as e:
            print(f"  verse_embedding_m3 warning: {e}")
        if not args.skip_arabic:
            try:
                s.run(f"""
                    CREATE VECTOR INDEX verse_embedding_m3_ar IF NOT EXISTS
                    FOR (v:Verse) ON (v.embedding_m3_ar)
                    OPTIONS {{indexConfig: {{
                      `vector.dimensions`: {dim},
                      `vector.similarity_function`: 'cosine'
                    }}}}
                """)
                print("  verse_embedding_m3_ar OK")
            except Exception as e:
                print(f"  verse_embedding_m3_ar warning: {e}")

    ts = _now_iso()

    # ── embed + write English in chunks (bounded memory) ────────────────────
    if todo_en:
        print(f"\nEmbedding+writing {len(todo_en):,} English verse texts (chunk={WRITE_BATCH}, batch={BATCH})...")
        ids   = [r["id"] for r in todo_en]
        texts = [r["text"] or "" for r in todo_en]
        with driver.session(database=DB) as s:
            for i in range(0, len(ids), WRITE_BATCH):
                bi = ids[i:i+WRITE_BATCH]
                bt = texts[i:i+WRITE_BATCH]
                # encode just this chunk
                be = model.encode(
                    bt, batch_size=BATCH, show_progress_bar=False,
                    normalize_embeddings=True, convert_to_numpy=True,
                )
                rows_param = [
                    {"id": vid, "emb": e.tolist(),
                     "src_hash": source_hash(MODEL_NAME, dim, t)}
                    for vid, t, e in zip(bi, bt, be)
                ]
                s.run("""
                    UNWIND $rows AS row
                    MATCH (v:Verse {verseId: row.id})
                    CALL db.create.setNodeVectorProperty(v, 'embedding_m3', row.emb)
                    SET v.embedding_m3_model = $model,
                        v.embedding_m3_dim = $dim,
                        v.embedding_m3_source_hash = row.src_hash,
                        v.embedded_m3_at = datetime($ts)
                """, rows=rows_param, model=MODEL_NAME, dim=dim, ts=ts)
                done = min(i + WRITE_BATCH, len(ids))
                print(f"  {done}/{len(ids)}", end="\r", flush=True)
        print(f"  {len(ids)}/{len(ids)} OK              ")

    # ── embed + write Arabic in chunks ───────────────────────────────────────
    if todo_ar:
        print(f"\nEmbedding+writing {len(todo_ar):,} Arabic verse texts...")
        ids   = [r["id"] for r in todo_ar]
        ars   = [r["ap"] or "" for r in todo_ar]
        with driver.session(database=DB) as s:
            for i in range(0, len(ids), WRITE_BATCH):
                bi = ids[i:i+WRITE_BATCH]
                bt = ars[i:i+WRITE_BATCH]
                be = model.encode(
                    bt, batch_size=BATCH, show_progress_bar=False,
                    normalize_embeddings=True, convert_to_numpy=True,
                )
                rows_param = [
                    {"id": vid, "emb": e.tolist(),
                     "src_hash": source_hash(MODEL_NAME, dim, t)}
                    for vid, t, e in zip(bi, bt, be)
                ]
                s.run("""
                    UNWIND $rows AS row
                    MATCH (v:Verse {verseId: row.id})
                    CALL db.create.setNodeVectorProperty(v, 'embedding_m3_ar', row.emb)
                    SET v.embedding_m3_ar_source_hash = row.src_hash
                """, rows=rows_param)
                done = min(i + WRITE_BATCH, len(ids))
                print(f"  {done}/{len(ids)}", end="\r", flush=True)
        print(f"  {len(ids)}/{len(ids)} OK              ")

    # ── verify ────────────────────────────────────────────────────────────────
    print("\nVerifying — sample query: 'God forgives the repentant'")
    qvec = model.encode(["God forgives the repentant"], normalize_embeddings=True,
                        convert_to_numpy=True)[0].tolist()
    with driver.session(database=DB) as s:
        results = s.run("""
            CALL db.index.vector.queryNodes('verse_embedding_m3', 5, $vec)
            YIELD node, score
            RETURN node.verseId AS id, score, node.text AS text
        """, vec=qvec).data()
    print("Top 5 (BGE-M3 over English):")
    for r in results:
        print(f"  [{r['id']}] score={r['score']:.4f}")
        print(f"    {r['text'][:90]}...")

    # Cross-lingual test
    if not args.skip_arabic:
        print("\nCross-lingual test: Arabic query \u0635\u0628\u0631 (patience)")
        qvec_ar = model.encode(["\u0635\u0628\u0631"], normalize_embeddings=True,
                              convert_to_numpy=True)[0].tolist()
        with driver.session(database=DB) as s:
            r = s.run("""
                CALL db.index.vector.queryNodes('verse_embedding_m3', 5, $vec)
                YIELD node, score
                RETURN node.verseId AS id, score, node.text AS text
            """, vec=qvec_ar).data()
        print("Top 5 English verses for Arabic query 'patience':")
        for row in r:
            print(f"  [{row['id']}] score={row['score']:.4f}")
            print(f"    {row['text'][:90]}...")

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
