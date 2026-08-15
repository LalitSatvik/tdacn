"""Sparsify a dense weighted edge list to each node's top-K strongest edges.

Blended PMI graphs over the full concept vocabulary can be extremely dense
(most common concepts co-occur with most other common concepts), which
makes node2vec's per-edge transition-probability precomputation
intractable. Keeping an edge if it's in either endpoint's top-K neighbor
list is standard practice for turning a dense similarity graph into a
tractable kNN-style graph, and preserves each node's strongest
relationships even when its neighbor is a much higher-degree hub.
"""

import pandas as pd


def top_k_sparsify(edges: pd.DataFrame, k: int) -> pd.DataFrame:
    directed = pd.concat(
        [
            edges.rename(columns={"concept_id_a": "node", "concept_id_b": "neighbor"}),
            edges.rename(
                columns={"concept_id_b": "node", "concept_id_a": "neighbor"}
            ),
        ],
        ignore_index=True,
    )

    top = (
        directed.sort_values("weight", ascending=False)
        .groupby("node")
        .head(k)
    )
    kept_pairs = set(
        frozenset(pair) for pair in zip(top["node"], top["neighbor"])
    )

    mask = edges.apply(
        lambda row: frozenset((row["concept_id_a"], row["concept_id_b"])) in kept_pairs,
        axis=1,
    )
    return edges[mask].reset_index(drop=True)
