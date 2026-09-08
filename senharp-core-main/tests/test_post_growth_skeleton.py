import pytest

from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_model(
    scenario: Scenario,
    policy_mode: PolicyMode,
) -> Model:
    """Build a model for the post-growth neutrality test."""

    return Model(
        params=Parameters(
            seed=1761,

            # Neutral post-growth financial instruments.
            post_growth_brown_credit_cap=1.0,
            post_growth_brown_credit_cap_decay_rate=0.0,
            post_growth_brown_credit_extinction_after=0,
            post_growth_brown_capital_retention=1.0,
            post_growth_progressive_tax_rate=0.0,
            post_growth_work_time_reduction=0.0,

            # Neutral post-growth public-purchase rule.
            post_growth_government_purchase_growth_rate=0.02,

            # Neutral post-growth environmental shortcut.
            post_growth_emissions_multiplier=1.0,
        ),
        scenario=scenario,
        policy_mode=policy_mode,
        public_service_spending_growth=0.0,
    )


def non_political_snapshot(model: Model) -> dict[str, float]:
    """Return the current non-political model state."""

    return {
        # Firms and production
        "actual_output": sum(
            firm.actual_output
            for firm in model.firms
        ),
        "potential_output": sum(
            firm.potential_output
            for firm in model.firms
        ),
        "brown_capital": sum(
            firm.brown_capital
            for firm in model.firms
        ),
        "green_capital": sum(
            firm.green_capital
            for firm in model.firms
        ),
        "brown_loans": sum(
            firm.brown_loans
            for firm in model.firms
        ),
        "green_loans": sum(
            firm.green_loans
            for firm in model.firms
        ),
        "profits": sum(
            firm.profits
            for firm in model.firms
        ),
        "carbon_tax_paid": sum(
            firm.carbon_tax_paid
            for firm in model.firms
        ),

        # Households
        "economic_disposable_income": sum(
            household.economic_disposable_income
            for household in model.households
        ),
        "legacy_disposable_income": sum(
            household.disposable_income
            for household in model.households
        ),
        "base_consumption_cost": sum(
            household.base_consumption_cost
            for household in model.households
        ),
        "needs_index": sum(
            household.needs_index
            for household in model.households
        ),

        # Public finance
        "carbon_tax_revenue": (
            model.government.carbon_tax_revenue
        ),
        "public_debt": (
            model.government.public_debt
        ),

        # Credit conditions
        "green_policy_rate": (
            model.central_bank.green_policy_rate
        ),
        "brown_policy_rate": (
            model.central_bank.brown_policy_rate
        ),

        # Environment and climate
        "household_emissions": (
            model.total_emissions
        ),
        "pollution_stock": (
            model.pollution_stock
        ),
        "industrial_emissions": (
            model.industrial_emissions
        ),
        "world_emissions": (
            model.world_emissions
        ),
        "atmospheric_carbon": (
            model.atmospheric_carbon
        ),
        "atmospheric_temperature": (
            model.atmospheric_temperature
        ),
        "climate_damage": (
            model.climate_damage
        ),
    }


def test_post_growth_fixed_matches_baseline_when_instruments_are_neutral():
    """A neutral post-growth package must reproduce the baseline."""

    baseline = build_model(
        scenario=Scenario.BASELINE,
        policy_mode=PolicyMode.OFF,
    )

    post_growth = build_model(
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
    )

    for period in range(6):
        baseline.run_period(
            period=period,
        )

        post_growth.run_period(
            period=period,
        )

        baseline_state = (
            non_political_snapshot(
                baseline
            )
        )

        post_growth_state = (
            non_political_snapshot(
                post_growth
            )
        )

        assert post_growth_state == pytest.approx(
            baseline_state,
            rel=1e-12,
            abs=1e-12,
        ), (
            "The neutral post-growth package diverges "
            f"from the baseline at period {period}."
        )
