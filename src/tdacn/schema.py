"""Canonical schema for the Temporal Drift in Accounting Concept Networks pipeline.

All analysis code (graph construction, embedding, drift metrics, segmentation)
is written against this abstract schema and never touches a dataset's raw
column names directly. A dataset adapter's only job is to produce a
CanonicalBundle; see tdacn.adapters.base.AdapterBase.
"""

from dataclasses import dataclass, fields

import pandas as pd

REQUIRED_COLUMNS = {
    "periods": {"period_id", "order"},
    "entities": {"entity_id", "period", "industry_code", "size_class"},
    "concepts": {"concept_id", "period", "label", "is_custom", "datatype"},
    "facts": {"entity_id", "concept_id", "period", "value", "uom"},
    "relations": {
        "concept_id_a",
        "concept_id_b",
        "period",
        "relation_type",
        "source_entity_id",
    },
}


@dataclass
class CanonicalBundle:
    """The five abstract tables every dataset adapter must produce."""

    periods: pd.DataFrame
    entities: pd.DataFrame
    concepts: pd.DataFrame
    facts: pd.DataFrame
    relations: pd.DataFrame


def validate_bundle(bundle: CanonicalBundle) -> None:
    """Raise ValueError if any table in the bundle is missing required columns."""
    for field in fields(bundle):
        table_name = field.name
        frame = getattr(bundle, table_name)
        required = REQUIRED_COLUMNS[table_name]
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{table_name} is missing required column(s): {sorted(missing)}"
            )
