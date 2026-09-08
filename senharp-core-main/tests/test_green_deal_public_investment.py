import pytest

from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_model(
    scenario,
    policy_mode=PolicyMode.FIXED,
    investment_share=0.50,
):
    return Model(
        params=Parameters(
            seed=1761,
            green_deal_public_investment_share=(
                investment_share
            ),
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


def test_green_deal_uses_factual_green_capital_target_and_gdp_cap():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    run_two_periods(
        model
    )

    assert model.government.carbon_tax_revenue > 0.0
    results = model.current_public_green_investment_results
    expected = min(
        results["green_investment_gap"],
        results["public_green_investment_gdp_cap"],
    )
    assert model.government.planned_public_green_investment == pytest.approx(expected)
    assert results["planned_public_green_investment"] == pytest.approx(expected)


def test_green_investment_is_allocated_to_technology():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    run_two_periods(
        model
    )

    base_technology_demand = (
        model.government.base_capital_purchases
        * model.params.government_capital_technology_share
    )

    expected_technology_demand = (
        base_technology_demand
        + model.government.planned_public_green_investment
    )

    observed_technology_demand = (
        model.current_sector_government_demand_results[
            "technology_capital_government_demand"
        ]
    )

    assert observed_technology_demand == pytest.approx(
        expected_technology_demand,
        rel=1e-12,
        abs=1e-12,
    )


def test_market_package_has_no_public_green_investment():
    model = build_model(
        scenario=Scenario.CARBON_TAX,
    )

    run_two_periods(
        model
    )

    assert model.government.carbon_tax_revenue > 0.0

    assert (
        model.government.planned_public_green_investment
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )

def get_technology_settlement_row(
    model,
):
    rows = [
        row
        for row in model.current_market_settlement_results
        if str(
            row["sector"]
        ).lower() == "technology"
    ]

    assert len(rows) == 1

    return rows[0]


def test_public_green_investment_follows_technology_delivery():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    run_two_periods(
        model
    )

    technology_row = (
        get_technology_settlement_row(
            model
        )
    )

    planned_technology_capital = float(
        technology_row[
            "planned_capital_government_demand"
        ]
    )

    realised_technology_capital = float(
        technology_row[
            "realised_capital_government_demand"
        ]
    )

    if planned_technology_capital <= 1e-12:
        expected_delivery_ratio = 1.0
    else:
        expected_delivery_ratio = min(
            1.0,
            max(
                0.0,
                realised_technology_capital
                / planned_technology_capital,
            ),
        )

    expected_realised_green_investment = (
        model.government.planned_public_green_investment
        * expected_delivery_ratio
    )

    assert (
        model.government.realised_public_green_investment
        == pytest.approx(
            expected_realised_green_investment,
            rel=1e-12,
            abs=1e-12,
        )
    )


def test_public_green_investment_flow_identity():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    run_two_periods(
        model
    )

    assert (
        model.government.planned_public_green_investment
        == pytest.approx(
            (
                model.government
                .realised_public_green_investment
                + model.government
                .unmet_public_green_investment
            ),
            rel=1e-12,
            abs=1e-12,
        )
    )

    assert (
        model.current_government_settlement_results[
            "public_green_investment_balance_gap"
        ]
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )


def test_realised_public_green_investment_accumulates():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    run_two_periods(
        model
    )

    # The opening public stock is zero. At period 1 there is
    # therefore no depreciation, so the closing stock equals
    # the investment delivered during that period.
    assert model.government.public_green_capital == pytest.approx(
        model.government.realised_public_green_investment,
        rel=1e-12,
        abs=1e-12,
    )

    assert (
        model.current_public_green_capital_results[
            "public_green_capital_identity_gap"
        ]
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )


def test_market_package_accumulates_no_public_green_capital():
    model = build_model(
        scenario=Scenario.CARBON_TAX,
    )

    run_two_periods(
        model
    )

    assert (
        model.government.realised_public_green_investment
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )

    assert (
        model.government.public_green_capital
        == pytest.approx(
            0.0,
            abs=1e-12,
        )
    )
    
def test_government_collector_records_one_row_per_period():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    for period in range(6):
        model.run_period(
            period=period,
        )

    assert len(
        model.collector.government_rows
    ) == 6

    final_row = (
        model.collector.government_rows[-1]
    )

    assert final_row[
        "planned_public_green_investment"
    ] == pytest.approx(
        model.government
        .planned_public_green_investment,
        rel=1e-12,
        abs=1e-12,
    )

    assert final_row[
        "public_green_capital"
    ] == pytest.approx(
        model.government.public_green_capital,
        rel=1e-12,
        abs=1e-12,
    )


def test_collected_public_green_investment_identity():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    for period in range(6):
        model.run_period(
            period=period,
        )

    for row in model.collector.government_rows:
        assert row[
            "planned_public_green_investment"
        ] == pytest.approx(
            (
                row[
                    "realised_public_green_investment"
                ]
                + row[
                    "unmet_public_green_investment"
                ]
            ),
            rel=1e-12,
            abs=1e-12,
        )

        assert row[
            "public_green_investment_balance_gap"
        ] == pytest.approx(
            0.0,
            abs=1e-12,
        )


def test_collected_public_green_capital_identity():
    model = build_model(
        scenario=Scenario.GREEN_DEAL,
    )

    for period in range(6):
        model.run_period(
            period=period,
        )

    rows = model.collector.government_rows

    for previous_row, current_row in zip(
        rows[:-1],
        rows[1:],
    ):
        expected_closing_stock = (
            previous_row[
                "public_green_capital"
            ]
            - current_row[
                "public_green_capital_depreciation"
            ]
            + current_row[
                "realised_public_green_investment"
            ]
        )

        assert current_row[
            "public_green_capital"
        ] == pytest.approx(
            expected_closing_stock,
            rel=1e-12,
            abs=1e-12,
        )

        assert current_row[
            "public_green_capital_identity_gap"
        ] == pytest.approx(
            0.0,
            abs=1e-12,
        )
