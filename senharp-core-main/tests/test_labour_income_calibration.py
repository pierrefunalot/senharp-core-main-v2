import pytest

from senharp_core.entities import EmploymentStatus
from senharp_core.income import status_income_multiplier
from senharp_core.parameters import Parameters


def test_default_unemployment_benefit_is_40_percent_of_base_wage():
    params = Parameters()

    multiplier = status_income_multiplier(
        status=EmploymentStatus.UNEMPLOYED,
        params=params,
    )

    assert multiplier == pytest.approx(0.40)


def test_experimental_labour_calibration_defaults():
    params = Parameters()

    assert params.calibrated_labor_productivity == pytest.approx(325.5)
    assert params.nominal_wage_growth_rate == pytest.approx(0.0)


def test_factual_capital_productivity_defaults():
    params = Parameters()

    assert params.initial_private_capital_scale == pytest.approx(12.5)
    assert params.base_productivity == pytest.approx(2.4)
    assert params.green_productivity_gain == pytest.approx(1.6)
    assert params.firm_carbon_tax_rate == pytest.approx(0.016)
    assert (
        params.initial_private_capital_scale
        * params.base_productivity
    ) == pytest.approx(30.0)
    assert (
        params.initial_private_capital_scale
        * params.green_productivity_gain
    ) == pytest.approx(20.0)
    assert (
        params.initial_private_capital_scale
        * params.firm_carbon_tax_rate
    ) == pytest.approx(0.20)
