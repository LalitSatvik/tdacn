"""Global (whole-network) drift metrics -- one row per period or period pair,
rather than per concept.
"""

from typing import Dict, List, Set

import networkx as nx
import pandas as pd
from scipy.stats import ks_2samp


def edge_overlap_ratio(
    graphs: Dict[str, nx.Graph], period_order: List[str]
) -> pd.DataFrame:
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        edges_a = {frozenset(e) for e in graphs[period_a].edges()}
        edges_b = {frozenset(e) for e in graphs[period_b].edges()}
        union = edges_a | edges_b
        jaccard = len(edges_a & edges_b) / len(union) if union else float("nan")
        rows.append({"period_a": period_a, "period_b": period_b, "jaccard": jaccard})
    return pd.DataFrame(rows, columns=["period_a", "period_b", "jaccard"])


def degree_distribution_ks(
    graphs: Dict[str, nx.Graph], period_order: List[str]
) -> pd.DataFrame:
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        degrees_a = [d for _, d in graphs[period_a].degree()]
        degrees_b = [d for _, d in graphs[period_b].degree()]
        result = ks_2samp(degrees_a, degrees_b)
        rows.append(
            {
                "period_a": period_a,
                "period_b": period_b,
                "ks_stat": result.statistic,
                "p_value": result.pvalue,
            }
        )
    return pd.DataFrame(rows, columns=["period_a", "period_b", "ks_stat", "p_value"])


def concept_churn(
    vocab_by_period: Dict[str, Set[str]], period_order: List[str]
) -> pd.DataFrame:
    rows = []
    for period_a, period_b in zip(period_order, period_order[1:]):
        vocab_a = vocab_by_period[period_a]
        vocab_b = vocab_by_period[period_b]
        entered = vocab_b - vocab_a
        exited = vocab_a - vocab_b
        retained = vocab_a & vocab_b
        union = vocab_a | vocab_b
        churn_rate = (len(entered) + len(exited)) / len(union) if union else float("nan")
        rows.append(
            {
                "period_a": period_a,
                "period_b": period_b,
                "entered": len(entered),
                "exited": len(exited),
                "retained": len(retained),
                "churn_rate": churn_rate,
            }
        )
    return pd.DataFrame(
        rows,
        columns=["period_a", "period_b", "entered", "exited", "retained", "churn_rate"],
    )


def modularity_trend(
    graphs: Dict[str, nx.Graph],
    labels_by_period: Dict[str, Dict[str, int]],
    period_order: List[str],
) -> pd.DataFrame:
    rows = []
    for period in period_order:
        labels = labels_by_period[period]
        communities: Dict[int, set] = {}
        for node, label in labels.items():
            communities.setdefault(label, set()).add(node)
        modularity = nx.algorithms.community.modularity(
            graphs[period], communities.values(), weight="weight"
        )
        rows.append({"period": period, "modularity": modularity})
    return pd.DataFrame(rows, columns=["period", "modularity"])
