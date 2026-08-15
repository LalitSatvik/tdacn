import math

import pandas as pd
import pytest

from tdacn.graph.pmi import pmi_weight


def test_pmi_weight_matches_hand_computed_value():
    counts = pd.DataFrame(
        [{"concept_id_a": "A", "concept_id_b": "B", "weight": 2}]
    )
    support = pd.Series({"A": 3, "B": 2})

    out = pmi_weight(counts, support, total_entities=4)

    # P(A,B)=2/4=0.5, P(A)=3/4=0.75, P(B)=2/4=0.5
    # pmi = log(0.5 / (0.75*0.5)) = log(4/3)
    expected = math.log(4 / 3)
    row = out.iloc[0]
    assert row["pmi"] == pytest.approx(expected)
    assert row["weight"] == pytest.approx(expected)  # positive pmi -> unclipped


def test_pmi_weight_clips_negative_pmi_to_zero_by_default():
    counts = pd.DataFrame(
        [{"concept_id_a": "X", "concept_id_b": "Y", "weight": 1}]
    )
    support = pd.Series({"X": 4, "Y": 4})

    out = pmi_weight(counts, support, total_entities=4)

    row = out.iloc[0]
    assert row["pmi"] < 0  # P(X,Y)=0.25 < P(X)*P(Y)=1.0
    assert row["weight"] == 0.0


def test_pmi_weight_can_return_raw_pmi_unclipped():
    counts = pd.DataFrame(
        [{"concept_id_a": "X", "concept_id_b": "Y", "weight": 1}]
    )
    support = pd.Series({"X": 4, "Y": 4})

    out = pmi_weight(counts, support, total_entities=4, positive=False)

    row = out.iloc[0]
    assert row["weight"] == row["pmi"]
    assert row["weight"] < 0
