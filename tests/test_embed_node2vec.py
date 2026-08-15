import networkx as nx
import numpy as np

from tdacn.embed.node2vec_embed import train_node2vec


def _toy_graph():
    g = nx.Graph()
    g.add_weighted_edges_from(
        [
            ("A", "B", 1.0),
            ("B", "C", 1.0),
            ("A", "C", 1.0),
            ("D", "E", 1.0),
            ("E", "F", 1.0),
            ("D", "F", 1.0),
        ]
    )
    g.add_node("Z")  # isolated node, no edges
    return g


def test_train_node2vec_returns_a_vector_of_the_requested_dimension_per_node():
    graph = _toy_graph()

    vectors = train_node2vec(
        graph, dimensions=4, walk_length=5, num_walks=3, seed=42, workers=1
    )

    assert set(vectors.keys()) == set(graph.nodes)
    for vec in vectors.values():
        assert vec.shape == (4,)


def test_train_node2vec_is_deterministic_given_a_fixed_seed():
    graph = _toy_graph()

    v1 = train_node2vec(
        graph, dimensions=4, walk_length=5, num_walks=3, seed=42, workers=1
    )
    v2 = train_node2vec(
        graph, dimensions=4, walk_length=5, num_walks=3, seed=42, workers=1
    )

    for node in graph.nodes:
        assert np.allclose(v1[node], v2[node])


def test_train_node2vec_gives_isolated_nodes_a_vector_too():
    graph = _toy_graph()

    vectors = train_node2vec(
        graph, dimensions=4, walk_length=5, num_walks=3, seed=42, workers=1
    )

    assert "Z" in vectors
    assert vectors["Z"].shape == (4,)
