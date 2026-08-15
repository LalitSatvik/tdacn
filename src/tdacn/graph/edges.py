"""Two edge layers over supported concepts: structural (presentation
adjacency, from relations) and co-reporting (concepts a filer reports
together, from facts). Both produce the same shape:
DataFrame[concept_id_a, concept_id_b, weight], one undirected row per pair,
weight = number of distinct entities contributing that pair.
"""

from typing import Set

import numpy as np
import pandas as pd
from scipy import sparse

from tdacn.schema import CanonicalBundle


def _normalize_pair_order(df: pd.DataFrame) -> pd.DataFrame:
    a = df["concept_id_a"].where(
        df["concept_id_a"] < df["concept_id_b"], df["concept_id_b"]
    )
    b = df["concept_id_b"].where(
        df["concept_id_a"] < df["concept_id_b"], df["concept_id_a"]
    )
    out = df.copy()
    out["concept_id_a"] = a
    out["concept_id_b"] = b
    return out


def build_structural_edges(
    bundle: CanonicalBundle, period: str, supported_concepts: Set[str]
) -> pd.DataFrame:
    relations = bundle.relations[bundle.relations["period"] == period]
    relations = relations[
        relations["concept_id_a"].isin(supported_concepts)
        & relations["concept_id_b"].isin(supported_concepts)
        & (relations["concept_id_a"] != relations["concept_id_b"])
    ]

    pairs = _normalize_pair_order(
        relations[["concept_id_a", "concept_id_b", "source_entity_id"]]
    ).drop_duplicates()

    counts = (
        pairs.groupby(["concept_id_a", "concept_id_b"])
        .size()
        .reset_index(name="weight")
    )
    return counts


def build_co_reporting_edges(
    bundle: CanonicalBundle, period: str, supported_concepts: Set[str]
) -> pd.DataFrame:
    facts = bundle.facts[bundle.facts["period"] == period]
    facts = facts[facts["concept_id"].isin(supported_concepts)]

    incidence = facts[["entity_id", "concept_id"]].drop_duplicates()
    if incidence.empty:
        return pd.DataFrame(columns=["concept_id_a", "concept_id_b", "weight"])

    entities = pd.Index(incidence["entity_id"].unique())
    concepts = pd.Index(sorted(incidence["concept_id"].unique()))

    row_idx = entities.get_indexer(incidence["entity_id"])
    col_idx = concepts.get_indexer(incidence["concept_id"])
    data = np.ones(len(incidence), dtype=np.int64)

    matrix = sparse.csr_matrix(
        (data, (row_idx, col_idx)), shape=(len(entities), len(concepts))
    )
    co_occurrence = (matrix.T @ matrix).tocoo()

    upper = co_occurrence.row < co_occurrence.col
    return pd.DataFrame(
        {
            "concept_id_a": concepts[co_occurrence.row[upper]],
            "concept_id_b": concepts[co_occurrence.col[upper]],
            "weight": co_occurrence.data[upper],
        }
    )
