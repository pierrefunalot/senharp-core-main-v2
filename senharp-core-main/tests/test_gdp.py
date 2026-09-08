import pytest

from senharp_core.entities import Firm, Sector
from senharp_core.gdp import compute_market_gdp


def test_period_zero_nominal_and_real_gdp_are_equal():
    firms = [
        Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0),
        Firm(firm_id=1, sector=Sector.TECHNOLOGY, bank_id=0),
    ]
    firms[0].price = 2.0
    firms[0].sales_quantity = 10.0
    firms[0].revenue = 20.0
    firms[1].price = 4.0
    firms[1].sales_quantity = 5.0
    firms[1].revenue = 20.0

    settlement = [{
        "sector": "industry",
        "realised_total_demand": 20.0,
        "realised_essential_household_demand": 10.0,
        "realised_supplementary_household_demand": 0.0,
        "realised_private_investment_demand": 5.0,
        "realised_current_government_demand": 3.0,
        "realised_capital_government_demand": 2.0,
    }, {
        "sector": "technology",
        "realised_total_demand": 20.0,
        "realised_essential_household_demand": 5.0,
        "realised_supplementary_household_demand": 5.0,
        "realised_private_investment_demand": 4.0,
        "realised_current_government_demand": 3.0,
        "realised_capital_government_demand": 3.0,
    }]
    results = compute_market_gdp(firms, settlement, {}, None)

    assert results["nominal_gdp"] == pytest.approx(40.0)
    assert results["real_gdp"] == pytest.approx(40.0)
    assert results["gdp_deflator"] == pytest.approx(100.0)
    assert results["gdp_revenue_identity_gap"] == pytest.approx(0.0)
    assert results["nominal_household_consumption"] == pytest.approx(20.0)
    assert results["nominal_private_investment"] == pytest.approx(9.0)
    assert results["nominal_government_consumption"] == pytest.approx(6.0)
    assert results["nominal_public_investment"] == pytest.approx(5.0)


def test_real_gdp_uses_fixed_reference_prices():
    firm = Firm(firm_id=0, sector=Sector.INDUSTRY, bank_id=0)
    firm.price = 2.0
    firm.sales_quantity = 10.0
    firm.revenue = 20.0
    reference_prices: dict[int, float] = {}
    settlement = [{
        "sector": "industry",
        "realised_total_demand": 20.0,
        "realised_essential_household_demand": 20.0,
        "realised_supplementary_household_demand": 0.0,
        "realised_private_investment_demand": 0.0,
        "realised_current_government_demand": 0.0,
        "realised_capital_government_demand": 0.0,
    }]
    compute_market_gdp([firm], settlement, reference_prices, None)

    firm.price = 3.0
    firm.sales_quantity = 12.0
    firm.revenue = 36.0
    settlement[0]["realised_total_demand"] = 36.0
    settlement[0]["realised_essential_household_demand"] = 36.0
    results = compute_market_gdp([firm], settlement, reference_prices, 20.0)

    assert results["nominal_gdp"] == pytest.approx(36.0)
    assert results["real_gdp"] == pytest.approx(24.0)
    assert results["gdp_deflator"] == pytest.approx(150.0)
    assert results["real_gdp_growth"] == pytest.approx(0.20)
