import numpy as np
import pytest

from tdacn.embed.align import align_periods, procrustes_align


def test_procrustes_align_recovers_a_known_rotation_on_anchor_concepts():
    rng = np.random.default_rng(0)
    target_points = rng.normal(size=(6, 3))
    target_vectors = {f"C{i}": target_points[i] for i in range(6)}

    theta = np.pi / 3
    rotation = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )
    # source = target rotated by a known rotation -> alignment should undo it.
    source_vectors = {
        concept_id: rotation @ vec for concept_id, vec in target_vectors.items()
    }

    aligned = procrustes_align(source_vectors, target_vectors)

    for concept_id in target_vectors:
        assert aligned[concept_id] == pytest.approx(
            target_vectors[concept_id], abs=1e-6
        )


def test_procrustes_align_applies_the_learned_rotation_to_non_anchor_concepts():
    rng = np.random.default_rng(1)
    target_points = rng.normal(size=(6, 3))
    target_vectors = {f"C{i}": target_points[i] for i in range(6)}

    theta = np.pi / 4
    rotation = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )
    source_vectors = {
        concept_id: rotation @ vec for concept_id, vec in target_vectors.items()
    }
    # "NewConcept" only exists in source (not an anchor -- absent from target).
    new_point = rng.normal(size=3)
    source_vectors["NewConcept"] = rotation @ new_point

    aligned = procrustes_align(source_vectors, target_vectors)

    assert aligned["NewConcept"] == pytest.approx(new_point, abs=1e-6)


def test_procrustes_align_raises_when_too_few_shared_anchors():
    target_vectors = {"A": np.array([1.0, 0.0]), "B": np.array([0.0, 1.0])}
    source_vectors = {"C": np.array([1.0, 1.0])}  # no overlap with target

    with pytest.raises(ValueError, match="anchor"):
        procrustes_align(source_vectors, target_vectors)


def _rotation_2d(theta):
    return np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])


def test_align_periods_chains_each_period_onto_the_previous_aligned_space():
    rng = np.random.default_rng(2)
    base = {f"C{i}": rng.normal(size=2) for i in range(6)}

    r1 = _rotation_2d(np.pi / 6)
    r2 = _rotation_2d(np.pi / 5)
    raw = {
        "Q1": base,
        "Q2": {c: r1 @ v for c, v in base.items()},
        # Q3 is built by rotating Q2's raw vectors -- i.e. doubly rotated
        # relative to Q1 -- so correctly undoing it requires chaining
        # through Q2's *aligned* space, not aligning straight onto Q1.
        "Q3": {c: r2 @ (r1 @ v) for c, v in base.items()},
    }

    aligned = align_periods(raw, period_order=["Q1", "Q2", "Q3"])

    for c in base:
        assert aligned["Q1"][c] == pytest.approx(base[c])
        assert aligned["Q2"][c] == pytest.approx(base[c], abs=1e-6)
        assert aligned["Q3"][c] == pytest.approx(base[c], abs=1e-6)
