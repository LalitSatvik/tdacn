"""Attribute each concept to a segment profile based on the entities that
actually report it, without rebuilding a separate per-segment graph.

Rebuilding a fully independent graph+embedding per (industry, period) is
methodologically cleaner but re-runs the whole expensive pipeline once per
segment; this cheaper alternative reuses the already-trained full-
population embeddings and asks "what kind of filer reports this concept,
on average" so drift can still be regressed against industry/size/
complexity. See segment.industry / segment.complexity for the true
per-segment-subgraph approach when that compute budget is available.
"""

import pandas as pd

from tdacn.schema import CanonicalBundle
from tdacn.segment.industry import sic_to_division


def concept_segment_profile(
    bundle: CanonicalBundle, period: str, complexity: pd.DataFrame
) -> pd.DataFrame:
    facts = bundle.facts[bundle.facts["period"] == period][
        ["entity_id", "concept_id"]
    ].drop_duplicates()
    entities = bundle.entities[bundle.entities["period"] == period].copy()
    entities["division"] = entities["industry_code"].map(sic_to_division)

    merged = facts.merge(entities, on="entity_id").merge(complexity, on="entity_id")

    def _plurality(series):
        modes = series.mode()
        return modes.iloc[0] if len(modes) > 0 else None

    out = merged.groupby("concept_id").agg(
        dominant_industry=("division", _plurality),
        dominant_size_class=("size_class", _plurality),
        mean_complexity=("n_unique_tags", "mean"),
    )
    return out.reset_index()
