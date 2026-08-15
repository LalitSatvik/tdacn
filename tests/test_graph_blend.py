import pandas as pd
import pytest

from tdacn.graph.blend import blend_edges


def test_blend_edges_alpha_weights_the_two_layers():
    structural = pd.DataFrame([{"concept_id_a": "A", "concept_id_b": "B", "weight": 1.0}])
    co_reporting = pd.DataFrame(
        [
            {"concept_id_a": "A", "concept_id_b": "B", "weight": 0.5},
            {"concept_id_a": "A", "concept_id_b": "C", "weight": 0.3},
        ]
    )

    out = blend_edges(structural, co_reporting, alpha=0.5)
    weights = out.set_index(["concept_id_a", "concept_id_b"])["weight"]

    assert weights[("A", "B")] == pytest.approx(0.75)  # 0.5*1.0 + 0.5*0.5
    assert weights[("A", "C")] == pytest.approx(0.15)  # 0.5*0 + 0.5*0.3


def test_blend_edges_alpha_one_uses_only_structural_layer():
    structural = pd.DataFrame([{"concept_id_a": "A", "concept_id_b": "B", "weight": 1.0}])
    co_reporting = pd.DataFrame([{"concept_id_a": "A", "concept_id_b": "B", "weight": 100.0}])

    out = blend_edges(structural, co_reporting, alpha=1.0)

    assert out.iloc[0]["weight"] == pytest.approx(1.0)
