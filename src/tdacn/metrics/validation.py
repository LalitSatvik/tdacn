"""Generic bootstrap/permutation primitives for testing whether an observed
drift statistic exceeds what sampling noise (filer turnover) alone would
produce.

These are dataset- and statistic-agnostic: they take arrays and a
statistic function, not domain objects. Wiring them up to actually
resample filers and rebuild the graph/embedding/drift pipeline per
iteration is a separate, much more expensive orchestration step (each
iteration re-runs graph construction + node2vec) left to a dedicated batch
job -- these primitives are what that job would call per iteration.
"""

from typing import Callable, Tuple

import numpy as np


def bootstrap_ci(
    values: np.ndarray,
    statistic_fn: Callable[[np.ndarray], float] = np.mean,
    n_boot: int = 1000,
    ci: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = np.asarray(values)
    stats = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        stats[i] = statistic_fn(sample)

    alpha = (1 - ci) / 2
    low, high = np.quantile(stats, [alpha, 1 - alpha])
    return float(low), float(high)


def permutation_test(
    sample_a: np.ndarray,
    sample_b: np.ndarray,
    statistic_fn: Callable[[np.ndarray, np.ndarray], float] = lambda a, b: np.mean(a)
    - np.mean(b),
    n_perm: int = 1000,
    seed: int = 42,
) -> Tuple[float, float]:
    """Two-sided permutation test: is `statistic_fn(sample_a, sample_b)`
    larger in magnitude than expected under the null that group labels
    don't matter?
    """
    rng = np.random.default_rng(seed)
    observed = statistic_fn(sample_a, sample_b)

    pooled = np.concatenate([sample_a, sample_b])
    n_a = len(sample_a)

    exceed_count = 0
    for _ in range(n_perm):
        shuffled = rng.permutation(pooled)
        perm_stat = statistic_fn(shuffled[:n_a], shuffled[n_a:])
        if abs(perm_stat) >= abs(observed):
            exceed_count += 1

    p_value = exceed_count / n_perm
    return float(observed), float(p_value)
