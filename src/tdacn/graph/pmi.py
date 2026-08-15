"""Pointwise mutual information weighting for co-occurrence edge counts.

Raw counts are biased toward whichever period has more filers. PMI
normalizes against each concept's marginal frequency, so an edge weight
reflects genuine association strength rather than sample size — important
here since filer counts swing ~20% quarter to quarter.
"""

import numpy as np
import pandas as pd


def pmi_weight(
    counts: pd.DataFrame,
    concept_support: pd.Series,
    total_entities: int,
    positive: bool = True,
) -> pd.DataFrame:
    out = counts.copy()
    p_ab = out["weight"] / total_entities
    p_a = out["concept_id_a"].map(concept_support) / total_entities
    p_b = out["concept_id_b"].map(concept_support) / total_entities

    out["pmi"] = np.log(p_ab / (p_a * p_b))
    out["weight"] = out["pmi"].clip(lower=0) if positive else out["pmi"]
    return out
