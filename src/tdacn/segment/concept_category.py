"""Classify concepts into dei / abstract-header / dimensional / accounting-fact.

The "most-drifting concepts" question only makes sense for real accounting
facts -- cover-page metadata (dei:) and structural scaffolding
(Abstract/Domain/Member tags) drift for different reasons and would
otherwise dominate a naive top-movers list. Classification uses the
taxonomy's own metadata (namespace, abstract flag, datatype) rather than
tag-name pattern matching, so it stays correct as the vocabulary evolves.

Relies on the optional `namespace`/`is_abstract` columns some adapters
(e.g. sec_dera) attach to `concepts`; a bundle without them falls back to
`datatype` alone (still distinguishes dimensional from fact concepts).
"""

import pandas as pd

_DIMENSIONAL_DATATYPES = {"domain", "member"}


def classify_concepts(concepts: pd.DataFrame) -> pd.DataFrame:
    out = concepts.copy()
    namespace = out["namespace"] if "namespace" in out.columns else ""
    is_abstract = out["is_abstract"] if "is_abstract" in out.columns else False

    category = pd.Series("accounting_fact", index=out.index)
    category = category.mask(out["datatype"].isin(_DIMENSIONAL_DATATYPES), "dimensional")
    category = category.mask(pd.Series(is_abstract, index=out.index) == True, "abstract_header")  # noqa: E712
    category = category.mask(pd.Series(namespace, index=out.index) == "dei", "dei")

    out["category"] = category
    return out
