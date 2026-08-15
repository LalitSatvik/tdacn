import networkx as nx
import pytest

from tdacn.metrics.graph_drift import centrality_drift, community_drift, compute_communities


def test_centrality_drift_matches_hand_computed_degree_centrality_delta():
    g_q1 = nx.Graph()
    g_q1.add_edges_from([("A", "B"), ("A", "C")])
    g_q1.add_node("D")  # isolated

    g_q2 = nx.Graph()
    g_q2.add_edges_from([("A", "B"), ("A", "C"), ("A", "D")])

    out = centrality_drift(
        {"Q1": g_q1, "Q2": g_q2}, period_order=["Q1", "Q2"], centrality_fn=nx.degree_centrality
    )
    delta = out.set_index("concept_id")["delta"]

    # degree_centrality = degree / (n-1), n=4 -> denom=3
    assert delta["A"] == pytest.approx(1.0 - 2 / 3)
    assert delta["B"] == pytest.approx(0.0)
    assert delta["D"] == pytest.approx(1 / 3 - 0.0)


def test_community_drift_is_perfect_agreement_for_identical_partitions():
    labels_q1 = {"A": 0, "B": 0, "C": 1, "D": 1}
    labels_q2 = {"A": 0, "B": 0, "C": 1, "D": 1}

    out = community_drift({"Q1": labels_q1, "Q2": labels_q2}, period_order=["Q1", "Q2"])
    row = out.iloc[0]

    assert row["nmi"] == pytest.approx(1.0)
    assert row["ari"] == pytest.approx(1.0)


def test_community_drift_is_imperfect_for_a_reshuffled_partition():
    labels_q1 = {"A": 0, "B": 0, "C": 1, "D": 1}
    labels_q2 = {"A": 0, "B": 1, "C": 0, "D": 1}  # different grouping

    out = community_drift({"Q1": labels_q1, "Q2": labels_q2}, period_order=["Q1", "Q2"])
    row = out.iloc[0]

    assert row["nmi"] < 1.0
    assert row["ari"] < 1.0


def test_compute_communities_returns_a_label_per_node():
    g = nx.Graph()
    g.add_weighted_edges_from([("A", "B", 1.0), ("B", "C", 1.0), ("D", "E", 1.0)])

    labels = compute_communities(g, seed=42)

    assert set(labels.keys()) == set(g.nodes)
