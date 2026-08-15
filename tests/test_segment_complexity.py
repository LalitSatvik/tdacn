import pandas as pd
import pytest

from tdacn.schema import CanonicalBundle
from tdacn.segment.complexity import compute_filer_complexity


def _bundle():
    periods = pd.DataFrame({"period_id": ["Q1"], "order": [0]})
    entities = pd.DataFrame(
        {
            "entity_id": ["e1", "e2"],
            "period": ["Q1", "Q1"],
            "industry_code": ["73", "60"],
            "size_class": ["1-LAF", "4-NON"],
        }
    )
    concepts = pd.DataFrame(
        {
            "concept_id": ["Assets", "Liabilities", "MyCustomKPI"],
            "period": ["Q1"] * 3,
            "label": ["Assets", "Liabilities", "My Custom KPI"],
            "is_custom": [False, False, True],
            "datatype": ["monetary"] * 3,
        }
    )
    # e1: 3 facts, 3 unique concepts (1 custom), reports on BS and IS.
    # e2: 2 facts, 1 unique concept, reports on BS only.
    facts = pd.DataFrame(
        {
            "entity_id": ["e1", "e1", "e1", "e2", "e2"],
            "concept_id": ["Assets", "Liabilities", "MyCustomKPI", "Assets", "Assets"],
            "period": ["Q1"] * 5,
            "value": [1.0] * 5,
            "uom": ["USD"] * 5,
        }
    )
    relations = pd.DataFrame(
        {
            "concept_id_a": ["Assets", "Assets"],
            "concept_id_b": ["Liabilities", "MyCustomKPI"],
            "period": ["Q1", "Q1"],
            "relation_type": ["structural", "structural"],
            "source_entity_id": ["e1", "e1"],
            "stmt": ["BS", "IS"],
        }
    )
    return CanonicalBundle(periods, entities, concepts, facts, relations)


def test_compute_filer_complexity_matches_hand_computed_features():
    bundle = _bundle()

    out = compute_filer_complexity(bundle, "Q1").set_index("entity_id")

    e1 = out.loc["e1"]
    assert e1["n_unique_tags"] == 3
    assert e1["n_facts"] == 3
    assert e1["pct_custom"] == pytest.approx(1 / 3)
    assert e1["n_statements"] == 2  # BS, IS

    e2 = out.loc["e2"]
    assert e2["n_unique_tags"] == 1
    assert e2["n_facts"] == 2
    assert e2["pct_custom"] == pytest.approx(0.0)
    assert e2["n_statements"] == 0  # no relations rows for e2
