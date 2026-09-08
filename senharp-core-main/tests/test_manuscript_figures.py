import numpy as np
import pandas as pd

from senharp_core.manuscript_statistics import (
    holm_adjust,
    p_value_stars,
    scenario_comparisons,
)
from senharp_core.robustness_graphs import _paired_differences


def test_significance_stars_use_conventional_thresholds():
    assert p_value_stars(0.2) == "ns"
    assert p_value_stars(0.049) == "*"
    assert p_value_stars(0.009) == "**"
    assert p_value_stars(0.0009) == "***"


def test_holm_adjustment_is_monotone_and_not_smaller_than_raw_p_values():
    raw = [0.01, 0.04, 0.20]
    adjusted = holm_adjust(raw)
    assert all(value >= original for value, original in zip(adjusted, raw))
    assert adjusted == sorted(adjusted)


def test_scenario_comparisons_exports_global_and_pairwise_tests():
    data = pd.DataFrame({
        "scenario_label": np.repeat(["Carbon Tax", "Green Deal", "Post-Growth"], 8),
        "outcome": np.r_[np.arange(8), np.arange(8) + 20, np.arange(8) + 40],
    })
    result = scenario_comparisons(data, value_column="outcome")
    assert (result.test == "Kruskal-Wallis").sum() == 1
    assert (result.test == "Mann-Whitney U (Holm)").sum() == 3
    assert set(result.stars) == {"***"}


def test_political_difference_is_seed_and_period_matched():
    rows = []
    for seed in [10, 11]:
        for period in [0, 4]:
            rows.extend([
                {"seed": seed, "period": period,
                 "experiment_id": "E1_carbon_tax_fixed", "value": seed + period},
                {"seed": seed, "period": period,
                 "experiment_id": "E2_carbon_tax_vote", "value": seed + period + 2},
            ])
    differences = _paired_differences(pd.DataFrame(rows), "value")
    carbon = differences[differences.scenario_label == "Carbon Tax"]
    assert len(carbon) == 4
    assert np.allclose(carbon.difference, 2.0)
