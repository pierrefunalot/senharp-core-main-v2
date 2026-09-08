import pytest

from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_fixed_model(
    scenario,
):
    return Model(
        params=Parameters(
            seed=1761,

            # Neutralise the additional instrument so that
            # the Green Deal skeleton remains comparable.
            green_deal_public_investment_share=0.0,
        ),
        scenario=scenario,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )


def non_political_snapshot(model):
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


def test_green_deal_adds_differentiated_credit_and_dividend():
    """The Green Deal must differ through credit and revenue recycling."""

    carbon_tax = build_fixed_model(
        Scenario.CARBON_TAX
    )

    green_deal = build_fixed_model(
        Scenario.GREEN_DEAL
    )

    for period in range(6):
        carbon_tax.run_period(
            period=period,
        )

        green_deal.run_period(
            period=period,
        )

        assert carbon_tax.government.carbon_dividend_spending == pytest.approx(0.0)
        assert green_deal.government.carbon_dividend_spending > 0.0
        assert sum(
            household.carbon_dividend_income
            for household in green_deal.households
        ) == pytest.approx(
            green_deal.government.carbon_dividend_spending
        )
        assert green_deal.central_bank.green_policy_rate < (
            green_deal.central_bank.brown_policy_rate
        )
        assert green_deal.central_bank.green_policy_rate != pytest.approx(
            carbon_tax.central_bank.green_policy_rate
        )
