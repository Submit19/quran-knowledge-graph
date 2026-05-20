"""
Pass 4 — add BGE-M3 question embeddings to data/answer_cache.json.

For every cache entry, compute a 1024-dim BGE-M3 embedding from the
QUESTION text and store it as a new `embedding_m3` field. The legacy
384-dim `embedding` (MiniLM) is preserved unchanged.

Why this matters: the graph (Verse nodes) was re-embedded against
BGE-M3 in the 2026-04 retrofit; the answer cache still uses MiniLM.
Pass 6 (optional) and any future cross-modal cache search can use
these embeddings for parity with the graph's index.

Reuses the get_bge_m3() singleton from model_registry — the same
loader embed_verses_m3.py uses — to avoid duplicating model
configuration.

NO Anthropic API calls. ~5–10 min on CPU for ~1600 short questions.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import answer_cache  # noqa: E402
from model_registry import get_bge_m3  # noqa: E402

CACHE_FILE = ROOT / "data" / "answer_cache.json"
BATCH = 16  # BGE-M3 attention is heavy — keep batches small on CPU.


def main() -> int:
    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    print(f"Cache entries: {len(cache)}")
    cache_size_before = CACHE_FILE.stat().st_size
    print(f"Cache file size before: {cache_size_before / 1024 / 1024:.2f} MB")

    needs = [i for i, r in enumerate(cache) if "embedding_m3" not in r]
    print(f"Entries needing embedding_m3: {len(needs)}")

    if not needs:
        print("Nothing to do.")
        return 0

    print("Loading BGE-M3...")
    t0 = time.time()
    model = get_bge_m3()
    print(f"  loaded in {time.time() - t0:.1f}s")

    t0 = time.time()
    questions = [cache[i].get("question", "") for i in needs]
    n_total = len(questions)
    done = 0
    for start in range(0, n_total, BATCH):
        batch_qs = questions[start : start + BATCH]
        batch_idxs = needs[start : start + BATCH]
        embs = model.encode(
            batch_qs,
            batch_size=BATCH,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for idx, emb in zip(batch_idxs, embs):
            cache[idx]["embedding_m3"] = emb.tolist()
        done += len(batch_qs)
        if start % (BATCH * 5) == 0 or done == n_total:
            elapsed = time.time() - t0
            rate = done / elapsed if elapsed > 0 else 0
            eta = (n_total - done) / rate if rate > 0 else 0
            print(
                f"  {done}/{n_total}  elapsed={elapsed:.1f}s  rate={rate:.1f}/s  eta={eta:.0f}s"
            )

    total_time = time.time() - t0
    print(
        f"\nEncoded {n_total} questions in {total_time:.1f}s "
        f"({n_total / total_time:.1f}/s)."
    )

    # Sanity check before saving: every record now has both embeddings.
    for r in cache:
        assert "embedding" in r, "lost legacy embedding field"
        assert "embedding_m3" in r, "missing embedding_m3 field"
        assert len(r["embedding"]) == 384, f"embedding dim wrong: {len(r['embedding'])}"
        assert len(r["embedding_m3"]) == 1024, (
            f"embedding_m3 dim wrong: {len(r['embedding_m3'])}"
        )

    answer_cache._save_cache(cache)
    cache_size_after = CACHE_FILE.stat().st_size
    print(
        f"Cache file size after:  {cache_size_after / 1024 / 1024:.2f} MB "
        f"(+{(cache_size_after - cache_size_before) / 1024 / 1024:.2f} MB)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
