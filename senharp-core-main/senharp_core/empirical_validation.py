"""Operational tests of the four realism hypotheses stated in the manuscript."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def evaluate_realism_hypotheses(
    trajectories: pd.DataFrame,
    needs_snapshots: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return seed-level diagnostics and hypothesis pass frequencies.

    These are internal generative-validity checks, not estimates of external
    causal effects. A hypothesis is labelled robust at an 80% seed frequency.
    """
    rows: list[dict] = []
    final_period = trajectories.period.max()

    # H1: price/technology packages mitigate, but do not reach a stylised
    # 55% reduction within the horizon (the manuscript's insufficiency claim).
    cumulative = trajectories.groupby(["seed", "experiment_id"]).industrial_emissions.sum()
    for seed in sorted(trajectories.seed.unique()):
        baseline = float(cumulative.loc[(seed, "E0_baseline")])
        reductions = []
        for experiment_id in ["E1_carbon_tax_fixed", "E3_green_deal_fixed"]:
            reductions.append(1.0 - float(cumulative.loc[(seed, experiment_id)]) / baseline)
        rows.append({
            "seed": seed,
            "hypothesis": "H1_mitigation_but_insufficient",
            "statistic": min(reductions),
            "passes": int(all(0.0 < value < 0.55 for value in reductions)),
        })

    # H2: higher constrained-expenditure burden is associated with lower
    # pro-transition support at elections, evaluated within each seed.
    political = trajectories[
        (trajectories.policy_mode == "ENDOGENOUS") & (trajectories.election == 1)
    ]
    for seed, group in political.groupby("seed"):
        x = group.mean_constrained_expenditure_burden.to_numpy(float)
        y = group.mean_vote_probability.to_numpy(float)
        correlation = float(np.corrcoef(x, y)[0, 1]) if np.std(x) > 0 and np.std(y) > 0 else np.nan
        rows.append({
            "seed": seed,
            "hypothesis": "H2_cost_burden_backlash",
            "statistic": correlation,
            "passes": int(np.isfinite(correlation) and correlation < 0.0),
        })

    # H3: identical policies generate territorially different social outcomes.
    final_needs = needs_snapshots[needs_snapshots.period == final_period]
    for seed, group in final_needs.groupby("seed"):
        territorial = group.groupby("territory_id").needs_index.mean()
        gap = float(territorial.get(1, np.nan) - territorial.get(0, np.nan))
        rows.append({
            "seed": seed,
            "hypothesis": "H3_territorial_divergence",
            "statistic": gap,
            "passes": int(np.isfinite(gap) and abs(gap) > 0.01),
        })

    # H4: the integrated Green Deal is more socially and politically durable
    # than isolated carbon pricing in endogenous-policy experiments.
    for seed in sorted(trajectories.seed.unique()):
        seed_data = trajectories[trajectories.seed == seed]
        carbon = seed_data[seed_data.experiment_id == "E2_carbon_tax_vote"]
        green = seed_data[seed_data.experiment_id == "E4_green_deal_vote"]
        durability_gap = float(green.policy_active.mean() - carbon.policy_active.mean())
        needs_gap = float(green.mean_needs_index.mean() - carbon.mean_needs_index.mean())
        rows.append({
            "seed": seed,
            "hypothesis": "H4_integrated_policy_durability",
            "statistic": durability_gap,
            "secondary_statistic": needs_gap,
            "passes": int(durability_gap >= 0.0 and needs_gap > 0.0),
        })

    details = pd.DataFrame(rows)
    summary = details.groupby("hypothesis", as_index=False).agg(
        seeds=("seed", "nunique"),
        pass_frequency=("passes", "mean"),
        mean_statistic=("statistic", "mean"),
        median_statistic=("statistic", "median"),
    )
    summary["passes_80_percent_rule"] = (summary.pass_frequency >= 0.80).astype(int)
    return details, summary


def export_realism_validation(
    trajectories: pd.DataFrame,
    needs_snapshots: pd.DataFrame,
    output_dir: str | Path,
) -> None:
    details, summary = evaluate_realism_hypotheses(trajectories, needs_snapshots)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    details.to_csv(output / "realism_hypothesis_seed_results.csv", index=False)
    summary.to_csv(output / "realism_hypothesis_summary.csv", index=False)

