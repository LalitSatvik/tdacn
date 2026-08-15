import pandas as pd

from tdacn.graph.support import compute_concept_support, select_supported_concepts
from tdacn.schema import CanonicalBundle


def _bundle(facts_rows, relations_rows=None):
    periods = pd.DataFrame({"period_id": ["Q1"], "order": [0]})
    entities = pd.DataFrame(
        {
            "entity_id": ["e1", "e2", "e3", "e4"],
            "period": ["Q1"] * 4,
            "industry_code": ["73"] * 4,
            "size_class": ["1-LAF"] * 4,
        }
    )
    facts = pd.DataFrame(facts_rows)
    relations = pd.DataFrame(
        relations_rows
        or {
            "concept_id_a": [],
            "concept_id_b": [],
            "period": [],
            "relation_type": [],
            "source_entity_id": [],
        }
    )
    concepts = pd.DataFrame(
        {"concept_id": [], "period": [], "label": [], "is_custom": [], "datatype": []}
    )
    return CanonicalBundle(periods, entities, concepts, facts, relations)


def test_compute_concept_support_counts_distinct_entities_per_concept():
    facts_rows = {
        "entity_id": ["e1", "e1", "e2", "e2", "e2", "e3", "e3", "e4"],
        "concept_id": ["A", "B", "A", "B", "C", "A", "C", "D"],
        "period": ["Q1"] * 8,
        "value": [1.0] * 8,
        "uom": ["USD"] * 8,
    }
    bundle = _bundle(facts_rows)

    support = compute_concept_support(bundle, "Q1")

    assert support.to_dict() == {"A": 3, "B": 2, "C": 2, "D": 1}


def test_compute_concept_support_counts_entities_from_relations_too():
    facts_rows = {"entity_id": [], "concept_id": [], "period": [], "value": [], "uom": []}
    relations_rows = {
        "concept_id_a": ["A", "B"],
        "concept_id_b": ["B", "C"],
        "period": ["Q1", "Q1"],
        "relation_type": ["structural", "structural"],
        "source_entity_id": ["e1", "e2"],
    }
    bundle = _bundle(facts_rows, relations_rows)

    support = compute_concept_support(bundle, "Q1")

    # A,B appear via e1's pair; B,C appear via e2's pair -> B seen by e1 and e2.
    assert support.to_dict() == {"A": 1, "B": 2, "C": 1}


def test_select_supported_concepts_filters_by_threshold():
    support = pd.Series({"A": 3, "B": 2, "C": 2, "D": 1})

    supported = select_supported_concepts(support, min_support=2)

    assert supported == {"A", "B", "C"}
