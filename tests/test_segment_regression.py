import numpy as np
import pandas as pd
import pytest

from tdacn.segment.regression import fit_ols


def test_fit_ols_recovers_a_known_group_difference():
    rng = np.random.default_rng(0)
    n = 200
    industry = np.array(["A"] * (n // 2) + ["B"] * (n // 2))
    # True effect: industry B has 0.6 higher drift than industry A.
    drift = np.where(industry == "A", 0.2, 0.8) + rng.normal(scale=0.05, size=n)
    data = pd.DataFrame({"drift": drift, "industry": industry})

    result = fit_ols(data, "drift ~ C(industry)")

    coef = result.params["C(industry)[T.B]"]
    assert coef == pytest.approx(0.6, abs=0.05)
    assert result.pvalues["C(industry)[T.B]"] < 0.01


def test_fit_ols_supports_cluster_robust_standard_errors():
    rng = np.random.default_rng(1)
    n = 100
    data = pd.DataFrame(
        {
            "drift": rng.normal(size=n),
            "x": rng.normal(size=n),
            "cluster_id": rng.integers(0, 10, size=n),
        }
    )

    result = fit_ols(data, "drift ~ x", cluster_col="cluster_id")

    # Cluster-robust fit should still produce a coefficient + p-value for x.
    assert "x" in result.params.index
    assert 0.0 <= result.pvalues["x"] <= 1.0
