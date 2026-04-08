"""
Uncertainty Quantification — Phase 5 of hallucination reduction.

Detects when Claude is uncertain about a question using Semantic Entropy:
  1. Generate N short probe responses with Haiku (temperature 0.7)
  2. Compute pairwise semantic similarity between probes
  3. High entropy (low agreement) = model is uncertain = flag or abstain

This runs BEFORE the main retrieval pipeline. If entropy is very high,
the system can warn the user or add a confidence qualifier.
"""

import numpy as np


def _get_probe_model():
    """Return the fast/cheap model ID for probes."""
    return "claude-haiku-4-5-20251001"


def generate_probes(question: str, client, n: int = 5) -> list[str]:
    """
    Generate N short probe responses using Haiku at temperature 0.7.
    These are quick, cheap answers — not the final response.
    """
    probes = []
    for _ in range(n):
        try:
            resp = client.messages.create(
                model=_get_probe_model(),
                max_tokens=300,
                temperature=0.7,
                messages=[{"role": "user", "content": question}],
                system=(
                    "You are a Quran scholar. Give a brief answer (2-3 sentences) "
                    "about what the Quran says on this topic. If the Quran does not "
                    "address this topic, say so clearly."
                ),
            )
            text = resp.content[0].text.strip()
            if text:
                probes.append(text)
        except Exception:
            pass
    return probes


def compute_entropy(probes: list[str], embedding_model=None) -> dict:
    """
    Compute semantic entropy from probe responses.

    Uses embedding similarity to measure agreement between probes.
    Returns:
        entropy: float 0-1 (0 = all probes agree, 1 = total disagreement)
        agreement: float 0-1 (inverse of entropy)
        mean_similarity: average pairwise cosine similarity
        probe_count: number of probes used
    """
    if len(probes) < 2:
        return {"entropy": 0.0, "agreement": 1.0, "mean_similarity": 1.0,
                "probe_count": len(probes)}

    # Load embedding model if not provided
    if embedding_model is None:
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    # Embed all probes
    embeddings = embedding_model.encode(probes, normalize_embeddings=True)

    # Compute pairwise cosine similarity
    sim_matrix = np.dot(embeddings, embeddings.T)

    # Average off-diagonal similarities
    n = len(probes)
    total_sim = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_sim += sim_matrix[i][j]
            count += 1

    mean_sim = total_sim / count if count > 0 else 1.0

    # Convert similarity to entropy: low similarity = high entropy
    # Clamp to [0, 1] range
    entropy = max(0.0, min(1.0, 1.0 - mean_sim))

    return {
        "entropy": round(float(entropy), 4),
        "agreement": round(float(mean_sim), 4),
        "mean_similarity": round(float(mean_sim), 4),
        "probe_count": n,
    }


def assess_uncertainty(question: str, client, embedding_model=None,
                       n_probes: int = 5) -> dict:
    """
    Full uncertainty assessment pipeline.

    Returns dict with:
        entropy: 0-1
        agreement: 0-1
        confidence: "high" | "medium" | "low"
        should_abstain: bool (True if entropy is very high)
        probe_count: int
    """
    probes = generate_probes(question, client, n=n_probes)
    result = compute_entropy(probes, embedding_model)

    entropy = result["entropy"]

    if entropy < 0.25:
        confidence = "high"
        should_abstain = False
    elif entropy < 0.45:
        confidence = "medium"
        should_abstain = False
    else:
        confidence = "low"
        should_abstain = True

    result["confidence"] = confidence
    result["should_abstain"] = should_abstain
    return result
