import pandas as pd

from tdacn.graph.sparsify import top_k_sparsify


def _pairs(df):
    return set(frozenset(p) for p in zip(df.concept_id_a, df.concept_id_b))


def test_top_k_sparsify_drops_an_edge_ranked_below_k_on_both_sides():
    # A's neighbors: B(5) > C(4) > D(1) -> top-2 excludes D.
    # D's neighbors: E(3) > F(2) > A(1) -> top-2 excludes A.
    # So A-D is below the cutoff on both sides and should be dropped.
    edges = pd.DataFrame(
        [
            {"concept_id_a": "A", "concept_id_b": "B", "weight": 5.0},
            {"concept_id_a": "A", "concept_id_b": "C", "weight": 4.0},
            {"concept_id_a": "A", "concept_id_b": "D", "weight": 1.0},
            {"concept_id_a": "D", "concept_id_b": "E", "weight": 3.0},
            {"concept_id_a": "D", "concept_id_b": "F", "weight": 2.0},
        ]
    )

    kept = _pairs(top_k_sparsify(edges, k=2))

    assert frozenset({"A", "B"}) in kept
    assert frozenset({"A", "C"}) in kept
    assert frozenset({"D", "E"}) in kept
    assert frozenset({"D", "F"}) in kept
    assert frozenset({"A", "D"}) not in kept


def test_top_k_sparsify_keeps_an_edge_that_is_top_ranked_for_only_one_side():
    # F's only edge is to G -> trivially F's top-1, kept even though it's
    # G's weakest edge.
    edges = pd.DataFrame(
        [
            {"concept_id_a": "G", "concept_id_b": "H", "weight": 10.0},
            {"concept_id_a": "G", "concept_id_b": "I", "weight": 9.0},
            {"concept_id_a": "F", "concept_id_b": "G", "weight": 0.1},
            {"concept_id_a": "I", "concept_id_b": "J", "weight": 9.5},
        ]
    )

    kept = _pairs(top_k_sparsify(edges, k=1))

    assert frozenset({"F", "G"}) in kept  # F's only edge
    assert frozenset({"G", "H"}) in kept  # G's top-1
    assert frozenset({"I", "J"}) in kept  # I's top-1
    assert frozenset({"G", "I"}) not in kept  # below top-1 on both sides
