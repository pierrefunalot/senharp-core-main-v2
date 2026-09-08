"""Create robustness and sensitivity diagnostics from protocol outputs."""

from pathlib import Path
import argparse
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from senharp_core.robustness_graphs import export_manuscript_figures


def analyze_robustness(root: Path) -> None:
    trajectories = pd.read_csv(root / "trajectories.csv")
    needs_path = root / "needs_index_snapshots.csv"
    needs = pd.read_csv(needs_path) if needs_path.exists() else None
    export_manuscript_figures(trajectories, root, needs)
    figures = root / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    fixed = ["E0_baseline", "E1_carbon_tax_fixed", "E3_green_deal_fixed", "E5_post_growth_fixed"]
    colors = {
        "E0_baseline": "#4d4d4d",
        "E1_carbon_tax_fixed": "#2878b5",
        "E3_green_deal_fixed": "#e68613",
        "E5_post_growth_fixed": "#3a923a",
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    for experiment_id in fixed:
        data = trajectories[trajectories.experiment_id == experiment_id]
        grouped = data.groupby("period")["real_gdp"]
        mean = grouped.mean()
        low = grouped.quantile(0.025)
        high = grouped.quantile(0.975)
        ax.plot(mean.index, mean.values, label=experiment_id, color=colors[experiment_id])
        ax.fill_between(mean.index, low.values, high.values, color=colors[experiment_id], alpha=0.16)
    ax.set(title="Real GDP — 30 paired seeds", xlabel="Period", ylabel="Real GDP")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures / "real_gdp_30_seeds.png", dpi=200)
    plt.close(fig)

    vote = trajectories[trajectories.policy_mode == "ENDOGENOUS"]
    activation = vote.groupby(["experiment_id", "period"], as_index=False).policy_active.mean()
    activation.to_csv(root / "policy_activation_by_period.csv", index=False)


def analyze_oat(root: Path) -> None:
    results = pd.read_csv(root / "oat_results.csv")
    rows = []
    metrics = [
        "real_gdp", "mean_needs_index", "income_gini", "needs_index_gini",
        "cumulative_industrial_emissions", "cumulative_material_use", "public_debt",
    ]
    for (parameter, experiment), group in results.groupby(["sensitivity_parameter", "experiment_id"]):
        base = group[group.multiplier == 1.0].iloc[0]
        for _, row in group.iterrows():
            for metric in metrics:
                denominator = abs(float(base[metric])) or 1.0
                rows.append({
                    "sensitivity_parameter": parameter,
                    "experiment_id": experiment,
                    "multiplier": row.multiplier,
                    "metric": metric,
                    "relative_change_from_central": (float(row[metric]) - float(base[metric])) / denominator,
                })
    effects = pd.DataFrame(rows)
    effects.to_csv(root / "oat_relative_effects.csv", index=False)

    needs = effects[effects.metric == "mean_needs_index"]
    spans = needs.groupby(["sensitivity_parameter", "experiment_id"]).relative_change_from_central.agg(
        minimum="min", maximum="max"
    ).reset_index()
    spans["range"] = spans.maximum - spans.minimum
    spans.to_csv(root / "oat_needs_tornado_data.csv", index=False)

    fixed = "E5_post_growth_fixed"
    plot = spans[spans.experiment_id == fixed].sort_values("range")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(plot.sensitivity_parameter, plot.range, color="#3a923a")
    ax.set(title="OAT range — final NeedsIndex, Post-Growth", xlabel="Relative response range")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(root / "oat_needs_tornado.png", dpi=200)
    plt.close(fig)


def analyze_lhs(root: Path) -> None:
    design = pd.read_csv(root / "latin_hypercube_design.csv")
    results = pd.read_csv(root / "latin_hypercube_results.csv")
    merged = results.merge(design, on="design_id", how="left")
    calibration_count = merged["design_id"].nunique()
    fixed = merged.pivot(index="design_id", columns="experiment_id")
    rows = []
    contrasts = {
        "E1_minus_E0": ("E1_carbon_tax_fixed", "E0_baseline"),
        "E3_minus_E0": ("E3_green_deal_fixed", "E0_baseline"),
        "E5_minus_E0": ("E5_post_growth_fixed", "E0_baseline"),
    }
    for contrast, (left, right) in contrasts.items():
        for metric in [
            "real_gdp", "mean_needs_index", "income_gini", "needs_index_gini",
            "cumulative_industrial_emissions", "cumulative_material_use", "public_debt",
        ]:
            values = fixed[metric][left] - fixed[metric][right]
            positive = (values > 0.0).mean()
            negative = (values < 0.0).mean()
            rows.append({
                "contrast": contrast,
                "metric": metric,
                "calibrations_run": len(values),
                "mean_difference": values.mean(),
                "positive_sign_frequency": positive,
                "negative_sign_frequency": negative,
                "sign_stability": max(positive, negative),
                "passes_80_percent_rule": int(max(positive, negative) >= 0.80),
            })
    pd.DataFrame(rows).to_csv(root / "lhs_preliminary_robustness.csv", index=False)

    figure_dir = root / "figures_lhs_300"
    figure_dir.mkdir(parents=True, exist_ok=True)
    labels = {
        "E0_baseline": "Baseline",
        "E1_carbon_tax_fixed": "Carbon Tax",
        "E3_green_deal_fixed": "Green Deal",
        "E5_post_growth_fixed": "Post-Growth",
    }
    colors = ["#777777", "#2878b5", "#e68613", "#3a923a"]
    metrics = [
        ("real_gdp", "Final real GDP"),
        ("mean_needs_index", "Final mean Needs Index"),
        ("income_gini", "Final disposable-income Gini"),
        ("needs_index_gini", "Final Needs Index Gini"),
        ("cumulative_industrial_emissions", "Cumulative industrial CO2 emissions"),
        ("cumulative_material_use", "Cumulative material use"),
        ("public_debt", "Final public debt"),
    ]
    order = list(labels)
    for number, (metric, title) in enumerate(metrics, start=1):
        values = [
            merged[merged.experiment_id == experiment][metric].dropna().to_numpy()
            for experiment in order
        ]
        fig, ax = plt.subplots(figsize=(9, 6))
        boxes = ax.boxplot(values, patch_artist=True, showfliers=False, whis=(2.5, 97.5))
        for box, color in zip(boxes["boxes"], colors):
            box.set(facecolor=color, alpha=0.55, edgecolor=color)
        ax.set(
            title=f"{title} — {calibration_count} Latin Hypercube calibrations",
            ylabel=title,
            xticks=np.arange(1, len(order) + 1),
            xticklabels=[labels[item] for item in order],
        )
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        fig.tight_layout()
        fig.savefig(figure_dir / f"{number:02d}_{metric}.png", dpi=200)
        plt.close(fig)

    trajectories_path = root / "latin_hypercube_trajectories.csv"
    if trajectories_path.exists():
        export_lhs_trajectory_figures(
            pd.read_csv(trajectories_path),
            figure_dir,
        )
    else:
        print(
            "No latin_hypercube_trajectories.csv found: rerun lhs-run "
            "with the current code to create mean trajectory figures."
        )


def export_lhs_trajectory_figures(
    trajectories: pd.DataFrame,
    figure_dir: Path,
) -> None:
    """Export mean trajectories across LHS calibrations with 95% bands."""

    experiments = [
        "E0_baseline",
        "E1_carbon_tax_fixed",
        "E3_green_deal_fixed",
        "E5_post_growth_fixed",
    ]
    labels = {
        "E0_baseline": "Baseline",
        "E1_carbon_tax_fixed": "Carbon Tax",
        "E3_green_deal_fixed": "Green Deal",
        "E5_post_growth_fixed": "Post-Growth",
    }
    colors = {
        "E0_baseline": "#4d4d4d",
        "E1_carbon_tax_fixed": "#2878b5",
        "E3_green_deal_fixed": "#e68613",
        "E5_post_growth_fixed": "#3a923a",
    }
    required = {
        "design_id", "experiment_id", "period", "mean_needs_index",
        "real_gdp", "mean_vote_probability", "atmospheric_temperature",
        "unemployment_rate", "real_household_consumption",
        "target_job_rate", "filled_job_rate", "vacancy_rate",
        "layoff_rate", "hire_rate",
        "real_private_investment", "real_public_investment",
        "real_government_consumption",
    }
    missing = sorted(required - set(trajectories.columns))
    if missing:
        raise ValueError(
            "Missing LHS trajectory columns: " + ", ".join(missing)
        )

    data = trajectories[trajectories.experiment_id.isin(experiments)].copy()
    data["real_consumption_C"] = data["real_household_consumption"]
    data["real_investment_I"] = (
        data["real_private_investment"] + data["real_public_investment"]
    )
    data["real_government_G"] = data["real_government_consumption"]
    for component in ["C", "I", "G"]:
        data[f"{component}_share_gdp"] = np.where(
            data["real_gdp"].abs() > 1e-12,
            data[f"real_{'consumption' if component == 'C' else 'investment' if component == 'I' else 'government'}_{component}"]
            / data["real_gdp"],
            np.nan,
        )

    summary_columns = [
        "mean_needs_index", "real_gdp", "mean_vote_probability",
        "atmospheric_temperature", "unemployment_rate",
        "target_job_rate", "filled_job_rate", "vacancy_rate",
        "layoff_rate", "hire_rate",
        "real_consumption_C", "real_investment_I", "real_government_G",
        "C_share_gdp", "I_share_gdp", "G_share_gdp",
    ]
    summary = (
        data.groupby(["experiment_id", "period"])[summary_columns]
        .agg(["mean", lambda values: values.quantile(0.025), lambda values: values.quantile(0.975)])
    )
    summary.columns = [
        f"{variable}_{stat if stat == 'mean' else 'p025' if stat == '<lambda_0>' else 'p975'}"
        for variable, stat in summary.columns
    ]
    summary.reset_index().to_csv(
        figure_dir.parent / "latin_hypercube_trajectory_summary.csv",
        index=False,
    )

    specs = [
        ("mean_needs_index", "Mean Needs Index", "Needs Index", "08_mean_needs_trajectory.png"),
        ("real_gdp", "Mean real GDP", "Real GDP", "09_mean_real_gdp_trajectory.png"),
        ("mean_vote_probability", "Mean political support", "Vote probability", "10_mean_political_support_trajectory.png"),
        ("atmospheric_temperature", "Mean atmospheric temperature", "Temperature anomaly", "11_mean_temperature_trajectory.png"),
        ("unemployment_rate", "Mean unemployment rate", "Share of households", "12_mean_unemployment_trajectory.png"),
        ("target_job_rate", "Mean private job target", "Target jobs / households", "12b_mean_target_job_rate.png"),
        ("vacancy_rate", "Mean vacancy rate", "Vacancies / target jobs", "12c_mean_vacancy_rate.png"),
        ("layoff_rate", "Mean layoff rate", "Layoffs / households", "12d_mean_layoff_rate.png"),
        ("hire_rate", "Mean hiring rate", "Hires / households", "12e_mean_hire_rate.png"),
    ]
    calibration_count = data["design_id"].nunique()
    for variable, title, ylabel, filename in specs:
        fig, ax = plt.subplots(figsize=(10, 6))
        for experiment in experiments:
            grouped = data[data.experiment_id == experiment].groupby("period")[variable]
            mean = grouped.mean()
            low = grouped.quantile(0.025)
            high = grouped.quantile(0.975)
            ax.plot(mean.index, mean.values, label=labels[experiment], color=colors[experiment])
            ax.fill_between(mean.index, low.values, high.values, color=colors[experiment], alpha=0.16)
        ax.set(title=f"{title} — {calibration_count} LHS calibrations", xlabel="Period", ylabel=ylabel)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.legend(frameon=False)
        fig.tight_layout()
        fig.savefig(figure_dir / filename, dpi=200)
        plt.close(fig)

    for suffix, variables, title, ylabel in [
        ("levels", ["real_consumption_C", "real_investment_I", "real_government_G"], "Mean contributions to real GDP", "Real expenditure"),
        ("shares", ["C_share_gdp", "I_share_gdp", "G_share_gdp"], "Mean shares of real GDP", "Share of real GDP"),
    ]:
        for experiment in experiments:
            fig, ax = plt.subplots(figsize=(10, 6))
            for variable, component, color in zip(variables, ["C", "I", "G"], ["#2878b5", "#e68613", "#3a923a"]):
                grouped = data[data.experiment_id == experiment].groupby("period")[variable]
                mean = grouped.mean()
                low = grouped.quantile(0.025)
                high = grouped.quantile(0.975)
                ax.plot(mean.index, mean.values, label=component, color=color)
                ax.fill_between(mean.index, low.values, high.values, color=color, alpha=0.14)
            ax.set(title=f"{title} — {labels[experiment]}", xlabel="Period", ylabel=ylabel)
            ax.grid(axis="y", linestyle=":", alpha=0.5)
            ax.legend(frameon=False)
            fig.tight_layout()
            fig.savefig(figure_dir / f"13_cig_{suffix}_{experiment}.png", dpi=200)
            plt.close(fig)

    snapshot_periods = [
        period
        for period in sorted(data["period"].unique())
        if int(period) % 5 == 0
    ]
    for variable, title, ylabel, filename, ylim in [
        (
            "mean_needs_index",
            "Distribution of mean Needs Index across calibrations",
            "Mean Needs Index",
            "14_needs_boxplots_every_5_periods.png",
            None,
        ),
        (
            "mean_vote_probability",
            "Distribution of political support across calibrations",
            "Mean vote probability",
            "15_political_support_boxplots_every_5_periods.png",
            (0.0, 1.0),
        ),
    ]:
        positions = []
        values = []
        box_colors = []
        offsets = np.linspace(-0.30, 0.30, len(experiments))
        for period_index, period in enumerate(snapshot_periods):
            for offset, experiment in zip(offsets, experiments):
                sample = data[
                    (data["period"] == period)
                    & (data["experiment_id"] == experiment)
                ][variable].dropna().to_numpy()
                positions.append(period_index + offset)
                values.append(sample)
                box_colors.append(colors[experiment])

        fig, ax = plt.subplots(figsize=(14, 7))
        boxes = ax.boxplot(
            values,
            positions=positions,
            widths=0.15,
            patch_artist=True,
            showfliers=False,
            whis=(2.5, 97.5),
            manage_ticks=False,
        )
        for box, color in zip(boxes["boxes"], box_colors):
            box.set(facecolor=color, edgecolor=color, alpha=0.58)
        for median in boxes["medians"]:
            median.set(color="black", linewidth=1.1)
        handles = [
            plt.Line2D([0], [0], color=colors[item], linewidth=8, alpha=0.58)
            for item in experiments
        ]
        ax.set(
            title=f"{title} — {calibration_count} LHS calibrations",
            xlabel="Period",
            ylabel=ylabel,
            xticks=np.arange(len(snapshot_periods)),
            xticklabels=[str(int(period)) for period in snapshot_periods],
        )
        if ylim is not None:
            ax.set_ylim(*ylim)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
        ax.legend(
            handles,
            [labels[item] for item in experiments],
            frameon=False,
            ncol=4,
        )
        fig.tight_layout()
        fig.savefig(figure_dir / filename, dpi=200)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--section",
        choices=["all", "robustness", "oat", "lhs"],
        default="all",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Output directory to analyze, e.g. outputs/sensitivity_300.",
    )
    args = parser.parse_args()
    robustness = PROJECT_ROOT / "outputs/robustness_30_seeds"
    sensitivity = (
        args.root
        if args.root is not None
        else PROJECT_ROOT / "outputs/sensitivity"
    )
    if args.section in {"all", "robustness"}:
        analyze_robustness(robustness)
    if args.section in {"all", "oat"}:
        analyze_oat(sensitivity)
    if args.section in {"all", "lhs"}:
        analyze_lhs(sensitivity)


if __name__ == "__main__":
    main()
