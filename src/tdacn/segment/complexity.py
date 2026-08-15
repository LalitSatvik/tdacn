"""Per-filer reporting-complexity score: how much of the concept vocabulary
and statement structure a given entity actually uses in a period.

`n_statements` relies on the optional `stmt` column some adapters (e.g.
sec_dera) attach to `relations`; if a bundle's relations lack it, every
filer gets 0 rather than raising, since the schema doesn't require it.
"""

import pandas as pd

from tdacn.schema import CanonicalBundle


def compute_filer_complexity(bundle: CanonicalBundle, period: str) -> pd.DataFrame:
    facts = bundle.facts[bundle.facts["period"] == period]
    concepts = bundle.concepts[bundle.concepts["period"] == period].set_index(
        "concept_id"
    )["is_custom"]

    n_facts = facts.groupby("entity_id").size().rename("n_facts")

    unique_tags = facts[["entity_id", "concept_id"]].drop_duplicates()
    n_unique_tags = unique_tags.groupby("entity_id").size().rename("n_unique_tags")

    unique_tags = unique_tags.assign(
        is_custom=unique_tags["concept_id"].map(concepts).fillna(False)
    )
    pct_custom = unique_tags.groupby("entity_id")["is_custom"].mean().rename(
        "pct_custom"
    )

    entities = bundle.entities[bundle.entities["period"] == period][["entity_id"]]

    if "stmt" in bundle.relations.columns:
        relations = bundle.relations[bundle.relations["period"] == period]
        n_statements = (
            relations.groupby("source_entity_id")["stmt"]
            .nunique()
            .rename("n_statements")
        )
    else:
        n_statements = pd.Series(dtype=int, name="n_statements")

    out = (
        entities.set_index("entity_id")
        .join([n_unique_tags, pct_custom, n_facts, n_statements])
        .fillna({"n_unique_tags": 0, "pct_custom": 0.0, "n_facts": 0, "n_statements": 0})
        .reset_index()
    )
    out["n_unique_tags"] = out["n_unique_tags"].astype(int)
    out["n_facts"] = out["n_facts"].astype(int)
    out["n_statements"] = out["n_statements"].astype(int)
    return out
