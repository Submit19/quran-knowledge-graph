"""
model_registry.py — shared lazy singletons for heavyweight ML models.

Centralises SentenceTransformer / CrossEncoder loading so that
answer_cache.py, reasoning_memory.py, and chat.py all share the SAME
in-process objects rather than each loading their own copy.

Benefit: on a typical 8 GB machine the three MiniLM instances together
consume ~960 MB of RAM. Sharing them saves ~640 MB at startup and
eliminates the redundant initialisation time (~3 s each on cold start).

Usage:
    from model_registry import get_minilm, get_bge_m3, get_reranker

    # 384-dim, all-MiniLM-L6-v2  (legacy verse_embedding + Query + AnswerCache)
    model = get_minilm()
    vec = model.encode("some text", normalize_embeddings=True)

    # 1024-dim, BAAI/bge-m3  (verse_embedding_m3 + verse_embedding_m3_ar)
    model = get_bge_m3()
    vec = model.encode("some text", normalize_embeddings=True, convert_to_numpy=True)

    # CrossEncoder for reranking (BAAI/bge-reranker-v2-m3 by default)
    reranker = get_reranker()   # None if RERANK_DISABLED=1 or RERANKER_MODEL=none

Note on thread safety: SentenceTransformer instances are NOT thread-safe
for concurrent .encode() calls in some versions. The caller (app_free.py)
runs the agent loop in a daemon thread; concurrent requests each get their
own event loop, but the models are shared. In practice this is safe because
encode() releases the GIL for the heavy ONNX/torch work and the objects
themselves are not mutated after load. If you observe race conditions under
high load, wrap get_minilm()/get_bge_m3() with a threading.Lock here.
"""
import os

# ── MiniLM (384-dim) ──────────────────────────────────────────────────────────

_minilm = None
_MINILM_NAME = "all-MiniLM-L6-v2"


def get_minilm():
    """Return (and lazily load) the all-MiniLM-L6-v2 SentenceTransformer."""
    global _minilm
    if _minilm is None:
        from sentence_transformers import SentenceTransformer
        _minilm = SentenceTransformer(_MINILM_NAME)
    return _minilm


# ── BGE-M3 (1024-dim) ────────────────────────────────────────────────────────

_bge_m3 = None
_BGE_M3_NAME = "BAAI/bge-m3"


def get_bge_m3():
    """Return (and lazily load) the BAAI/bge-m3 SentenceTransformer."""
    global _bge_m3
    if _bge_m3 is None:
        from sentence_transformers import SentenceTransformer
        _bge_m3 = SentenceTransformer(_BGE_M3_NAME)
    return _bge_m3


# ── Cross-encoder reranker ────────────────────────────────────────────────────

_reranker = None
_reranker_loaded = False   # distinguish "loaded as None" (disabled) from "not yet loaded"

_DEFAULT_RERANKER = "BAAI/bge-reranker-v2-m3"
_RERANKER_MODEL   = os.environ.get("RERANKER_MODEL", _DEFAULT_RERANKER).strip()
_RERANK_DISABLED  = (
    _RERANKER_MODEL.lower() in ("none", "off", "disabled")
    or os.environ.get("RERANK_DISABLED", "0") == "1"
)


def get_reranker():
    """Return (and lazily load) the reranker CrossEncoder.

    Returns None when reranking is disabled via env
    (RERANKER_MODEL=none or RERANK_DISABLED=1).
    retrieval_gate.py should call get_reranker() instead of its own
    _get_reranker() once it migrates; the existing _get_reranker() in
    retrieval_gate.py is left in place for backward compatibility.
    """
    global _reranker, _reranker_loaded
    if _reranker_loaded:
        return _reranker
    if not _RERANK_DISABLED:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(_RERANKER_MODEL)
    _reranker_loaded = True
    return _reranker
