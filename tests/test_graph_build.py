import pandas as pd

from tdacn.graph.build import build_graph


def test_build_graph_includes_isolated_nodes_and_weighted_edges():
    supported = {"A", "B", "C", "D"}  # D has no edges
    edges = pd.DataFrame(
        [
            {"concept_id_a": "A", "concept_id_b": "B", "weight": 0.75},
            {"concept_id_a": "A", "concept_id_b": "C", "weight": 0.15},
        ]
    )

    graph = build_graph(supported, edges)

    assert set(graph.nodes) == supported
    assert graph.degree("D") == 0
    assert graph["A"]["B"]["weight"] == 0.75
    assert graph["A"]["C"]["weight"] == 0.15
