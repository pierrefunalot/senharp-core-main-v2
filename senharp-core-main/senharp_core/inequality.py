"""Simple distributional indicators used by SEN-HARP validation."""

from __future__ import annotations

import numpy as np


def gini(values) -> float:
    """Return the Gini coefficient of finite non-negative observations."""
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return 0.0
    if np.any(array < 0.0):
        raise ValueError("Gini observations must be non-negative.")
    total = float(array.sum())
    if total <= 0.0:
        return 0.0
    ordered = np.sort(array)
    ranks = np.arange(1, ordered.size + 1, dtype=float)
    return float(
        (2.0 * np.sum(ranks * ordered) / (ordered.size * total))
        - (ordered.size + 1.0) / ordered.size
    )

