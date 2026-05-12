"""
PPR hyperparameter sweep — varies pagerank damping, alpha_vector,
beta_past, and the new SIMILAR_PHRASE edges (added in T1).

Re-evaluates HippoRAG vs vanilla retrieval on QRCD across the grid to
test whether our negative result was a tuning issue.

Outputs data/qrcd_hipporag_sweep.json with all configurations tested.
"""

import itertools
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from dotenv import load_dotenv
from neo4j import GraphDatabase

from eval_common import (
    load_qrcd_grouped,
    hit_at_k, recall_at_k, first_hit_rank,
)

load_dotenv()
URI = os.getenv("NEO4J_URI"); USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD"); DB = os.getenv("NEO4J_DATABASE", "quran")

os.environ.setdefault("SEMANTIC_SEARCH_INDEX", "verse_embedding_m3")


def load_questions():
    """Load QRCD questions with gold as a set (flat format for sweep)."""
    grouped = load_qrcd_grouped()
    return [{"question": q["question"], "gold": set(q["gold"])} for q in grouped]


def main():
    questions = load_questions()
    print(f"loaded {len(questions)} questions")

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print("Neo4j OK")

    # Import patched hipporag with SIMILAR_PHRASE edges + tunable knobs
    from hipporag_traverse import _vector_seed, _past_query_seed
    import networkx as nx

    def hipporag_with_phrase_edges(session, query, alpha_vector, beta_past,
                                    pagerank_alpha, top_k_seed=30,
                                    top_k_past=5, final_top_k=20,
                                    include_similar_phrase=True):
        vec_seeds = _vector_seed(session, query, top_k=top_k_seed)
        past_seeds = _past_query_seed(session, query, top_k=top_k_past)
        personalization = defaultdict(float)
        for vid, sc in vec_seeds:
            personalization[vid] += alpha_vector * sc
        for vid, sc in past_seeds:
            personalization[vid] += beta_past * sc
        if not personalization:
            return []
        seed_ids = list(personalization.keys())

        # Build subgraph including SIMILAR_PHRASE if asked
        if include_similar_phrase:
            sp_clause = "OR type(r) = 'SIMILAR_PHRASE'"
        else:
            sp_clause = ""
        rows = session.run(f"""
            MATCH (v:Verse) WHERE v.verseId IN $seeds
            OPTIONAL MATCH (v)-[r]-(o:Verse)
            WHERE type(r) = 'RELATED_TO'
               OR type(r) IN ['SUPPORTS','ELABORATES','QUALIFIES','CONTRASTS','REPEATS']
               {sp_clause}
            WITH v, r, o LIMIT 6000
            RETURN v.verseId AS src, type(r) AS et, o.verseId AS dst,
                   coalesce(r.score, 1.0) AS w
        """, seeds=seed_ids).data()

        g = nx.Graph()
        for r in rows:
            if r["src"] and r["dst"]:
                # Weight scheme: typed edges 1.5x, similar_phrase 2.0x, related 1.0x
                w = float(r["w"] or 1.0)
                if r["et"] == "SIMILAR_PHRASE":
                    w = 2.0
                elif r["et"] in ("SUPPORTS","ELABORATES","QUALIFIES","CONTRASTS","REPEATS"):
                    w = 1.5
                g.add_edge(r["src"], r["dst"], weight=w)
        for vid in seed_ids:
            if vid not in g:
                g.add_node(vid)

        pers = {n: w for n, w in personalization.items() if n in g}
        if not pers:
            return []
        try:
            pr = nx.pagerank(g, alpha=1 - pagerank_alpha, personalization=pers,
                             weight="weight", max_iter=200, tol=1e-6)
        except Exception:
            return []
        return sorted(pr, key=pr.get, reverse=True)[:final_top_k]

    # Param grid
    grid = []
    for damping_inv in [0.15, 0.25, 0.50]:    # = 1 - alpha_pagerank
        for alpha_v in [0.5, 0.7, 1.0]:
            for beta_p in [0.0, 0.3]:
                for include_sp in [True, False]:
                    grid.append({
                        "pagerank_alpha": damping_inv,
                        "alpha_vector": alpha_v,
                        "beta_past": beta_p,
                        "include_similar_phrase": include_sp,
                    })
    print(f"sweep: {len(grid)} configs")

    # Vector-only baseline once
    print("\n=== baseline: vector-only ===")
    base_hits = {f"hit@{k}": 0 for k in [5, 10, 20]}
    base_recalls = {f"recall@{k}": 0.0 for k in [5, 10, 20]}
    base_rr = 0.0
    with driver.session(database=DB) as s:
        for q in questions:
            ids = [v[0] for v in _vector_seed(s, q["question"], top_k=20)]
            r = first_hit_rank(ids, q["gold"])
            base_rr += (1.0/r) if r else 0
            for k in [5, 10, 20]:
                base_hits[f"hit@{k}"] += int(hit_at_k(ids, q["gold"], k))
                base_recalls[f"recall@{k}"] += recall_at_k(ids, q["gold"], k)
    n = len(questions)
    base = {**{k: v/n for k,v in base_hits.items()}, **{k: v/n for k,v in base_recalls.items()},
            "mrr": base_rr/n}
    print(f"  hit@10={base['hit@10']:.4f} recall@10={base['recall@10']:.4f} mrr={base['mrr']:.4f}")

    # Sweep
    results = []
    print("\n=== sweep ===")
    with driver.session(database=DB) as s:
        for cfg in grid:
            hits = {f"hit@{k}": 0 for k in [5, 10, 20]}
            recalls = {f"recall@{k}": 0.0 for k in [5, 10, 20]}
            sum_rr = 0.0
            for q in questions:
                ids = hipporag_with_phrase_edges(
                    s, q["question"],
                    alpha_vector=cfg["alpha_vector"],
                    beta_past=cfg["beta_past"],
                    pagerank_alpha=cfg["pagerank_alpha"],
                    include_similar_phrase=cfg["include_similar_phrase"],
                )
                r = first_hit_rank(ids, q["gold"])
                sum_rr += (1.0/r) if r else 0
                for k in [5, 10, 20]:
                    hits[f"hit@{k}"] += int(hit_at_k(ids, q["gold"], k))
                    recalls[f"recall@{k}"] += recall_at_k(ids, q["gold"], k)
            row = {**cfg,
                   **{k: v/n for k,v in hits.items()},
                   **{k: v/n for k,v in recalls.items()},
                   "mrr": sum_rr/n}
            row["delta_hit10"] = row["hit@10"] - base["hit@10"]
            row["delta_mrr"] = row["mrr"] - base["mrr"]
            results.append(row)
            tag = "+" if row["delta_hit10"] > 0 else " "
            print(f"  {tag} alpha={cfg['alpha_vector']} beta={cfg['beta_past']} "
                  f"pr_a={cfg['pagerank_alpha']} sp={cfg['include_similar_phrase']}  "
                  f"hit@10={row['hit@10']:.4f} (Δ={row['delta_hit10']:+.4f})  "
                  f"mrr={row['mrr']:.4f} (Δ={row['delta_mrr']:+.4f})")

    # Find best
    best = max(results, key=lambda r: r["hit@10"])
    print("\n=== best config ===")
    print(f"  {best}")
    print(f"\n=== baseline ===")
    print(f"  {base}")

    # Save
    out = Path("data/qrcd_hipporag_sweep.json")
    out.write_text(json.dumps({
        "n_questions": n, "baseline": base, "configs": results, "best": best,
    }, indent=2), encoding="utf-8")
    print(f"\nWrote {out}")
    driver.close()


if __name__ == "__main__":
    main()
