import pytest

from senharp_core.entities import (
    EmploymentStatus,
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_model(
    scenario,
    policy_mode,
):
    return Model(
        params=Parameters(
            seed=1761,
        ),
        scenario=scenario,
        policy_mode=policy_mode,
        public_service_spending_growth=0.0,
    )


def economic_snapshot(model):
    """Return the non-political state of the model."""

    return {
        # Production and firms
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

        # Households and social outcomes
        "economic_disposable_income": sum(
            household.economic_disposable_income
            for household in model.households
        ),
        "needs_index": sum(
            household.needs_index
            for household in model.households
        ),
        "unemployed": sum(
            household.employment_status
            == EmploymentStatus.UNEMPLOYED
            for household in model.households
        ),

        # Banking and public finance
        "bank_firm_loans": sum(
            bank.total_firm_loans
            for bank in model.banks
        ),
        "bank_consumer_loans": sum(
            bank.consumer_loans
            for bank in model.banks
        ),
        "bank_household_deposits": sum(
            bank.household_deposits
            for bank in model.banks
        ),
        "public_debt": (
            model.government.public_debt
        ),
        "government_revenue": (
            model.government.total_revenue
        ),
        "central_bank_bonds": (
            model.central_bank.government_bonds
        ),
        "central_bank_reserves": (
            model.central_bank.bank_reserves
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


def test_carbon_tax_off_reproduces_baseline():
    """An inactive package must be economically neutral."""

    baseline = build_model(
        scenario=Scenario.BASELINE,
        policy_mode=PolicyMode.OFF,
    )

    carbon_tax_off = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.OFF,
    )

    for period in range(26):
        baseline.run_period(
            period=period,
        )

        carbon_tax_off.run_period(
            period=period,
        )

        baseline_state = economic_snapshot(
            baseline
        )

        policy_off_state = economic_snapshot(
            carbon_tax_off
        )

        assert (
            policy_off_state
            == pytest.approx(
                baseline_state,
                rel=1e-12,
                abs=1e-12,
            )
        ), (
            "CARBON_TAX + OFF diverges from the "
            f"baseline at period {period}."
        )
