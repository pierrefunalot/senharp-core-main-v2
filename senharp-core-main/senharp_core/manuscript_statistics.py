"""Auditable non-parametric tests used by the manuscript figures."""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu


def p_value_stars(p_value: float) -> str:
    if not np.isfinite(p_value):
        return "NA"
    if p_value < 0.001:
        return "***"
    if p_value < 0.01:
        return "**"
    if p_value < 0.05:
        return "*"
    return "ns"


def format_p_value(p_value: float) -> str:
    if not np.isfinite(p_value):
        return "p=NA"
    if p_value < 0.001:
        return f"p<0.001 {p_value_stars(p_value)}"
    return f"p={p_value:.3f} {p_value_stars(p_value)}"


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm-adjust a family of p-values, preserving input order."""
    adjusted = [np.nan] * len(p_values)
    ordered = sorted(
        ((index, value) for index, value in enumerate(p_values) if np.isfinite(value)),
        key=lambda item: item[1],
    )
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * value))
        adjusted[index] = running
    return adjusted


def scenario_comparisons(
    data: pd.DataFrame,
    *,
    value_column: str,
    scenario_column: str = "scenario_label",
    context: dict[str, object] | None = None,
) -> pd.DataFrame:
    """Run Kruskal-Wallis plus Holm-corrected pairwise Mann-Whitney tests."""
    context = dict(context or {})
    groups = {
        str(label): group[value_column].dropna().to_numpy(float)
        for label, group in data.groupby(scenario_column, sort=False)
        if not group[value_column].dropna().empty
    }
    rows: list[dict[str, object]] = []
    if len(groups) >= 2:
        try:
            statistic, p_value = kruskal(*groups.values())
        except ValueError:
            statistic, p_value = np.nan, np.nan
        rows.append({
            **context, "test": "Kruskal-Wallis", "contrast": "all scenarios",
            "n": sum(map(len, groups.values())), "statistic": statistic,
            "p_value_raw": p_value, "p_value_adjusted": p_value,
            "stars": p_value_stars(p_value),
        })
    pair_rows, pair_p_values = [], []
    for left, right in combinations(groups, 2):
        statistic, p_value = mannwhitneyu(
            groups[left], groups[right], alternative="two-sided", method="auto"
        )
        pair_rows.append({
            **context, "test": "Mann-Whitney U (Holm)",
            "contrast": f"{left} vs {right}",
            "n": len(groups[left]) + len(groups[right]), "statistic": statistic,
            "p_value_raw": p_value,
        })
        pair_p_values.append(float(p_value))
    for row, adjusted in zip(pair_rows, holm_adjust(pair_p_values)):
        row["p_value_adjusted"] = adjusted
        row["stars"] = p_value_stars(adjusted)
        rows.append(row)
    return pd.DataFrame(rows)
