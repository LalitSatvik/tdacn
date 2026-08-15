import numpy as np
import pytest

from tdacn.metrics.validation import bootstrap_ci, permutation_test


def test_bootstrap_ci_brackets_the_true_mean_of_a_known_distribution():
    values = np.arange(1, 101)  # mean = 50.5

    low, high = bootstrap_ci(values, statistic_fn=np.mean, n_boot=500, seed=42)

    assert low < 50.5 < high


def test_bootstrap_ci_is_deterministic_given_a_fixed_seed():
    values = np.arange(1, 101)

    ci_1 = bootstrap_ci(values, statistic_fn=np.mean, n_boot=200, seed=7)
    ci_2 = bootstrap_ci(values, statistic_fn=np.mean, n_boot=200, seed=7)

    assert ci_1 == ci_2


def test_permutation_test_detects_a_clear_difference_between_samples():
    rng = np.random.default_rng(0)
    sample_a = rng.normal(loc=10, scale=1, size=50)
    sample_b = rng.normal(loc=0, scale=1, size=50)

    observed, p_value = permutation_test(sample_a, sample_b, n_perm=500, seed=42)

    assert observed == pytest.approx(sample_a.mean() - sample_b.mean())
    assert p_value < 0.05


def test_permutation_test_gives_p_value_one_for_identical_samples():
    sample = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    observed, p_value = permutation_test(sample, sample, n_perm=200, seed=42)

    assert observed == pytest.approx(0.0)
    assert p_value == pytest.approx(1.0)
