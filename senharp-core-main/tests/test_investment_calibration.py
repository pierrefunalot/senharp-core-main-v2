from types import SimpleNamespace

import pytest

from senharp_core.capital_accumulation import accumulate_firm_capital_and_debt
from senharp_core.entities import Firm, Scenario, Sector
from senharp_core.investment import compute_desired_investment
from senharp_core.parameters import Parameters


def test_initial_investment_rate_is_applied_to_opening_capital():
    params = Parameters(initial_investment_rate=0.03)
    firm = Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0)
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 20.0
    policy = SimpleNamespace(active=False, scenario=Scenario.BASELINE)

    compute_desired_investment(firm, 1, policy, params)

    assert firm.desired_brown_investment == pytest.approx(3.0)
    assert firm.desired_green_investment == pytest.approx(0.6)


def test_opening_period_contains_reproducible_investment_demand():
    params = Parameters(initial_investment_rate=0.03)
    firm = Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0)
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 20.0
    policy = SimpleNamespace(active=False, scenario=Scenario.BASELINE)

    compute_desired_investment(firm, 0, policy, params)

    assert firm.desired_brown_investment == pytest.approx(3.0)
    assert firm.desired_green_investment == pytest.approx(0.6)
    assert firm.brown_loan_demand == pytest.approx(3.0)
    assert firm.green_loan_demand == pytest.approx(0.6)


def test_opening_investment_enters_closing_capital_and_debt():
    params = Parameters(
        capital_depreciation_rate=0.01,
        firm_loan_repayment_rate=0.0,
    )
    firm = Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0)
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 20.0
    firm.previous_brown_loans = 25.0
    firm.previous_green_loans = 5.0
    firm.brown_investment = 3.0
    firm.green_investment = 0.6
    firm.brown_loans_granted = 3.0
    firm.green_loans_granted = 0.6
    policy = SimpleNamespace(active=False, scenario=Scenario.BASELINE)

    accumulate_firm_capital_and_debt(firm, 0, policy, params)

    assert firm.brown_capital == pytest.approx(102.0)
    assert firm.green_capital == pytest.approx(20.4)
    assert firm.brown_loans == pytest.approx(28.0)
    assert firm.green_loans == pytest.approx(5.6)


def test_current_calibration_grows_capital_when_initial_investment_is_delivered():
    params = Parameters(
        initial_investment_rate=0.03,
        capital_depreciation_rate=0.01,
        firm_loan_repayment_rate=0.0,
    )
    firm = Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0)
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 20.0
    firm.brown_investment = 3.0
    firm.green_investment = 0.6
    policy = SimpleNamespace(active=False, scenario=Scenario.BASELINE)

    accumulate_firm_capital_and_debt(firm, 1, policy, params)

    assert firm.brown_capital == pytest.approx(102.0)
    assert firm.green_capital == pytest.approx(20.4)
    assert firm.brown_policy_retirement == pytest.approx(0.0)


def test_desired_growth_uses_lagged_realised_capacity_utilization():
    params = Parameters(capital_depreciation_rate=0.03)
    firm = Firm(
        firm_id=0,
        sector=Sector.INDUSTRY,
        bank_id=0,
        animal_spirits_brown=0.02,
        animal_spirits_green=0.02,
        gamma_cash_flow=0.0,
        gamma_leverage=0.0,
        gamma_capacity=0.10,
        gamma_interest=0.0,
    )
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 20.0
    firm.actual_output = 50.0
    firm.potential_output = 100.0
    policy = SimpleNamespace(active=False, scenario=Scenario.BASELINE)

    compute_desired_investment(firm, 2, policy, params)

    assert firm.investment_capacity_utilization == pytest.approx(0.50)
    assert firm.desired_brown_capital_growth == pytest.approx(0.07)
    assert firm.desired_green_capital_growth == pytest.approx(0.07)
    # The growth equation is net: gross investment also replaces normal
    # depreciation of the opening capital stock.
    assert firm.desired_brown_investment == pytest.approx(10.0)
    assert firm.desired_green_investment == pytest.approx(2.0)
