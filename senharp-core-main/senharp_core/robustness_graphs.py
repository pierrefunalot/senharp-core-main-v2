"""Publication-style figures for paired multi-seed robustness runs."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .manuscript_statistics import format_p_value, scenario_comparisons


FIXED_EXPERIMENTS = [
    "E0_baseline", "E1_carbon_tax_fixed", "E3_green_deal_fixed", "E5_post_growth_fixed"
]
ENDOGENOUS_EXPERIMENTS = [
    "E2_carbon_tax_vote", "E4_green_deal_vote", "E6_post_growth_vote"
]
COLORS = {
    "E0_baseline": "#4d4d4d",
    "E1_carbon_tax_fixed": "#2878b5",
    "E2_carbon_tax_vote": "#2878b5",
    "E3_green_deal_fixed": "#e68613",
    "E4_green_deal_vote": "#e68613",
    "E5_post_growth_fixed": "#3a923a",
    "E6_post_growth_vote": "#3a923a",
}
LABELS = {
    "E0_baseline": "Baseline",
    "E1_carbon_tax_fixed": "Carbon Tax",
    "E2_carbon_tax_vote": "Carbon Tax",
    "E3_green_deal_fixed": "Green Deal",
    "E4_green_deal_vote": "Green Deal",
    "E5_post_growth_fixed": "Post-Growth",
    "E6_post_growth_vote": "Post-Growth",
}
SCENARIO_PAIRS = {
    "Carbon Tax": ("E1_carbon_tax_fixed", "E2_carbon_tax_vote"),
    "Green Deal": ("E3_green_deal_fixed", "E4_green_deal_vote"),
    "Post-Growth": ("E5_post_growth_fixed", "E6_post_growth_vote"),
}
SCENARIOS = list(SCENARIO_PAIRS)
SCENARIO_COLORS = {
    label: COLORS[experiments[0]]
    for label, experiments in SCENARIO_PAIRS.items()
}
REQUIRED_COLUMNS = {
    "seed", "experiment_id", "period", "real_gdp", "nominal_gdp",
    "debt_to_gdp",
    "mean_needs_index", "industrial_emissions", "atmospheric_temperature",
    "policy_mode", "policy_active", "election", "mean_vote_probability",
    "last_election_support",
    "winner_vote_probability", "loser_vote_probability",
    "mean_economic_disposable_income", "private_employment_rate",
    "unemployment_rate",
    "target_job_rate", "filled_job_rate", "vacancy_rate",
    "layoff_rate", "hire_rate",
    "private_capital_to_gdp", "private_investment_to_gdp",
    "investment_capacity_utilization",
    "unmet_demand_share",
}


def _trajectory(
    data: pd.DataFrame,
    figures: Path,
    variable: str,
    title: str,
    ylabel: str,
    filename: str,
    experiments: list[str],
) -> None:
    """Plot the seed mean and empirical 95% interval for one variable."""
    figure, axis = plt.subplots(figsize=(10, 6))
    for experiment_id in experiments:
        grouped = data[data.experiment_id == experiment_id].groupby("period")[variable]
        mean = grouped.mean()
        low = grouped.quantile(0.025)
        high = grouped.quantile(0.975)
        color = COLORS[experiment_id]
        axis.plot(mean.index, mean.values, label=LABELS[experiment_id], color=color)
        axis.fill_between(mean.index, low.values, high.values, color=color, alpha=0.16)
    axis.set(title=title, xlabel="Period", ylabel=ylabel)
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(figures / filename, dpi=200)
    plt.close(figure)


def _paired_differences(data: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Return seed-and-period matched political minus fixed outcomes."""
    indexed = data.set_index(["seed", "period", "experiment_id"])[variable]
    rows = []
    for scenario, (fixed, political) in SCENARIO_PAIRS.items():
        available = set(data.experiment_id.unique())
        if fixed not in available or political not in available:
            continue
        left = indexed.xs(political, level="experiment_id")
        right = indexed.xs(fixed, level="experiment_id")
        common = left.index.intersection(right.index)
        for (seed, period), difference in (left.loc[common] - right.loc[common]).items():
            rows.append({
                "seed": seed, "period": period, "scenario_label": scenario,
                "difference": difference,
            })
    return pd.DataFrame(rows)


def _scenario_tests(
    data: pd.DataFrame,
    value: str,
    figure: str,
    panel: str,
    periods: list[int] | None = None,
) -> pd.DataFrame:
    rows = []
    subsets = [(None, data)] if periods is None else [
        (period, data[data.period == period]) for period in periods
    ]
    for period, subset in subsets:
        result = scenario_comparisons(
            subset,
            value_column=value,
            context={"figure": figure, "panel": panel, "period": period},
        )
        if not result.empty:
            rows.append(result)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def _annotate_global_tests(
    axis: plt.Axes, statistics: pd.DataFrame, positions: list[float]
) -> None:
    global_tests = statistics[statistics.test == "Kruskal-Wallis"]
    for position, (_, row) in zip(positions, global_tests.iterrows()):
        axis.text(
            position, 1.01, format_p_value(float(row.p_value_adjusted)),
            transform=axis.get_xaxis_transform(), ha="center", va="bottom",
            fontsize=8, clip_on=False,
        )


def _political_counterfactual_figure(
    data: pd.DataFrame,
    figures: Path,
    statistics: list[pd.DataFrame],
    *,
    figure_number: int,
    variable: str,
    title: str,
    ylabel: str,
    filename: str,
) -> None:
    """Plot manuscript trajectory and paired political-effect distribution."""
    figure, (top, bottom) = plt.subplots(
        2, 1, figsize=(11, 9), gridspec_kw={"height_ratios": [2.1, 1.0]}
    )
    for scenario, (fixed, political) in SCENARIO_PAIRS.items():
        color = SCENARIO_COLORS[scenario]
        for experiment, linestyle, suffix in [
            (political, "-", "political"),
            (fixed, "--", "counterfactual fixed"),
        ]:
            grouped = data[data.experiment_id == experiment].groupby("period")[variable]
            mean = grouped.mean()
            top.plot(
                mean.index, mean.values, color=color, linestyle=linestyle,
                label=f"{scenario} — {suffix}",
            )
            if experiment == political:
                top.fill_between(
                    mean.index, grouped.quantile(0.025).values,
                    grouped.quantile(0.975).values, color=color, alpha=0.12,
                )
    top.set(title=title, xlabel="Period", ylabel=ylabel)
    top.grid(axis="y", linestyle=":", alpha=0.5)
    top.legend(frameon=False, ncol=2, fontsize=9)
    # As in the factual manuscript code, scenario significance is evaluated on
    # one time-average observation per simulation, not on pooled period rows.
    experiment_to_scenario = {
        experiment: scenario
        for scenario, pair in SCENARIO_PAIRS.items()
        for experiment in pair
    }
    for row_index, (variant, experiments) in enumerate([
        ("Counterfactual fixed", [pair[0] for pair in SCENARIO_PAIRS.values()]),
        ("Political", [pair[1] for pair in SCENARIO_PAIRS.values()]),
    ]):
        seed_means = (
            data[data.experiment_id.isin(experiments)]
            .groupby(["seed", "experiment_id"], as_index=False)[variable].mean()
        )
        seed_means["scenario_label"] = seed_means.experiment_id.map(
            experiment_to_scenario
        )
        variant_result = scenario_comparisons(
            seed_means, value_column=variable,
            context={
                "figure": f"Figure {figure_number}",
                "panel": f"trajectory-{variant}", "period": None,
            },
        )
        statistics.append(variant_result)
        global_test = variant_result[variant_result.test == "Kruskal-Wallis"]
        if not global_test.empty:
            top.text(
                0.02, 0.98 - row_index * 0.065,
                f"{variant}: "
                f"{format_p_value(float(global_test.iloc[0].p_value_adjusted))}",
                transform=top.transAxes, va="top", fontsize=9,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.72},
            )

    differences = _paired_differences(data, variable)
    periods = sorted(data.loc[data.election == 1, "period"].unique().astype(int))
    positions, values, colors = [], [], []
    offsets = np.linspace(-0.25, 0.25, len(SCENARIOS))
    for period_index, period in enumerate(periods):
        for offset, scenario in zip(offsets, SCENARIOS):
            values.append(
                differences[
                    (differences.period == period)
                    & (differences.scenario_label == scenario)
                ].difference.dropna()
            )
            positions.append(period_index + offset)
            colors.append(SCENARIO_COLORS[scenario])
    boxes = bottom.boxplot(
        values, positions=positions, widths=0.22, patch_artist=True,
        showfliers=False, whis=(2.5, 97.5), manage_ticks=False,
    )
    for box, color in zip(boxes["boxes"], colors):
        box.set(facecolor=color, edgecolor=color, alpha=0.55)
    bottom.axhline(0.0, color="black", linewidth=0.8)
    bottom.set(xlabel="Election period", ylabel="Political − fixed")
    bottom.set_xticks(range(len(periods)), [str(period + 1) for period in periods])
    bottom.grid(axis="y", linestyle=":", alpha=0.5)
    result = _scenario_tests(
        differences, "difference", f"Figure {figure_number}",
        "political-minus-fixed", periods,
    )
    statistics.append(result)
    _annotate_global_tests(bottom, result, list(range(len(periods))))
    figure.tight_layout()
    figure.savefig(figures / filename, dpi=200, bbox_inches="tight")
    plt.close(figure)


def _political_data(data: pd.DataFrame) -> pd.DataFrame:
    elections = data[
        (data.policy_mode == "ENDOGENOUS") & (data.election == 1)
    ].copy()
    elections["scenario_label"] = elections.experiment_id.map(LABELS)
    return elections


def _vote_distribution(
    data: pd.DataFrame, figures: Path, statistics: list[pd.DataFrame]
) -> None:
    elections = _political_data(data)
    periods = sorted(elections.period.unique().astype(int))
    positions, values, colors = [], [], []
    offsets = np.linspace(-0.25, 0.25, len(SCENARIOS))
    for period_index, period in enumerate(periods):
        for offset, scenario in zip(offsets, SCENARIOS):
            values.append(
                elections[
                    (elections.period == period)
                    & (elections.scenario_label == scenario)
                ].last_election_support.dropna()
            )
            positions.append(period_index + offset)
            colors.append(SCENARIO_COLORS[scenario])
    figure, axis = plt.subplots(figsize=(12, 7))
    boxes = axis.boxplot(
        values, positions=positions, widths=0.22, patch_artist=True,
        showfliers=False, whis=(2.5, 97.5), manage_ticks=False,
    )
    for box, color in zip(boxes["boxes"], colors):
        box.set(facecolor=color, edgecolor=color, alpha=0.58)
    axis.axhline(0.5, color="black", linestyle="--", linewidth=0.9)
    axis.set(
        title="Figure 7 — Distribution of pro-transition vote shares",
        xlabel="Election period", ylabel="Mean vote probability", ylim=(0, 1.08),
    )
    axis.set_xticks(range(len(periods)), [str(period + 1) for period in periods])
    handles = [
        plt.Line2D([0], [0], color=SCENARIO_COLORS[item], linewidth=8, alpha=0.58)
        for item in SCENARIOS
    ]
    axis.legend(handles, SCENARIOS, frameon=False, ncol=3)
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    result = _scenario_tests(
        elections, "last_election_support", "Figure 7", "vote-share", periods
    )
    statistics.append(result)
    _annotate_global_tests(axis, result, list(range(len(periods))))
    figure.tight_layout()
    figure.savefig(figures / "manuscript_figure_07_vote_shares.png", dpi=200)
    plt.close(figure)


def _reelection_figure(
    data: pd.DataFrame, figures: Path, statistics: list[pd.DataFrame]
) -> None:
    elections = _political_data(data)
    periods = sorted(elections.period.unique().astype(int))
    summary = elections.groupby(["scenario_label", "period"]).policy_active.agg(
        ["mean", "std"]
    )
    figure, axis = plt.subplots(figsize=(10, 6))
    for scenario in SCENARIOS:
        values = summary.loc[scenario].reindex(periods)
        axis.errorbar(
            np.arange(len(periods)), values["mean"],
            yerr=values["std"].fillna(0.0), marker="o", capsize=3,
            label=scenario, color=SCENARIO_COLORS[scenario],
        )
    axis.set(
        title="Figure 8 — Reelection probability of pro-transition governments",
        xlabel="Election period", ylabel="Frequency (mean ± 1 SD)",
        ylim=(-0.05, 1.12),
    )
    axis.set_xticks(range(len(periods)), [str(period + 1) for period in periods])
    axis.legend(frameon=False)
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    result = _scenario_tests(
        elections, "policy_active", "Figure 8", "reelection", periods
    )
    statistics.append(result)
    _annotate_global_tests(axis, result, list(range(len(periods))))
    figure.tight_layout()
    figure.savefig(figures / "manuscript_figure_08_reelection.png", dpi=200)
    plt.close(figure)


def _subgroup_figure(
    data: pd.DataFrame, figures: Path, statistics: list[pd.DataFrame]
) -> None:
    elections = _political_data(data)
    final = elections[elections.period == elections.period.max()].copy()
    melted = final.melt(
        id_vars=["seed", "scenario_label"],
        value_vars=["winner_vote_probability", "loser_vote_probability"],
        var_name="subgroup", value_name="vote_probability",
    )
    subgroup_labels = {
        "winner_vote_probability": "Needs winners",
        "loser_vote_probability": "Needs losers",
    }
    figure, axis = plt.subplots(figsize=(10, 6))
    x = np.arange(len(SCENARIOS))
    width = 0.36
    for row_index, (offset, subgroup) in enumerate([
        (-width / 2, "winner_vote_probability"),
        (width / 2, "loser_vote_probability"),
    ]):
        group = melted[melted.subgroup == subgroup]
        summary = group.groupby("scenario_label").vote_probability.agg(
            ["mean", "std"]
        ).reindex(SCENARIOS)
        axis.bar(
            x + offset, summary["mean"], width, yerr=summary["std"], capsize=3,
            label=subgroup_labels[subgroup], alpha=0.78,
        )
        result = scenario_comparisons(
            group, value_column="vote_probability",
            context={
                "figure": "Figure 9", "panel": subgroup_labels[subgroup],
                "period": int(final.period.max()),
            },
        )
        statistics.append(result)
        global_test = result[result.test == "Kruskal-Wallis"]
        if not global_test.empty:
            axis.text(
                0.02, 0.98 - row_index * 0.07,
                f"{subgroup_labels[subgroup]}: "
                f"{format_p_value(float(global_test.iloc[0].p_value_adjusted))}",
                transform=axis.transAxes, va="top", fontsize=9,
            )
    axis.set(
        title="Figure 9 — Political support by material-outcome subgroup",
        ylabel="Mean vote probability", xticks=x, xticklabels=SCENARIOS,
        ylim=(0, 1.08),
    )
    axis.legend(frameon=False)
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    figure.tight_layout()
    figure.savefig(figures / "manuscript_figure_09_support_subgroups.png", dpi=200)
    plt.close(figure)


def _cumulative_emissions_figure(
    data: pd.DataFrame, figures: Path, statistics: list[pd.DataFrame]
) -> None:
    cumulative = data.groupby(
        ["seed", "experiment_id"], as_index=False
    ).industrial_emissions.sum()
    cumulative["scenario_label"] = cumulative.experiment_id.map(LABELS)
    cumulative["variant"] = np.where(
        cumulative.experiment_id.isin(ENDOGENOUS_EXPERIMENTS),
        "Political", "Counterfactual fixed",
    )
    cumulative = cumulative[cumulative.scenario_label.isin(SCENARIOS)]
    figure, axis = plt.subplots(figsize=(10, 6))
    positions, values, colors = [], [], []
    for index, scenario in enumerate(SCENARIOS):
        for offset, variant, alpha in [
            (-0.17, "Counterfactual fixed", 0.38), (0.17, "Political", 0.78)
        ]:
            values.append(
                cumulative[
                    (cumulative.scenario_label == scenario)
                    & (cumulative.variant == variant)
                ].industrial_emissions
            )
            positions.append(index + offset)
            colors.append((SCENARIO_COLORS[scenario], alpha))
    boxes = axis.boxplot(
        values, positions=positions, widths=0.28, patch_artist=True,
        showfliers=False, whis=(2.5, 97.5), manage_ticks=False,
    )
    for box, (color, alpha) in zip(boxes["boxes"], colors):
        box.set(facecolor=color, edgecolor=color, alpha=alpha)
    axis.set(
        title="Figure 10 — Cumulative CO₂ emissions across simulations",
        ylabel="Cumulative industrial CO₂ emissions",
        xticks=range(3), xticklabels=SCENARIOS,
    )
    axis.legend(
        handles=[
            plt.Line2D([0], [0], color="black", linewidth=8, alpha=0.38,
                       label="Counterfactual fixed"),
            plt.Line2D([0], [0], color="black", linewidth=8, alpha=0.78,
                       label="Political"),
        ],
        frameon=False,
    )
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    for row_index, variant in enumerate(["Counterfactual fixed", "Political"]):
        result = scenario_comparisons(
            cumulative[cumulative.variant == variant],
            value_column="industrial_emissions",
            context={"figure": "Figure 10", "panel": variant, "period": None},
        )
        statistics.append(result)
        global_test = result[result.test == "Kruskal-Wallis"]
        if not global_test.empty:
            axis.text(
                0.02, 0.98 - row_index * 0.07,
                f"{variant}: "
                f"{format_p_value(float(global_test.iloc[0].p_value_adjusted))}",
                transform=axis.transAxes, va="top", fontsize=9,
            )
    figure.tight_layout()
    figure.savefig(
        figures / "manuscript_figure_10_cumulative_emissions.png", dpi=200
    )
    plt.close(figure)


def export_manuscript_figures(
    trajectories: pd.DataFrame,
    output_dir: str | Path,
    needs_snapshots: pd.DataFrame | None = None,
) -> None:
    """Export manuscript outcomes and trajectory-diagnostic figures."""
    missing = sorted(REQUIRED_COLUMNS - set(trajectories.columns))
    if missing:
        raise ValueError(
            "Missing robustness columns: " + ", ".join(missing)
            + ". Rerun scripts/run_robustness.py with the current code."
        )

    figures = Path(output_dir) / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    seeds = trajectories["seed"].nunique()
    statistical_results: list[pd.DataFrame] = []

    # Figures 4–11 reproduce the empirical result figures of the manuscript.
    # Solid lines are endogenous-political runs; dashed lines are uninterrupted
    # fixed-policy counterfactuals using the same seeds.
    _political_counterfactual_figure(
        trajectories, figures, statistical_results,
        figure_number=4, variable="real_gdp",
        title="Figure 4 — Real GDP: political vs counterfactual models",
        ylabel="Real GDP", filename="manuscript_figure_04_real_gdp.png",
    )
    _political_counterfactual_figure(
        trajectories, figures, statistical_results,
        figure_number=5, variable="debt_to_gdp",
        title="Figure 5 — Public debt-to-GDP: political vs counterfactual models",
        ylabel="Public debt / real GDP",
        filename="manuscript_figure_05_debt_to_gdp.png",
    )
    _political_counterfactual_figure(
        trajectories, figures, statistical_results,
        figure_number=6, variable="mean_needs_index",
        title="Figure 6 — Needs Index: political vs counterfactual models",
        ylabel="Mean Needs Index",
        filename="manuscript_figure_06_needs_index.png",
    )
    _vote_distribution(trajectories, figures, statistical_results)
    _reelection_figure(trajectories, figures, statistical_results)
    _subgroup_figure(trajectories, figures, statistical_results)
    _cumulative_emissions_figure(trajectories, figures, statistical_results)
    _political_counterfactual_figure(
        trajectories, figures, statistical_results,
        figure_number=11, variable="atmospheric_temperature",
        title="Figure 11 — Atmospheric temperature: political vs counterfactual models",
        ylabel="Temperature anomaly",
        filename="manuscript_figure_11_temperature.png",
    )
    valid_results = [result for result in statistical_results if not result.empty]
    if valid_results:
        pd.concat(valid_results, ignore_index=True).to_csv(
            Path(output_dir) / "manuscript_figure_statistical_tests.csv",
            index=False,
        )

    specs = [
        ("real_gdp", "Real GDP", "Real GDP", "01_real_gdp.png"),
        (
            "nominal_gdp",
            "Factual GDP (C + I + G at current prices)",
            "Current-price C + I + G",
            "01b_factual_gdp_c_i_g.png",
        ),
        ("debt_to_gdp", "Public debt-to-GDP ratio", "Debt / real GDP", "02_debt_to_gdp.png"),
        ("mean_needs_index", "Mean Needs Index", "Needs Index", "03_needs_index.png"),
        (
            "mean_economic_disposable_income",
            "Mean disposable income",
            "Disposable income",
            "09_disposable_income.png",
        ),
        (
            "private_employment_rate",
            "Private employment rate",
            "Share of households",
            "10_private_employment_rate.png",
        ),
        (
            "target_job_rate",
            "Private jobs targeted by firms",
            "Target jobs / households",
            "10b_target_job_rate.png",
        ),
        (
            "vacancy_rate",
            "Unfilled share of firms' job targets",
            "Vacancies / target jobs",
            "10c_vacancy_rate.png",
        ),
        (
            "private_capital_to_gdp",
            "Private capital-to-GDP ratio",
            "Private capital / real GDP",
            "11_private_capital_to_gdp.png",
        ),
        (
            "private_investment_to_gdp",
            "Private investment-to-GDP ratio",
            "Private investment / real GDP",
            "12_private_investment_to_gdp.png",
        ),
        (
            "investment_capacity_utilization",
            "Lagged capacity utilization used by investment",
            "Realised output / potential output",
            "13_investment_capacity_utilization.png",
        ),
        (
            "unmet_demand_share",
            "Share of market demand not satisfied",
            "Unmet demand / total demand",
            "14_unmet_demand_share.png",
        ),
        ("atmospheric_temperature", "Atmospheric temperature", "Temperature anomaly", "08_temperature.png"),
    ]
    for variable, title, ylabel, filename in specs:
        _trajectory(
            trajectories, figures, variable, f"{title} — {seeds} paired seeds",
            ylabel, filename, FIXED_EXPERIMENTS,
        )

    cumulative = trajectories.sort_values(["seed", "experiment_id", "period"]).copy()
    cumulative["cumulative_industrial_emissions"] = cumulative.groupby(
        ["seed", "experiment_id"]
    )["industrial_emissions"].cumsum()
    _trajectory(
        cumulative, figures, "cumulative_industrial_emissions",
        f"Cumulative CO2 emissions — {seeds} paired seeds",
        "Cumulative CO2 emissions", "07_cumulative_emissions.png", FIXED_EXPERIMENTS,
    )

    elections = trajectories[
        (trajectories.policy_mode == "ENDOGENOUS") & (trajectories.election == 1)
    ].copy()
    _trajectory(
        elections, figures, "mean_vote_probability",
        f"Pro-transition vote probability — {seeds} paired seeds",
        "Mean vote probability", "04_vote_support.png", ENDOGENOUS_EXPERIMENTS,
    )

    reelection = elections.groupby(["experiment_id", "period"], as_index=False).agg(
        mean=("policy_active", "mean"), sd=("policy_active", "std")
    )
    figure, axis = plt.subplots(figsize=(10, 6))
    for experiment_id in ENDOGENOUS_EXPERIMENTS:
        values = reelection[reelection.experiment_id == experiment_id]
        axis.errorbar(
            values.period, values["mean"], yerr=values.sd.fillna(0.0), marker="o",
            capsize=3, label=LABELS[experiment_id], color=COLORS[experiment_id],
        )
    axis.set(
        title=f"Pro-transition reelection frequency — {seeds} paired seeds",
        xlabel="Election period", ylabel="Frequency (mean ± 1 SD)", ylim=(-0.05, 1.05),
    )
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(figures / "05_reelection_probability.png", dpi=200)
    plt.close(figure)

    final = elections[elections.period == elections.period.max()]
    subgroup = final.melt(
        id_vars=["experiment_id", "seed"],
        value_vars=["winner_vote_probability", "loser_vote_probability"],
        var_name="subgroup", value_name="vote_probability",
    ).groupby(["experiment_id", "subgroup"], as_index=False).agg(
        mean=("vote_probability", "mean"), sd=("vote_probability", "std")
    )
    x = np.arange(len(ENDOGENOUS_EXPERIMENTS))
    width = 0.36
    figure, axis = plt.subplots(figsize=(10, 6))
    for offset, column, label in [
        (-width / 2, "winner_vote_probability", "Needs winners"),
        (width / 2, "loser_vote_probability", "Needs losers"),
    ]:
        values = subgroup[subgroup.subgroup == column].set_index("experiment_id").reindex(
            ENDOGENOUS_EXPERIMENTS
        )
        axis.bar(x + offset, values["mean"], width, yerr=values.sd, capsize=3, label=label)
    axis.set(
        title=f"Political support by needs subgroup at final election — {seeds} paired seeds",
        ylabel="Mean vote probability", xticks=x,
        xticklabels=[LABELS[item] for item in ENDOGENOUS_EXPERIMENTS], ylim=(0.0, 1.0),
    )
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(figures / "06_vote_support_by_needs_group.png", dpi=200)
    plt.close(figure)

    if needs_snapshots is not None:
        export_needs_boxplots(needs_snapshots, figures, seeds)


def export_needs_boxplots(
    needs: pd.DataFrame, figures: Path, seeds: int | None = None
) -> None:
    """Plot household Needs Index distributions every five periods."""
    required = {"experiment_id", "period", "needs_index"}
    missing = sorted(required - set(needs.columns))
    if missing:
        raise ValueError("Missing Needs snapshot columns: " + ", ".join(missing))
    data = needs[needs.experiment_id.isin(FIXED_EXPERIMENTS)].copy()
    periods = sorted(data.period.unique())
    scenarios = FIXED_EXPERIMENTS
    positions = []
    values = []
    colors = []
    width = 0.16
    offsets = np.linspace(-0.27, 0.27, len(scenarios))
    for period_index, period in enumerate(periods):
        for offset, experiment_id in zip(offsets, scenarios):
            sample = data[
                (data.period == period) & (data.experiment_id == experiment_id)
            ].needs_index.dropna().to_numpy()
            values.append(sample)
            positions.append(period_index + offset)
            colors.append(COLORS[experiment_id])
    figure, axis = plt.subplots(figsize=(13, 7))
    boxes = axis.boxplot(
        values, positions=positions, widths=width, patch_artist=True,
        showfliers=False, whis=(2.5, 97.5), manage_ticks=False,
    )
    for box, color in zip(boxes["boxes"], colors):
        box.set(facecolor=color, alpha=0.55, edgecolor=color)
    for median in boxes["medians"]:
        median.set(color="black", linewidth=1.1)
    handles = [
        plt.Line2D([0], [0], color=COLORS[item], linewidth=8, alpha=0.55)
        for item in scenarios
    ]
    title_seed = f" — {seeds} paired seeds" if seeds is not None else ""
    axis.set(
        title=f"Household Needs Index distributions every five periods{title_seed}",
        xlabel="Period", ylabel="Needs Index", xticks=np.arange(len(periods)),
        xticklabels=[str(period) for period in periods],
    )
    axis.grid(axis="y", linestyle=":", alpha=0.5)
    axis.legend(handles, [LABELS[item] for item in scenarios], frameon=False, ncol=4)
    figure.tight_layout()
    figure.savefig(figures / "03b_needs_index_boxplots.png", dpi=200)
    plt.close(figure)
