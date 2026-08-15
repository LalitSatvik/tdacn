"""Concept support: how many distinct entities use each concept in a period.

A concept is only promoted to a graph node once it clears a minimum-support
threshold. Without this, one-off custom XBRL extension tags (the vast
majority of the raw vocabulary — see the Q1 smoke test: ~65K distinct tags,
~90% custom) would dominate and drown out genuine structure.
"""

from typing import Set

import pandas as pd

from tdacn.schema import CanonicalBundle


def compute_concept_support(bundle: CanonicalBundle, period: str) -> pd.Series:
    """Number of distinct entities using each concept (via facts or relations) in `period`."""
    facts = bundle.facts[bundle.facts["period"] == period]
    relations = bundle.relations[bundle.relations["period"] == period]

    usage = pd.concat(
        [
            facts[["entity_id", "concept_id"]],
            relations[["source_entity_id", "concept_id_a"]].rename(
                columns={"source_entity_id": "entity_id", "concept_id_a": "concept_id"}
            ),
            relations[["source_entity_id", "concept_id_b"]].rename(
                columns={"source_entity_id": "entity_id", "concept_id_b": "concept_id"}
            ),
        ],
        ignore_index=True,
    ).drop_duplicates()

    return usage.groupby("concept_id")["entity_id"].nunique()


def select_supported_concepts(support: pd.Series, min_support: int) -> Set[str]:
    return set(support[support >= min_support].index)
