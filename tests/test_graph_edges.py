import pandas as pd

from tdacn.graph.edges import build_co_reporting_edges, build_structural_edges
from tdacn.schema import CanonicalBundle


def _bundle(facts_rows=None, relations_rows=None):
    periods = pd.DataFrame({"period_id": ["Q1"], "order": [0]})
    entities = pd.DataFrame(
        {
            "entity_id": ["e1", "e2", "e3", "e4"],
            "period": ["Q1"] * 4,
            "industry_code": ["73"] * 4,
            "size_class": ["1-LAF"] * 4,
        }
    )
    facts = pd.DataFrame(
        facts_rows
        or {"entity_id": [], "concept_id": [], "period": [], "value": [], "uom": []}
    )
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


def _edge_weight(df, a, b):
    row = df[
        ((df.concept_id_a == a) & (df.concept_id_b == b))
        | ((df.concept_id_a == b) & (df.concept_id_b == a))
    ]
    assert len(row) == 1, f"expected exactly one row for pair ({a},{b}), found {len(row)}"
    return row.iloc[0]["weight"]


def test_build_co_reporting_edges_counts_distinct_entities_sharing_each_pair():
    facts_rows = {
        "entity_id": ["e1", "e1", "e2", "e2", "e2", "e3", "e3", "e4"],
        "concept_id": ["A", "B", "A", "B", "C", "A", "C", "D"],
        "period": ["Q1"] * 8,
        "value": [1.0] * 8,
        "uom": ["USD"] * 8,
    }
    bundle = _bundle(facts_rows=facts_rows)

    edges = build_co_reporting_edges(bundle, "Q1", supported_concepts={"A", "B", "C"})

    assert _edge_weight(edges, "A", "B") == 2  # e1, e2
    assert _edge_weight(edges, "A", "C") == 2  # e2, e3
    assert _edge_weight(edges, "B", "C") == 1  # e2
    # D excluded entirely: not in supported_concepts.
    assert not ((edges.concept_id_a == "D") | (edges.concept_id_b == "D")).any()
    # No self-pairs, no duplicate (a,b)/(b,a) rows.
    assert (edges.concept_id_a != edges.concept_id_b).all()
    assert len(edges) == 3


def test_build_structural_edges_counts_distinct_entities_per_adjacency():
    relations_rows = {
        "concept_id_a": ["A", "A", "B", "A"],
        "concept_id_b": ["B", "B", "C", "C"],
        "period": ["Q1"] * 4,
        "relation_type": ["structural"] * 4,
        "source_entity_id": ["e1", "e2", "e2", "e3"],
    }
    bundle = _bundle(relations_rows=relations_rows)

    edges = build_structural_edges(bundle, "Q1", supported_concepts={"A", "B", "C"})

    assert _edge_weight(edges, "A", "B") == 2  # e1, e2
    assert _edge_weight(edges, "B", "C") == 1  # e2
    assert _edge_weight(edges, "A", "C") == 1  # e3
    assert len(edges) == 3
