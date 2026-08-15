import networkx as nx
import pytest

from tdacn.metrics.global_drift import (
    concept_churn,
    degree_distribution_ks,
    edge_overlap_ratio,
    modularity_trend,
)


def test_edge_overlap_ratio_matches_hand_computed_jaccard():
    g1 = nx.Graph()
    g1.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])
    g2 = nx.Graph()
    g2.add_edges_from([("A", "B"), ("C", "D"), ("D", "E")])

    out = edge_overlap_ratio({"Q1": g1, "Q2": g2}, period_order=["Q1", "Q2"])
    row = out.iloc[0]

    # shared: {A,B},{C,D} = 2; union: {A,B},{B,C},{C,D},{D,E} = 4
    assert row["jaccard"] == pytest.approx(0.5)


def test_degree_distribution_ks_is_zero_for_identical_graphs():
    g = nx.Graph()
    g.add_edges_from([("A", "B"), ("B", "C"), ("C", "D")])

    out = degree_distribution_ks({"Q1": g, "Q2": g}, period_order=["Q1", "Q2"])
    row = out.iloc[0]

    assert row["ks_stat"] == pytest.approx(0.0)
    assert row["p_value"] == pytest.approx(1.0)


def test_concept_churn_matches_hand_computed_entered_exited_and_rate():
    vocab = {"Q1": {"A", "B", "C"}, "Q2": {"B", "C", "D"}}

    out = concept_churn(vocab, period_order=["Q1", "Q2"])
    row = out.iloc[0]

    assert row["entered"] == 1  # D
    assert row["exited"] == 1  # A
    assert row["retained"] == 2  # B, C
    assert row["churn_rate"] == pytest.approx(0.5)  # (1+1) / |union|=4


def test_modularity_trend_matches_networkx_modularity_for_two_disjoint_edges():
    g = nx.Graph()
    g.add_weighted_edges_from([("A", "B", 1.0), ("C", "D", 1.0)])
    labels = {"Q1": {"A": 0, "B": 0, "C": 1, "D": 1}}

    out = modularity_trend({"Q1": g}, labels, period_order=["Q1"])
    row = out.iloc[0]

    expected = nx.algorithms.community.modularity(
        g, [{"A", "B"}, {"C", "D"}], weight="weight"
    )
    assert row["modularity"] == pytest.approx(expected)
