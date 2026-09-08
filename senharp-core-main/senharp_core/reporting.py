"""Reproducible summary tables for the seven-experiment protocol."""

from pathlib import Path

import numpy as np
import pandas as pd


def build_trajectory_summary(
    period_tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for metric, table in period_tables.items():
        if metric not in table.columns:
            continue
        for (experiment_id, label), group in table.groupby(
            ["experiment_id", "experiment_label"]
        ):
            ordered = group.sort_values("period")
            values = ordered[metric].astype(float)
            periods = ordered["period"].astype(float)
            rows.append({
                "experiment_id": experiment_id,
                "experiment_label": label,
                "metric": metric,
                "initial": values.iloc[0],
                "final": values.iloc[-1],
                "change": values.iloc[-1] - values.iloc[0],
                "mean_over_time": values.mean(),
                "standard_deviation_over_time": values.std(ddof=0),
                "cumulative_sum": values.sum(),
                "area_under_trajectory": np.trapz(values, periods),
            })
    return pd.DataFrame(rows)


def build_needs_election_summary(
    households: pd.DataFrame,
    election_periods: list[int],
) -> pd.DataFrame:
    subset = households[households["period"].isin(election_periods)].copy()
    grouped = subset.groupby(
        ["experiment_id", "experiment_label", "period"]
    )["needs_index"]
    summary = grouped.agg(
        mean="mean",
        median="median",
        p10=lambda x: x.quantile(0.10),
        p90=lambda x: x.quantile(0.90),
        share_below_100=lambda x: (x < 100.0).mean(),
    ).reset_index()
    return summary


def build_policy_summary(
    macro: pd.DataFrame,
) -> pd.DataFrame:
    vote = macro[macro["policy_mode"] == "ENDOGENOUS"].copy()
    return (
        vote.groupby(["experiment_id", "experiment_label"], as_index=False)
        .agg(
            active_period_share=("policy_active", "mean"),
            election_count=("election", "sum"),
            mean_vote_probability=("mean_vote_probability", "mean"),
            final_needs_index=("mean_needs_index", "last"),
            final_real_gdp=("real_gdp", "last"),
        )
    )


def export_standard_tables(
    output_root: str | Path,
    period_tables: dict[str, pd.DataFrame],
    macro: pd.DataFrame,
    households: pd.DataFrame,
    election_periods: list[int],
) -> None:
    output_path = Path(output_root) / "tables"
    output_path.mkdir(parents=True, exist_ok=True)

    trajectories = build_trajectory_summary(period_tables)
    trajectories.to_csv(output_path / "trajectory_summaries.csv", index=False)
    trajectories[
        trajectories["experiment_id"].isin(
            ["E0_baseline", "E1_carbon_tax_fixed", "E3_green_deal_fixed", "E5_post_growth_fixed"]
        )
    ].to_csv(output_path / "fixed_experiment_summaries.csv", index=False)

    build_policy_summary(macro).to_csv(
        output_path / "endogenous_policy_summary.csv", index=False
    )
    build_needs_election_summary(households, election_periods).to_csv(
        output_path / "needs_index_at_elections.csv", index=False
    )

    gdp_columns = [
        "experiment_id", "experiment_label", "period", "real_gdp",
        "real_household_consumption", "real_private_investment",
        "real_government_consumption", "real_public_investment",
    ]
    macro[gdp_columns].to_csv(
        output_path / "gdp_expenditure_decomposition.csv", index=False
    )
