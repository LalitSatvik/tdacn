"""Embedding-based drift metrics (Approach A): distance and neighborhood
change of a concept's Procrustes-aligned vector, quarter to quarter.
"""

from typing import Dict, List

import numpy as np
import pandas as pd


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return np.nan
    return 1.0 - float(np.dot(a, b) / denom)


def consecutive_cosine_drift(
    aligned_vectors: Dict[str, Dict[str, np.ndarray]], period_order: List[str]
) -> pd.DataFrame:
    """Cosine distance per concept for each consecutive period pair.

    A concept only appears in the output for pairs where it exists in both
    periods -- vocabulary churn (concepts entering/leaving) is a separate
    metric, not something this silently imputes around.
    """
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        vecs_a = aligned_vectors[period_a]
        vecs_b = aligned_vectors[period_b]
        shared = set(vecs_a) & set(vecs_b)
        for concept_id in shared:
            rows.append(
                {
                    "concept_id": concept_id,
                    "period_a": period_a,
                    "period_b": period_b,
                    "cosine_distance": _cosine_distance(
                        vecs_a[concept_id], vecs_b[concept_id]
                    ),
                }
            )
    return pd.DataFrame(rows, columns=["concept_id", "period_a", "period_b", "cosine_distance"])


def _top_k_neighbors(vectors: Dict[str, np.ndarray], concept_id: str, k: int):
    target = vectors[concept_id]
    others = [c for c in vectors if c != concept_id]
    sims = {c: 1.0 - _cosine_distance(target, vectors[c]) for c in others}
    ranked = sorted(sims.items(), key=lambda kv: kv[1], reverse=True)
    return {c for c, _ in ranked[:k]}


def neighbor_jaccard_drift(
    aligned_vectors: Dict[str, Dict[str, np.ndarray]],
    period_order: List[str],
    k: int = 10,
) -> pd.DataFrame:
    """Jaccard overlap of each concept's top-k nearest neighbors across periods.

    Nearest neighbors are computed within each period's own concept set
    (cosine similarity is rotation-invariant, so this is unaffected by
    whether vectors are pre- or post-alignment).
    """
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        vecs_a = aligned_vectors[period_a]
        vecs_b = aligned_vectors[period_b]
        shared = set(vecs_a) & set(vecs_b)
        for concept_id in shared:
            neighbors_a = _top_k_neighbors(vecs_a, concept_id, k)
            neighbors_b = _top_k_neighbors(vecs_b, concept_id, k)
            union = neighbors_a | neighbors_b
            jaccard = len(neighbors_a & neighbors_b) / len(union) if union else np.nan
            rows.append(
                {
                    "concept_id": concept_id,
                    "period_a": period_a,
                    "period_b": period_b,
                    "jaccard": jaccard,
                }
            )
    return pd.DataFrame(rows, columns=["concept_id", "period_a", "period_b", "jaccard"])
