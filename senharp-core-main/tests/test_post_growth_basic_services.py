from types import SimpleNamespace

import pytest

from senharp_core.basic_services import (
    plan_post_growth_basic_services,
    settle_post_growth_basic_services,
)
from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.government_demand import (
    compute_sector_government_demand,
)
from senharp_core.model import Model
from senharp_core.needs_index import (
    compute_public_service_component,
)

from senharp_core.parameters import Parameters

SECTORS = (
    "agriculture",
    "energy",
    "housing",
    "transport",
    "industry",
    "technology",
)


def build_sector_government():
    return SimpleNamespace(
        current_purchases=120.0,
        base_current_purchases=100.0,
        planned_basic_services_spending=20.0,

        base_capital_purchases=40.0,
        planned_public_green_investment=0.0,

        realised_basic_services_spending=20.0,
        unmet_basic_services_spending=0.0,
    )


def build_market_rows(
    sector_results,
    delivery_ratio,
):
    rows = []

    for sector in SECTORS:
        planned = sector_results[
            f"{sector}_current_government_demand"
        ]

        rows.append(
            {
                "sector": sector,
                "planned_current_government_demand": (
                    planned
                ),
                "realised_current_government_demand": (
                    planned * delivery_ratio
                ),
            }
        )

    return rows


def test_sector_demand_separates_basic_services():
    params = Parameters(
        post_growth_basic_services_ratio=0.20,
    )

    government = build_sector_government()

    results = compute_sector_government_demand(
        government=government,
        params=params,
    )

    assert results[
        "total_current_government_demand"
    ] == pytest.approx(120.0)

    total_basic_services = sum(
        results[
            f"{sector}_basic_services_"
            "government_demand"
        ]
        for sector in SECTORS
    )

    assert total_basic_services == pytest.approx(
        20.0
    )

    for sector in SECTORS:
        assert results[
            f"{sector}_current_government_demand"
        ] == pytest.approx(
            results[
                f"{sector}_base_current_"
                "government_demand"
            ]
            + results[
                f"{sector}_basic_services_"
                "government_demand"
            ]
        )


def test_fully_delivered_basic_services_are_distributed():
    params = Parameters()

    government = build_sector_government()

    sector_results = compute_sector_government_demand(
        government=government,
        params=params,
    )

    households = [
        SimpleNamespace(
            base_consumption_cost=50.0,
            basic_services_received=0.0,
            basic_services_coverage=0.0,
            basic_services_component=0.0,
        ),
        SimpleNamespace(
            base_consumption_cost=50.0,
            basic_services_received=0.0,
            basic_services_coverage=0.0,
            basic_services_component=0.0,
        ),
    ]

    results = settle_post_growth_basic_services(
        government=government,
        households=households,
        sector_government_demand_results=(
            sector_results
        ),
        market_settlement_results=(
            build_market_rows(
                sector_results=sector_results,
                delivery_ratio=1.0,
            )
        ),
    )

    assert (
        government.realised_basic_services_spending
        == pytest.approx(20.0)
    )

    assert (
        government.unmet_basic_services_spending
        == pytest.approx(0.0)
    )

    for household in households:
        assert household.basic_services_received == (
            pytest.approx(10.0)
        )

        assert household.basic_services_coverage == (
            pytest.approx(0.20)
        )

    assert results[
        "basic_services_household_allocation_gap"
    ] == pytest.approx(0.0)


def test_rationed_basic_services_follow_delivery_ratio():
    params = Parameters()

    government = build_sector_government()

    sector_results = compute_sector_government_demand(
        government=government,
        params=params,
    )

    households = [
        SimpleNamespace(
            base_consumption_cost=50.0,
            basic_services_received=0.0,
            basic_services_coverage=0.0,
            basic_services_component=0.0,
        ),
        SimpleNamespace(
            base_consumption_cost=50.0,
            basic_services_received=0.0,
            basic_services_coverage=0.0,
            basic_services_component=0.0,
        ),
    ]

    results = settle_post_growth_basic_services(
        government=government,
        households=households,
        sector_government_demand_results=(
            sector_results
        ),
        market_settlement_results=(
            build_market_rows(
                sector_results=sector_results,
                delivery_ratio=0.50,
            )
        ),
    )

    assert (
        government.realised_basic_services_spending
        == pytest.approx(10.0)
    )

    assert (
        government.unmet_basic_services_spending
        == pytest.approx(10.0)
    )

    for household in households:
        assert household.basic_services_received == (
            pytest.approx(5.0)
        )

    assert results[
        "basic_services_settlement_gap"
    ] == pytest.approx(0.0)


def test_basic_services_enter_public_service_component():
    params = Parameters(
        weight_public_spending_growth=0.0,
        weight_transport_burden=0.0,
        weight_distance_to_services=0.0,
        weight_basic_services_coverage=0.10,
    )

    household = SimpleNamespace(
        economic_disposable_income=100.0,
        transport_cost=0.0,
        distance_to_public_services=0.0,
        basic_services_coverage=0.40,
        basic_services_component=0.0,
        transport_cost_burden=0.0,
        public_service_component=0.0,
        previous_basic_services_coverage=0.0,
        basic_services_coverage_change=0.0,
    )

    result = compute_public_service_component(
        household=household,
        public_service_spending_growth=0.0,
        params=params,
    )

    assert result == pytest.approx(0.04)

    assert household.basic_services_component == (
        pytest.approx(0.04)
    )


def test_model_integrates_delivered_basic_services():
    common = {
        "seed": 1761,
        "post_growth_brown_credit_cap": 1.0,
        "post_growth_brown_capital_retention": 1.0,
        "post_growth_emissions_multiplier": 1.0,
    }

    model_without_ubs = Model(
        params=Parameters(
            **common,
            post_growth_basic_services_ratio=0.0,
        ),
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    model_with_ubs = Model(
        params=Parameters(
            **common,
            post_growth_basic_services_ratio=0.20,
        ),
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    model_without_ubs.run_period(period=0)
    model_with_ubs.run_period(period=0)

    realised_ubs = (
        model_with_ubs.government
        .realised_basic_services_spending
    )

    household_ubs = sum(
        household.basic_services_received
        for household in model_with_ubs.households
    )

    assert realised_ubs > 0.0

    delivery_ratio = (
        realised_ubs
        / model_with_ubs.government.planned_basic_services_spending
    )
    assert household_ubs == pytest.approx(
        sum(
            household.planned_basic_services_received
            for household in model_with_ubs.households
        )
        * delivery_ratio
    )

    assert (
        model_with_ubs.government
        .planned_basic_services_spending
        == pytest.approx(
            realised_ubs
            + model_with_ubs.government
            .unmet_basic_services_spending
        )
    )

    # UBS are received in kind, not as household income.
    assert sum(
        household.economic_disposable_income
        for household in model_with_ubs.households
    ) == pytest.approx(
        sum(
            household.economic_disposable_income
            for household in model_without_ubs.households
        )
    )

    assert (
        sum(
            household.needs_index
            for household in model_with_ubs.households
        )
        > sum(
            household.needs_index
            for household in model_without_ubs.households
        )
    )

def build_government():
    return SimpleNamespace(
        current_purchases=100.0,
        planned_current_purchases=100.0,
        realised_current_purchases=100.0,
        unmet_current_purchases=0.0,

        capital_spending=40.0,

        transfer_spending=20.0,
        public_wage_spending=30.0,

        total_revenue=10.0,
        interest_payment=5.0,

        current_spending=150.0,
        primary_deficit=180.0,
        deficit=185.0,

        base_current_purchases=0.0,
        planned_basic_services_spending=0.0,
        realised_basic_services_spending=0.0,
        unmet_basic_services_spending=0.0,
    )


def build_household():
    return SimpleNamespace(
        transfer_income=25.0,
        gross_income=100.0,
        economic_disposable_income=90.0,
    )


def test_active_post_growth_plans_basic_services():
    params = Parameters(
        post_growth_basic_services_ratio=0.20,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.POST_GROWTH,
    )

    government = build_government()

    households = [
        build_household(),
        build_household(),
    ]

    results = plan_post_growth_basic_services(
        government=government,
        households=households,
        policy=policy,
        params=params,
        minimum_wage=50.0,
    )

    # 20% × 50 = 10 per household.
    assert results[
        "unit_basic_services"
    ] == pytest.approx(10.0)

    assert results[
        "planned_basic_services_spending"
    ] == pytest.approx(20.0)

    assert government.base_current_purchases == (
        pytest.approx(100.0)
    )

    assert government.current_purchases == (
        pytest.approx(120.0)
    )

    assert government.planned_current_purchases == (
        pytest.approx(120.0)
    )

    assert government.current_spending == (
        pytest.approx(170.0)
    )

    assert government.primary_deficit == (
        pytest.approx(200.0)
    )

    assert government.deficit == (
        pytest.approx(205.0)
    )

    assert results[
        "basic_services_planning_gap"
    ] == pytest.approx(0.0)


def test_basic_services_do_not_enter_household_income():
    params = Parameters(
        post_growth_basic_services_ratio=0.20,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.POST_GROWTH,
    )

    government = build_government()
    household = build_household()

    initial_transfer = household.transfer_income
    initial_gross_income = household.gross_income
    initial_disposable_income = (
        household.economic_disposable_income
    )

    plan_post_growth_basic_services(
        government=government,
        households=[household],
        policy=policy,
        params=params,
        minimum_wage=50.0,
    )

    assert household.transfer_income == (
        pytest.approx(initial_transfer)
    )

    assert household.gross_income == (
        pytest.approx(initial_gross_income)
    )

    assert household.economic_disposable_income == (
        pytest.approx(initial_disposable_income)
    )


def test_inactive_post_growth_plans_no_basic_services():
    params = Parameters(
        post_growth_basic_services_ratio=0.20,
    )

    policy = SimpleNamespace(
        active=False,
        scenario=Scenario.POST_GROWTH,
    )

    government = build_government()

    results = plan_post_growth_basic_services(
        government=government,
        households=[
            build_household(),
            build_household(),
        ],
        policy=policy,
        params=params,
        minimum_wage=50.0,
    )

    assert results[
        "post_growth_basic_services_active"
    ] == 0

    assert results[
        "planned_basic_services_spending"
    ] == pytest.approx(0.0)

    assert government.current_purchases == (
        pytest.approx(100.0)
    )

    assert government.primary_deficit == (
        pytest.approx(180.0)
    )

    assert government.deficit == (
        pytest.approx(185.0)
    )

def test_stable_basic_services_coverage_does_not_raise_growth():
    params = Parameters(
        weight_public_spending_growth=0.0,
        weight_transport_burden=0.0,
        weight_distance_to_services=0.0,
        weight_basic_services_coverage=0.10,
    )

    household = SimpleNamespace(
        economic_disposable_income=100.0,
        transport_cost=0.0,
        distance_to_public_services=0.0,
        previous_basic_services_coverage=0.40,
        basic_services_coverage=0.40,
        basic_services_coverage_change=0.0,
        basic_services_component=0.0,
        transport_cost_burden=0.0,
        public_service_component=0.0,
    )

    result = compute_public_service_component(
        household=household,
        public_service_spending_growth=0.0,
        params=params,
    )

    assert result == pytest.approx(0.0)

    assert household.basic_services_component == (
        pytest.approx(0.0)
    )


def test_falling_basic_services_coverage_reduces_growth():
    params = Parameters(
        weight_public_spending_growth=0.0,
        weight_transport_burden=0.0,
        weight_distance_to_services=0.0,
        weight_basic_services_coverage=0.10,
    )

    household = SimpleNamespace(
        economic_disposable_income=100.0,
        transport_cost=0.0,
        distance_to_public_services=0.0,
        previous_basic_services_coverage=0.40,
        basic_services_coverage=0.20,
        basic_services_coverage_change=0.0,
        basic_services_component=0.0,
        transport_cost_burden=0.0,
        public_service_component=0.0,
    )

    result = compute_public_service_component(
        household=household,
        public_service_spending_growth=0.0,
        params=params,
    )

    assert result == pytest.approx(-0.02)

    assert household.basic_services_component == (
        pytest.approx(-0.02)
    )
