"""Blend the structural and co-reporting edge layers into one weighted graph.

Both layers are kept separately upstream (needed for the layer-comparison
questions), and combined here via a documented alpha weight rather than a
hardcoded constant, so the blend is a first-class, sweepable parameter
(see the alpha-sensitivity robustness check).
"""

import pandas as pd


def blend_edges(
    structural: pd.DataFrame, co_reporting: pd.DataFrame, alpha: float = 0.5
) -> pd.DataFrame:
    merged = pd.merge(
        structural[["concept_id_a", "concept_id_b", "weight"]],
        co_reporting[["concept_id_a", "concept_id_b", "weight"]],
        on=["concept_id_a", "concept_id_b"],
        how="outer",
        suffixes=("_structural", "_co_reporting"),
    ).fillna(0.0)

    merged["weight"] = (
        alpha * merged["weight_structural"] + (1 - alpha) * merged["weight_co_reporting"]
    )
    return merged[["concept_id_a", "concept_id_b", "weight"]]
