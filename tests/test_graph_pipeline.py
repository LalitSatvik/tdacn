import pandas as pd

from tdacn.graph.pipeline import build_period_graph
from tdacn.schema import CanonicalBundle


def _bundle():
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
        {
            "entity_id": ["e1", "e1", "e2", "e2", "e2", "e3", "e3", "e4"],
            "concept_id": ["A", "B", "A", "B", "C", "A", "C", "D"],
            "period": ["Q1"] * 8,
            "value": [1.0] * 8,
            "uom": ["USD"] * 8,
        }
    )
    relations = pd.DataFrame(
        {
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


def test_build_period_graph_prunes_below_threshold_and_weights_edges():
    bundle = _bundle()

    graph = build_period_graph(bundle, "Q1", min_support=2, alpha=0.5)

    # D has support 1 (only e4) -> pruned below min_support=2.
    assert set(graph.nodes) == {"A", "B", "C"}
    assert graph.has_edge("A", "B")
    assert graph["A"]["B"]["weight"] > 0


def test_build_period_graph_applies_top_k_sparsification_when_requested():
    bundle = _bundle()

    full = build_period_graph(bundle, "Q1", min_support=2, alpha=0.5, top_k=None)
    sparsified = build_period_graph(bundle, "Q1", min_support=2, alpha=0.5, top_k=1)

    # Nodes are unchanged by sparsification; only edges may be pruned.
    assert set(sparsified.nodes) == set(full.nodes)
    assert sparsified.number_of_edges() <= full.number_of_edges()
