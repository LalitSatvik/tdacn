"""Plan's built-in validation: an identical graph fed as both periods must
show ~zero drift end-to-end. Graph-theoretic metrics (computed directly
from the graph) should be *exactly* zero; embedding-based metrics involve
node2vec's inherent training noise, so are checked to be small rather than
exactly zero.
"""

import networkx as nx
import pytest

from tdacn.embed.align import align_periods
from tdacn.embed.node2vec_embed import train_node2vec
from tdacn.metrics.embedding_drift import consecutive_cosine_drift
from tdacn.metrics.graph_drift import centrality_drift


def _connected_random_graph(seed=7, n=25, m=60):
    g = nx.gnm_random_graph(n, m, seed=seed)
    assert nx.is_connected(g), "fixture graph must be connected for this sanity check"
    for u, v in g.edges():
        g[u][v]["weight"] = 1.0
    return nx.relabel_nodes(g, {i: f"C{i}" for i in g.nodes})


def test_identical_graph_gives_exactly_zero_graph_theoretic_drift():
    graph = _connected_random_graph()

    out = centrality_drift(
        {"Q1": graph, "Q2": graph}, period_order=["Q1", "Q2"], centrality_fn=nx.pagerank
    )

    assert (out["delta"] == 0.0).all()


def test_identical_graph_gives_near_zero_embedding_drift_after_alignment():
    graph = _connected_random_graph()

    raw = {
        "Q1": train_node2vec(graph, dimensions=32, walk_length=20, num_walks=8, seed=1, workers=1),
        # Different seed simulates two independently-trained node2vec runs
        # on the same underlying structure (as if it were re-fit each
        # quarter) -- the point of Procrustes alignment is to remove the
        # resulting arbitrary rotation before measuring drift.
        "Q2": train_node2vec(graph, dimensions=32, walk_length=20, num_walks=8, seed=2, workers=1),
    }
    aligned = align_periods(raw, period_order=["Q1", "Q2"])

    out = consecutive_cosine_drift(aligned, period_order=["Q1", "Q2"])

    assert out["cosine_distance"].mean() < 0.1
