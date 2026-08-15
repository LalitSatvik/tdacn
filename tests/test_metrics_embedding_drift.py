import numpy as np
import pytest

from tdacn.metrics.embedding_drift import consecutive_cosine_drift, neighbor_jaccard_drift


def test_consecutive_cosine_drift_matches_hand_computed_distance():
    aligned = {
        "Q1": {"A": np.array([1.0, 0.0]), "B": np.array([0.0, 1.0])},
        "Q2": {"A": np.array([0.0, 1.0]), "B": np.array([0.0, 1.0])},  # A rotated 90deg, B unchanged
    }

    out = consecutive_cosine_drift(aligned, period_order=["Q1", "Q2"])
    drift = out.set_index("concept_id")["cosine_distance"]

    # cosine_similarity(A_Q1, A_Q2) = 0 -> distance = 1 - 0 = 1
    assert drift["A"] == pytest.approx(1.0)
    # B unchanged -> distance = 0
    assert drift["B"] == pytest.approx(0.0)


def test_consecutive_cosine_drift_restricted_to_concepts_present_in_both_periods():
    aligned = {
        "Q1": {"A": np.array([1.0, 0.0]), "GoneNextQuarter": np.array([1.0, 1.0])},
        "Q2": {"A": np.array([1.0, 0.0]), "NewThisQuarter": np.array([1.0, 1.0])},
    }

    out = consecutive_cosine_drift(aligned, period_order=["Q1", "Q2"])

    assert set(out["concept_id"]) == {"A"}


def test_consecutive_cosine_drift_covers_every_consecutive_pair():
    aligned = {
        "Q1": {"A": np.array([1.0, 0.0])},
        "Q2": {"A": np.array([1.0, 0.0])},
        "Q3": {"A": np.array([0.0, 1.0])},
    }

    out = consecutive_cosine_drift(aligned, period_order=["Q1", "Q2", "Q3"])

    pairs = set(zip(out["period_a"], out["period_b"]))
    assert pairs == {("Q1", "Q2"), ("Q2", "Q3")}


def test_neighbor_jaccard_drift_matches_hand_computed_overlap():
    # Q1: A's nearest neighbor (by cosine) among {B, C} is B (identical direction).
    # Q2: A's nearest neighbor is C instead -> neighbor set changes entirely at k=1.
    aligned = {
        "Q1": {
            "A": np.array([1.0, 0.0]),
            "B": np.array([1.0, 0.0]),
            "C": np.array([0.0, 1.0]),
        },
        "Q2": {
            "A": np.array([1.0, 0.0]),
            "B": np.array([0.0, 1.0]),
            "C": np.array([1.0, 0.0]),
        },
    }

    out = neighbor_jaccard_drift(aligned, period_order=["Q1", "Q2"], k=1)
    jaccard = out.set_index("concept_id")["jaccard"]

    assert jaccard["A"] == pytest.approx(0.0)  # neighbor set {B} vs {C} -> no overlap
