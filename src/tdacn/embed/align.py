"""Orthogonal Procrustes alignment across independently-trained embeddings.

node2vec is trained fresh per period, so the resulting vector spaces are
arbitrarily rotated/reflected relative to each other even for concepts
whose relationships didn't change at all. This is the standard fix from
diachronic word-embedding research (Hamilton et al. 2016): learn the
rotation that best superimposes one period's embedding onto another using
concepts present in both as anchors, then apply that same rotation to
every vector in the source period (anchors and non-anchors alike) so
drift can be measured as post-alignment distance.
"""

from typing import Dict, List

import numpy as np
from scipy.linalg import orthogonal_procrustes

MIN_ANCHORS = 2


def procrustes_align(
    source_vectors: Dict[str, np.ndarray], target_vectors: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    anchors = sorted(set(source_vectors) & set(target_vectors))
    if len(anchors) < MIN_ANCHORS:
        raise ValueError(
            f"procrustes_align requires at least {MIN_ANCHORS} shared anchor "
            f"concepts between source and target; found {len(anchors)}"
        )

    source_anchor_matrix = np.stack([source_vectors[c] for c in anchors])
    target_anchor_matrix = np.stack([target_vectors[c] for c in anchors])

    rotation, _ = orthogonal_procrustes(source_anchor_matrix, target_anchor_matrix)

    return {
        concept_id: vector @ rotation for concept_id, vector in source_vectors.items()
    }


def align_periods(
    raw_vectors: Dict[str, Dict[str, np.ndarray]], period_order: List[str]
) -> Dict[str, Dict[str, np.ndarray]]:
    """Chain-align each period onto the *previous aligned* period's space.

    The first period in `period_order` is the reference and passes through
    unchanged. Each subsequent period is aligned onto its predecessor's
    already-aligned vectors, not onto raw vectors -- otherwise rotation
    error would compound uncorrected across a long period window.
    """
    aligned = {period_order[0]: raw_vectors[period_order[0]]}
    for previous, current in zip(period_order, period_order[1:]):
        aligned[current] = procrustes_align(raw_vectors[current], aligned[previous])
    return aligned
