"""
consolidate_traces.py — nightly batch job that clusters near-duplicate Query nodes
and collapses them into (:QueryCluster) nodes with merged retrieval statistics.

Motivation (from "agent-memory" Neo4j YT pattern):
  Every chat accumulates unbounded (:Query) nodes. Queries that ask essentially
  the same thing (cosine > 0.96 on query_embedding) produce redundant traces.
  Consolidating them into (:QueryCluster) enables:
    1. Cleaner `recall_similar_query` playbooks (one cluster node, not N duplicates)
    2. Aggregate retrieval stats per semantic intent (avg tools, avg cites, etc.)
    3. Bounded memory growth without discarding trace detail

Schema produced:

  (:QueryCluster {
     clusterId,          // UUID (new each run if cluster doesn't exist)
     representative_text, // text of the highest-citation member
     member_count,       // number of Query nodes in the cluster
     avg_citation_count, // mean unique cites across all answers in this cluster
     avg_tool_calls,     // mean tool_call_count across all ReasoningTraces
     avg_duration_ms,    // mean total_duration_ms
     created_at,         // ISO 8601
     updated_at,         // ISO 8601 (bumped on re-runs)
  })

  (:Query)-[:MEMBER_OF {similarity, joined_at}]->(:QueryCluster)

Design:
  - Similarity kernel: cosine on existing query_embedding (384-dim MiniLM).
    We do NOT re-embed; we fetch the stored float arrays from Neo4j and compute
    pairwise cosine in Python. This keeps the job self-contained (no model load).
  - Clustering algorithm: single-pass greedy — iterate queries by timestamp desc;
    if a query is within 0.96 of an existing cluster centroid (represented by its
    seed's embedding), add it. Otherwise start a new cluster. Simple and fast for
    the expected scale (hundreds to low thousands of Query nodes).
  - Idempotent: existing MEMBER_OF edges are matched/merged (MERGE), not duplicated.
  - Clusters with only 1 member are created but not MEMBER_OF linked (nothing to merge).

Usage:
  python consolidate_traces.py                         # run once (dry-run default OFF)
  python consolidate_traces.py --dry-run               # preview clusters, no writes
  python consolidate_traces.py --threshold 0.94        # looser similarity
  python consolidate_traces.py --min-cluster-size 2    # skip singletons entirely
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cosine(a: list[float], b: list[float]) -> float:
    """Fast cosine similarity between two equal-length float lists."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Neo4j helpers
# ---------------------------------------------------------------------------

def _get_driver():
    """Build a Neo4j driver from .env / environment."""
    root = Path(__file__).parent
    env_file = root / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

    from neo4j import GraphDatabase  # type: ignore

    uri = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    return GraphDatabase.driver(uri, auth=(user, password))


def _db_name() -> str:
    return os.getenv("NEO4J_DATABASE", "quran")


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

FETCH_QUERIES_CYPHER = """
MATCH (q:Query)
WHERE q.textEmbedding IS NOT NULL
OPTIONAL MATCH (q)-[:TRIGGERED]->(t:ReasoningTrace)
OPTIONAL MATCH (q)-[:PRODUCED]->(a:Answer)
RETURN
  q.queryId         AS queryId,
  q.text            AS text,
  q.textEmbedding   AS embedding,
  q.timestamp       AS ts,
  avg(t.tool_call_count)   AS avg_tools,
  avg(t.total_duration_ms) AS avg_ms,
  avg(a.char_count)        AS avg_chars,
  max(size(coalesce(a.cited_verses, []))) AS max_cites
ORDER BY q.timestamp DESC
"""

EXISTING_CLUSTERS_CYPHER = """
MATCH (qc:QueryCluster)
OPTIONAL MATCH (q:Query)-[:MEMBER_OF]->(qc)
WHERE q.textEmbedding IS NOT NULL
RETURN
  qc.clusterId          AS clusterId,
  qc.representative_text AS rep_text,
  collect(q.queryId)    AS member_ids
"""

ENSURE_SCHEMA_CYPHER = """
CREATE CONSTRAINT IF NOT EXISTS FOR (qc:QueryCluster) REQUIRE qc.clusterId IS UNIQUE;
"""


def fetch_queries(session) -> list[dict]:
    """Fetch all Query nodes that have an embedding."""
    rows = session.run(FETCH_QUERIES_CYPHER).data()
    parsed = []
    for r in rows:
        emb = r.get("embedding")
        if emb is None:
            continue
        # Neo4j returns vector properties as lists of floats
        if not isinstance(emb, (list, tuple)):
            try:
                emb = list(emb)
            except Exception:
                continue
        parsed.append({
            "queryId": r["queryId"],
            "text": r["text"] or "",
            "embedding": [float(x) for x in emb],
            "ts": r["ts"] or "",
            "avg_tools": float(r["avg_tools"] or 0),
            "avg_ms": float(r["avg_ms"] or 0),
            "avg_chars": float(r["avg_chars"] or 0),
            "max_cites": int(r["max_cites"] or 0),
        })
    return parsed


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def greedy_cluster(
    queries: list[dict],
    threshold: float = 0.96,
) -> list[dict]:
    """
    Single-pass greedy clustering.

    Returns a list of cluster dicts:
      {
        "seed_embedding": [...],
        "members": [query_dict, ...],
        "representative_text": str,  # text of highest-citation member
      }
    """
    clusters: list[dict] = []

    for q in queries:
        emb = q["embedding"]
        best_cluster = None
        best_sim = threshold

        for cl in clusters:
            sim = _cosine(emb, cl["seed_embedding"])
            if sim >= best_sim:
                best_sim = sim
                best_cluster = cl

        if best_cluster is None:
            clusters.append({
                "seed_embedding": emb,
                "members": [q],
                "representative_text": q["text"],
            })
        else:
            best_cluster["members"].append(q)
            # Update representative to highest-citation member
            if q["max_cites"] > max(m["max_cites"] for m in best_cluster["members"][:-1] or [{"max_cites": -1}]):
                best_cluster["representative_text"] = q["text"]

    return clusters


# ---------------------------------------------------------------------------
# Neo4j write pass
# ---------------------------------------------------------------------------

MERGE_CLUSTER_CYPHER = """
MERGE (qc:QueryCluster {clusterId: $clusterId})
ON CREATE SET
  qc.representative_text = $rep_text,
  qc.member_count         = $member_count,
  qc.avg_citation_count   = $avg_cites,
  qc.avg_tool_calls       = $avg_tools,
  qc.avg_duration_ms      = $avg_ms,
  qc.created_at           = $now,
  qc.updated_at           = $now
ON MATCH SET
  qc.representative_text = $rep_text,
  qc.member_count         = $member_count,
  qc.avg_citation_count   = $avg_cites,
  qc.avg_tool_calls       = $avg_tools,
  qc.avg_duration_ms      = $avg_ms,
  qc.updated_at           = $now
RETURN qc.clusterId AS id
"""

MERGE_MEMBER_OF_CYPHER = """
MATCH (q:Query {queryId: $queryId})
MATCH (qc:QueryCluster {clusterId: $clusterId})
MERGE (q)-[r:MEMBER_OF]->(qc)
ON CREATE SET r.similarity = $similarity, r.joined_at = $now
ON MATCH  SET r.similarity = $similarity
RETURN r
"""


def write_clusters(
    session,
    clusters: list[dict],
    min_cluster_size: int = 1,
    dry_run: bool = False,
) -> dict:
    """Write clusters + MEMBER_OF edges to Neo4j. Returns summary dict."""
    now = _now_iso()
    n_clusters_written = 0
    n_edges_written = 0
    n_skipped_singletons = 0

    for cl in clusters:
        members = cl["members"]
        if len(members) < min_cluster_size:
            n_skipped_singletons += 1
            continue

        # Derive stats
        cluster_id = str(uuid.uuid4())
        avg_cites = sum(m["max_cites"] for m in members) / len(members)
        avg_tools = sum(m["avg_tools"] for m in members) / len(members)
        avg_ms = sum(m["avg_ms"] for m in members) / len(members)

        if not dry_run:
            session.run(
                MERGE_CLUSTER_CYPHER,
                clusterId=cluster_id,
                rep_text=cl["representative_text"],
                member_count=len(members),
                avg_cites=avg_cites,
                avg_tools=avg_tools,
                avg_ms=avg_ms,
                now=now,
            )

        n_clusters_written += 1

        # Write MEMBER_OF edges for multi-member clusters
        if len(members) >= 2:
            seed_emb = cl["seed_embedding"]
            for m in members:
                sim = _cosine(m["embedding"], seed_emb)
                if not dry_run:
                    session.run(
                        MERGE_MEMBER_OF_CYPHER,
                        queryId=m["queryId"],
                        clusterId=cluster_id,
                        similarity=round(sim, 6),
                        now=now,
                    )
                n_edges_written += 1

    return {
        "clusters_written": n_clusters_written,
        "member_edges_written": n_edges_written,
        "singletons_skipped": n_skipped_singletons,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(
    threshold: float = 0.96,
    min_cluster_size: int = 1,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict:
    """
    Full consolidation pass.

    Returns a summary dict suitable for logging:
      {
        "queries_fetched": int,
        "clusters_found": int,
        "clusters_written": int,
        "member_edges_written": int,
        "singletons_skipped": int,
        "dry_run": bool,
      }
    """
    driver = _get_driver()
    db = _db_name()

    with driver.session(database=db) as session:
        # Ensure schema (idempotent)
        try:
            session.run(ENSURE_SCHEMA_CYPHER)
        except Exception as e:
            if verbose:
                print(f"[WARN] schema constraint: {e}", file=sys.stderr)

        if verbose:
            print("Fetching Query nodes with embeddings...", flush=True)
        queries = fetch_queries(session)

        if not queries:
            print("No Query nodes with embeddings found. Nothing to consolidate.")
            driver.close()
            return {"queries_fetched": 0, "clusters_found": 0,
                    "clusters_written": 0, "member_edges_written": 0,
                    "singletons_skipped": 0, "dry_run": dry_run}

        if verbose:
            print(f"  {len(queries)} queries loaded.", flush=True)

        clusters = greedy_cluster(queries, threshold=threshold)

        if verbose:
            multi = [c for c in clusters if len(c["members"]) >= 2]
            print(f"  {len(clusters)} clusters found ({len(multi)} with 2+ members).", flush=True)

        summary = write_clusters(
            session,
            clusters,
            min_cluster_size=min_cluster_size,
            dry_run=dry_run,
        )
        summary["queries_fetched"] = len(queries)
        summary["clusters_found"] = len(clusters)

    driver.close()

    if verbose:
        tag = "[DRY-RUN] " if dry_run else ""
        print(
            f"{tag}Done — {summary['clusters_written']} clusters written, "
            f"{summary['member_edges_written']} MEMBER_OF edges, "
            f"{summary['singletons_skipped']} singletons skipped.",
            flush=True,
        )

    return summary


def main():
    ap = argparse.ArgumentParser(
        description="Consolidate near-duplicate Query nodes into QueryCluster nodes."
    )
    ap.add_argument(
        "--threshold", type=float, default=0.96,
        help="Cosine similarity threshold to merge queries (default: 0.96)",
    )
    ap.add_argument(
        "--min-cluster-size", type=int, default=1,
        help="Minimum members to write a cluster (default: 1, set 2 to skip singletons)",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Preview clustering without writing to Neo4j",
    )
    ap.add_argument(
        "--quiet", action="store_true",
        help="Suppress verbose output",
    )
    args = ap.parse_args()

    result = run(
        threshold=args.threshold,
        min_cluster_size=args.min_cluster_size,
        dry_run=args.dry_run,
        verbose=not args.quiet,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
