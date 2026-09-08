"""Multi-seed and sensitivity protocols for SEN-HARP Core."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

import numpy as np
import pandas as pd

from .entities import EmploymentStatus, PolicyMode, Scenario
from .labour_matching import is_private_employment_status
from .model import Model
from .parameters import Parameters


FIXED_IDS = ["E0_baseline", "E1_carbon_tax_fixed", "E3_green_deal_fixed", "E5_post_growth_fixed"]
PAIRED_CONTRASTS = {
    "E1_minus_E0": ("E1_carbon_tax_fixed", "E0_baseline"),
    "E3_minus_E0": ("E3_green_deal_fixed", "E0_baseline"),
    "E5_minus_E0": ("E5_post_growth_fixed", "E0_baseline"),
    "E2_minus_E1": ("E2_carbon_tax_vote", "E1_carbon_tax_fixed"),
    "E4_minus_E3": ("E4_green_deal_vote", "E3_green_deal_fixed"),
    "E6_minus_E5": ("E6_post_growth_vote", "E5_post_growth_fixed"),
}


def load_protocol_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as stream:
        return json.load(stream)


def resolved_parameters(config: dict, experiment: dict, seed: int, extra: dict | None = None) -> Parameters:
    values = dict(config.get("shared_parameter_overrides", {}))
    values.update(experiment.get("parameter_overrides", {}))
    values["seed"] = int(seed)
    if extra:
        values.update(extra)
    return Parameters(**values)


def run_experiment_summary(
    config: dict,
    experiment: dict,
    seed: int,
    extra_parameters: dict | None = None,
    needs_snapshots: list[dict] | None = None,
) -> list[dict[str, float | int | str]]:
    params = resolved_parameters(config, experiment, seed, extra_parameters)
    model = Model(
        params=params,
        scenario=Scenario[experiment["scenario"]],
        policy_mode=PolicyMode[experiment["policy_mode"]],
        public_service_spending_growth=config["run_control"].get(
            "public_service_spending_growth", 0.0
        ),
    )
    rows = []
    initial_needs: dict[int, float] = {}
    for period in range(int(config["run_control"]["number_of_periods"])):
        model.run_period(period)
        macro = model.collector.macro_rows[-1]
        if not initial_needs:
            initial_needs = {
                household.household_id: household.needs_index
                for household in model.households
            }
        if needs_snapshots is not None and period % 5 == 0:
            needs_snapshots.extend(
                {
                    "seed": seed,
                    "experiment_id": experiment["id"],
                    "experiment_label": experiment["label"],
                    "scenario": experiment["scenario"],
                    "policy_mode": experiment["policy_mode"],
                    "period": period,
                    "household_id": household.household_id,
                    "territory_id": household.territory_id,
                    "skill_level": household.skill_level.name,
                    "needs_index": household.needs_index,
                }
                for household in model.households
            )
        real_gdp = float(macro["real_gdp"])
        total_private_capital = sum(
            firm.brown_capital + firm.green_capital
            for firm in model.firms
        )
        capital_weighted_utilization = (
            sum(
                (firm.brown_capital + firm.green_capital)
                * firm.investment_capacity_utilization
                for firm in model.firms
            )
            / total_private_capital
            if total_private_capital > 0.0
            else 0.0
        )
        realised_market_demand = sum(
            float(row["realised_total_demand"])
            for row in model.current_market_settlement_results
        )
        unmet_market_demand = sum(
            float(row["unmet_total_demand"])
            for row in model.current_market_settlement_results
        )
        total_market_demand = (
            realised_market_demand + unmet_market_demand
        )
        winners = [
            household
            for household in model.households
            if household.needs_index >= initial_needs[household.household_id]
        ]
        losers = [
            household
            for household in model.households
            if household.needs_index < initial_needs[household.household_id]
        ]

        def mean_support(households: list) -> float:
            probabilities = [
                household.vote_probability
                for household in households
                if np.isfinite(household.vote_probability)
            ]
            return float(np.mean(probabilities)) if probabilities else np.nan

        labour = model.current_labour_market_results or {}
        household_count = len(model.households)
        target_jobs = int(labour.get("target_jobs", 0))
        filled_jobs = int(labour.get("filled_jobs", 0))
        vacancies = int(labour.get("vacancies", max(0, target_jobs - filled_jobs)))

        rows.append({
            "seed": seed,
            "experiment_id": experiment["id"],
            "experiment_label": experiment["label"],
            "scenario": experiment["scenario"],
            "policy_mode": experiment["policy_mode"],
            "period": period,
            "real_gdp": real_gdp,
            "nominal_gdp": macro["nominal_gdp"],
            "inflation_rate": macro["inflation_rate"],
            "income_gini": macro["income_gini"],
            "needs_index_gini": macro["needs_index_gini"],
            "job_guarantee_count": macro["job_guarantee_count"],
            "material_use": macro["material_use"],
            "labor_productivity": macro["labor_productivity"],
            "work_time_factor": model.current_work_time_factor,
            "mean_constrained_expenditure_burden": macro[
                "mean_constrained_expenditure_burden"
            ],
            "debt_to_gdp": (
                model.government.public_debt / real_gdp
                if real_gdp > 0.0
                else np.nan
            ),
            "industrial_emissions": macro["industrial_emissions"],
            "world_emissions": macro["world_emissions"],
            "atmospheric_temperature": macro["atmospheric_temperature"],
            "mean_needs_index": macro["mean_needs_index"],
            "mean_economic_disposable_income": macro[
                "mean_economic_disposable_income"
            ],
            "private_employment_rate": sum(
                is_private_employment_status(
                    household.employment_status
                )
                for household in model.households
            ) / len(model.households),
            "target_job_rate": (
                target_jobs / household_count if household_count else np.nan
            ),
            "filled_job_rate": (
                filled_jobs / household_count if household_count else np.nan
            ),
            "vacancy_rate": (
                vacancies / target_jobs if target_jobs > 0 else 0.0
            ),
            "layoff_rate": (
                int(labour.get("layoffs", 0)) / household_count
                if household_count else np.nan
            ),
            "hire_rate": (
                int(labour.get("hires", 0)) / household_count
                if household_count else np.nan
            ),
            "unemployment_rate": sum(
                household.employment_status
                == EmploymentStatus.UNEMPLOYED
                for household in model.households
            ) / len(model.households),
            "policy_active": macro["policy_active"],
            "election": macro["election"],
            "mean_vote_probability": macro["mean_vote_probability"],
            "last_election_support": macro["last_election_support"],
            "winner_vote_probability": mean_support(winners),
            "loser_vote_probability": mean_support(losers),
            "winner_household_share": len(winners) / len(model.households),
            "real_household_consumption": macro["real_household_consumption"],
            "real_private_investment": macro["real_private_investment"],
            "private_capital_to_gdp": (
                total_private_capital / real_gdp
                if real_gdp > 0.0
                else np.nan
            ),
            "private_investment_to_gdp": (
                float(macro["real_private_investment"]) / real_gdp
                if real_gdp > 0.0
                else np.nan
            ),
            "investment_capacity_utilization": (
                capital_weighted_utilization
            ),
            "unmet_demand_share": (
                unmet_market_demand / total_market_demand
                if total_market_demand > 0.0
                else 0.0
            ),
            "real_government_consumption": macro["real_government_consumption"],
            "real_public_investment": macro["real_public_investment"],
            "planned_ubs_private_consumption_replaced": float(
                (model.current_basic_services_substitution_results or {}).get(
                    "planned_private_consumption_replaced", 0.0
                )
            ),
            "planned_ubs_public_cost": (
                model.government.planned_basic_services_spending
            ),
            "realised_ubs_public_cost": (
                model.government.realised_basic_services_spending
            ),
            "brown_capital": sum(f.brown_capital for f in model.firms),
            "green_capital": sum(f.green_capital for f in model.firms),
            "public_green_capital": model.government.public_green_capital,
            "public_debt": model.government.public_debt,
        })
    return rows


def seed_level_outcomes(trajectories: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (seed, experiment_id), group in trajectories.groupby(["seed", "experiment_id"]):
        ordered = group.sort_values("period")
        periods = ordered["period"].to_numpy(float)
        rows.append({
            "seed": seed,
            "experiment_id": experiment_id,
            "final_real_gdp": ordered["real_gdp"].iloc[-1],
            "mean_real_gdp": ordered["real_gdp"].mean(),
            "auc_real_gdp": np.trapz(ordered["real_gdp"], periods),
            "final_needs_index": ordered["mean_needs_index"].iloc[-1],
            "mean_needs_index": ordered["mean_needs_index"].mean(),
            "auc_needs_index": np.trapz(ordered["mean_needs_index"], periods),
            "cumulative_industrial_emissions": ordered["industrial_emissions"].sum(),
            "final_public_debt": ordered["public_debt"].iloc[-1],
            "auc_public_debt": np.trapz(ordered["public_debt"], periods),
            "active_period_share": ordered["policy_active"].mean(),
        })
    return pd.DataFrame(rows)


def paired_contrasts(outcomes: pd.DataFrame) -> pd.DataFrame:
    wide = outcomes.set_index(["seed", "experiment_id"])
    metrics = [column for column in outcomes.columns if column not in {"seed", "experiment_id"}]
    rows = []
    for name, (left, right) in PAIRED_CONTRASTS.items():
        common = sorted(
            set(outcomes.loc[outcomes.experiment_id == left, "seed"])
            & set(outcomes.loc[outcomes.experiment_id == right, "seed"])
        )
        for seed in common:
            for metric in metrics:
                rows.append({
                    "seed": seed,
                    "contrast": name,
                    "metric": metric,
                    "difference": wide.loc[(seed, left), metric] - wide.loc[(seed, right), metric],
                })
    return pd.DataFrame(rows)


def bootstrap_contrast_summary(
    contrasts: pd.DataFrame,
    draws: int = 2000,
    seed: int = 1761,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for (contrast, metric), group in contrasts.groupby(["contrast", "metric"]):
        values = group["difference"].to_numpy(float)
        samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
        positive = float((values > 0.0).mean())
        negative = float((values < 0.0).mean())
        rows.append({
            "contrast": contrast,
            "metric": metric,
            "mean_difference": values.mean(),
            "median_difference": np.median(values),
            "bootstrap_ci_low": np.quantile(samples, 0.025),
            "bootstrap_ci_high": np.quantile(samples, 0.975),
            "positive_sign_frequency": positive,
            "negative_sign_frequency": negative,
            "sign_stability": max(positive, negative),
            "passes_80_percent_rule": int(max(positive, negative) >= 0.80),
        })
    return pd.DataFrame(rows)


def ranking_frequencies(outcomes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    directions = {
        "final_real_gdp": "max",
        "final_needs_index": "max",
        "cumulative_industrial_emissions": "min",
        "final_public_debt": "min",
    }
    fixed = outcomes[outcomes.experiment_id.isin(FIXED_IDS)]
    for metric, direction in directions.items():
        winners = []
        for _, group in fixed.groupby("seed"):
            index = group[metric].idxmax() if direction == "max" else group[metric].idxmin()
            winners.append(group.loc[index, "experiment_id"])
        counts = pd.Series(winners).value_counts(normalize=True)
        for experiment_id in FIXED_IDS:
            rows.append({
                "metric": metric,
                "preferred_direction": direction,
                "experiment_id": experiment_id,
                "winner_frequency": float(counts.get(experiment_id, 0.0)),
            })
    return pd.DataFrame(rows)


def export_robustness_analysis(trajectories: pd.DataFrame, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    outcomes = seed_level_outcomes(trajectories)
    contrasts = paired_contrasts(outcomes)
    outcomes.to_csv(output / "seed_level_outcomes.csv", index=False)
    contrasts.to_csv(output / "paired_contrasts.csv", index=False)
    bootstrap_contrast_summary(contrasts).to_csv(
        output / "bootstrap_contrast_summary.csv", index=False
    )
    ranking_frequencies(outcomes).to_csv(
        output / "ranking_frequencies.csv", index=False
    )


def write_resolved_parameter_manifest(config: dict, output_dir: str | Path, seed: int = 1761) -> None:
    output = Path(output_dir) / "resolved_parameters"
    output.mkdir(parents=True, exist_ok=True)
    for experiment in config["experiments"]:
        params = resolved_parameters(config, experiment, seed)
        with (output / f"{experiment['id']}.json").open("w", encoding="utf-8") as stream:
            json.dump(asdict(params), stream, indent=2, ensure_ascii=False)


OAT_PARAMETERS = [
    "alpha_affordability",
    "beta_relative_income",
    "weight_public_spending_growth",
    "weight_transport_burden",
    "weight_distance_to_services",
    "weight_basic_services_coverage",
]


def latin_hypercube_design(samples: int = 300, seed: int = 1761) -> pd.DataFrame:
    base = Parameters()
    central_values = {
        "post_growth_basic_income_ratio": 0.0,
        "post_growth_basic_services_ratio": 0.20,
    }
    ranges = {
        "initial_investment_rate": (0.5, 1.5),
        "capital_depreciation_rate": (0.5, 1.5),
        "propensity_to_consume_income": (0.9, 1.1),
        "firm_carbon_tax_rate": (0.5, 1.5),
        "household_carbon_tax_rate": (0.5, 1.5),
        "green_deal_public_investment_share": (0.5, 1.5),
        "post_growth_basic_services_ratio": (0.5, 1.5),
        "alpha_affordability": (0.5, 1.5),
        "w_needs_change": (0.5, 1.5),
    }
    rng = np.random.default_rng(seed)
    design = {"design_id": np.arange(samples)}
    for name, (low, high) in ranges.items():
        bins = (np.arange(samples) + rng.random(samples)) / samples
        rng.shuffle(bins)
        multipliers = low + (high - low) * bins
        central = float(central_values.get(name, getattr(base, name)))
        values = central * multipliers
        if name in {"propensity_to_consume_income", "green_deal_public_investment_share"}:
            values = np.clip(values, 0.0, 1.0)
        design[name] = values
    return pd.DataFrame(design)
