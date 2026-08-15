"""OLS wrapper for the inferential segmentation question: does drift
differ *systematically* by industry/size/complexity, not just
descriptively? A thin wrapper so callers pass a formula string
(e.g. "cosine_distance ~ C(dominant_industry) + C(dominant_size_class) +
mean_complexity + degree_q1") rather than hand-building design matrices.
"""

import pandas as pd
import statsmodels.formula.api as smf


def fit_ols(data: pd.DataFrame, formula: str, cluster_col: str = None):
    model = smf.ols(formula, data=data)
    if cluster_col is not None:
        return model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster_col]})
    return model.fit()
