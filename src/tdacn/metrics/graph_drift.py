"""Graph-theoretic drift metrics (Approach C): model-free, computed
directly from each period's graph rather than from embeddings. Serves as
the robustness check against the embedding-based metrics -- if both
methods agree, the finding is credible; if they diverge, that's reported
too (see Q19).
"""

from typing import Callable, Dict, List

import networkx as nx
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score


def centrality_drift(
    graphs: Dict[str, nx.Graph],
    period_order: List[str],
    centrality_fn: Callable[[nx.Graph], Dict[str, float]],
) -> pd.DataFrame:
    """Change in a centrality measure per concept for each consecutive period pair.

    `centrality_fn` is any networkx-style function returning {node: score}
    (e.g. nx.degree_centrality, nx.pagerank, nx.betweenness_centrality) --
    kept generic so one function serves every centrality metric in the plan
    rather than duplicating this loop per metric.
    """
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        scores_a = centrality_fn(graphs[period_a])
        scores_b = centrality_fn(graphs[period_b])
        shared = set(scores_a) & set(scores_b)
        for concept_id in shared:
            rows.append(
                {
                    "concept_id": concept_id,
                    "period_a": period_a,
                    "period_b": period_b,
                    "delta": scores_b[concept_id] - scores_a[concept_id],
                }
            )
    return pd.DataFrame(rows, columns=["concept_id", "period_a", "period_b", "delta"])


def compute_communities(graph: nx.Graph, seed: int = 42) -> Dict[str, int]:
    partition = nx.algorithms.community.louvain_communities(
        graph, weight="weight", seed=seed
    )
    return {node: i for i, community in enumerate(partition) for node in community}


def community_drift(
    labels_by_period: Dict[str, Dict[str, int]], period_order: List[str]
) -> pd.DataFrame:
    """NMI/ARI agreement between community assignments of shared concepts."""
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        labels_a = labels_by_period[period_a]
        labels_b = labels_by_period[period_b]
        shared = sorted(set(labels_a) & set(labels_b))
        y_a = [labels_a[c] for c in shared]
        y_b = [labels_b[c] for c in shared]
        rows.append(
            {
                "period_a": period_a,
                "period_b": period_b,
                "nmi": normalized_mutual_info_score(y_a, y_b),
                "ari": adjusted_rand_score(y_a, y_b),
            }
        )
    return pd.DataFrame(rows, columns=["period_a", "period_b", "nmi", "ari"])
