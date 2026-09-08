import pytest

from senharp_core.entities import (
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


def run_two_periods(
    model,
):
    model.run_period(
        period=0,
    )

    model.run_period(
        period=1,
    )


def test_fixed_carbon_tax_is_recorded_as_government_revenue():
    """Firm and household payments must have a public counterpart."""

    model = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    run_two_periods(
        model
    )

    total_expected_carbon_cost = sum(
        firm.firm_carbon_cost
        for firm in model.firms
    )

    total_carbon_tax_paid = sum(
        firm.carbon_tax_paid
        for firm in model.firms
    )

    assert total_expected_carbon_cost > 0.0

    assert total_carbon_tax_paid == pytest.approx(
        total_expected_carbon_cost,
        rel=1e-12,
        abs=1e-12,
    )

    household_tax_paid = sum(
        household.household_carbon_tax_paid
        for household in model.households
    )

    assert household_tax_paid > 0.0
    assert model.government.firm_carbon_tax_revenue == pytest.approx(
        total_carbon_tax_paid,
    )
    assert model.government.household_carbon_tax_revenue == pytest.approx(
        household_tax_paid,
    )
    assert model.government.carbon_tax_revenue == pytest.approx(
        total_carbon_tax_paid + household_tax_paid,
    )
    assert model.government.carbon_dividend_spending == pytest.approx(0.0)


def test_off_carbon_tax_has_no_revenue():
    """No carbon-tax revenue may exist when the package is off."""

    model = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.OFF,
    )

    run_two_periods(
        model
    )

    total_firm_carbon_cost = sum(
        firm.firm_carbon_cost
        for firm in model.firms
    )

    total_carbon_tax_paid = sum(
        firm.carbon_tax_paid
        for firm in model.firms
    )

    assert total_carbon_tax_paid == pytest.approx(
        0.0,
        abs=1e-12,
    )

    assert total_firm_carbon_cost == pytest.approx(
        0.0,
        abs=1e-12,
    )

    assert (
        model.government.carbon_tax_revenue
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )

def test_carbon_tax_is_deducted_from_firm_profits():
    """Firm profits must be net of current carbon-tax payments."""

    model = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    run_two_periods(
        model
    )

    for firm in model.firms:
        expected_profits = (
            firm.revenue
            - firm.wage_bill
            - firm.interest_paid
            - firm.carbon_tax_paid
        )

        assert firm.profits == pytest.approx(
            expected_profits,
            rel=1e-12,
            abs=1e-12,
        )

def test_collector_records_carbon_tax_flow():
    """Macro revenue must equal collected firm and household payments."""

    model = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    run_two_periods(
        model
    )

    macro_row = (
        model.collector.macro_rows[-1]
    )

    firm_rows = [
        row
        for row in model.collector.firm_rows
        if row["period"] == 1
    ]

    collected_firm_payments = sum(
        row["carbon_tax_paid"]
        for row in firm_rows
    )

    collected_firm_costs = sum(
        row["firm_carbon_cost"]
        for row in firm_rows
    )

    household_rows = [
        row
        for row in model.collector.household_rows
        if row["period"] == 1
    ]
    collected_household_payments = sum(
        row["household_carbon_tax_paid"]
        for row in household_rows
    )

    assert collected_firm_payments > 0.0

    assert (
        collected_firm_payments
        == pytest.approx(
            collected_firm_costs,
            rel=1e-12,
            abs=1e-12,
        )
    )

    assert (
        macro_row["carbon_tax_revenue"]
        == pytest.approx(
            collected_firm_payments
            + collected_household_payments,
            rel=1e-12,
            abs=1e-12,
        )
    )
    assert macro_row["firm_carbon_tax_revenue"] == pytest.approx(
        collected_firm_payments,
    )
    assert macro_row["household_carbon_tax_revenue"] == pytest.approx(
        collected_household_payments,
    )

def test_collector_records_firm_profits():
    """Collected firm profits must match current firm profits."""

    model = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    run_two_periods(model)

    firm_rows = [
        row
        for row in model.collector.firm_rows
        if row["period"] == 1
    ]

    firms_by_id = {
        firm.firm_id: firm
        for firm in model.firms
    }

    assert len(firm_rows) == len(model.firms)

    for row in firm_rows:
        firm = firms_by_id[
            row["firm_id"]
        ]

        assert row["profits"] == pytest.approx(
            firm.profits,
            rel=1e-12,
            abs=1e-12,
        )
