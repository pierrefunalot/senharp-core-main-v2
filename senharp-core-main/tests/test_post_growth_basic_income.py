from types import SimpleNamespace

import pytest

from senharp_core.basic_income import (
    apply_post_growth_basic_income,
)
from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_test_household():
    return SimpleNamespace(
        transfer_income=20.0,
        gross_income=100.0,
        basic_income_income=0.0,
    )


def test_active_post_growth_basic_income_enters_gross_income():
    params = Parameters(
        post_growth_basic_income_ratio=0.20,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.POST_GROWTH,
    )

    households = [
        build_test_household(),
        build_test_household(),
    ]

    results = apply_post_growth_basic_income(
        households=households,
        policy=policy,
        params=params,
        minimum_wage=50.0,
    )

    # 20% of a minimum wage equal to 50.
    assert results[
        "unit_basic_income"
    ] == pytest.approx(10.0)

    assert results[
        "total_basic_income"
    ] == pytest.approx(20.0)

    assert results[
        "basic_income_accounting_gap"
    ] == pytest.approx(0.0)

    for household in households:
        assert (
            household.basic_income_income
            == pytest.approx(10.0)
        )

        assert (
            household.transfer_income
            == pytest.approx(30.0)
        )

        assert (
            household.gross_income
            == pytest.approx(110.0)
        )


def test_inactive_post_growth_package_pays_no_basic_income():
    params = Parameters(
        post_growth_basic_income_ratio=0.20,
    )

    policy = SimpleNamespace(
        active=False,
        scenario=Scenario.POST_GROWTH,
    )

    household = build_test_household()
    household.basic_income_income = 15.0

    results = apply_post_growth_basic_income(
        households=[household],
        policy=policy,
        params=params,
        minimum_wage=50.0,
    )

    assert results[
        "total_basic_income"
    ] == pytest.approx(0.0)

    assert (
        household.basic_income_income
        == pytest.approx(0.0)
    )

    assert (
        household.transfer_income
        == pytest.approx(20.0)
    )

    assert (
        household.gross_income
        == pytest.approx(100.0)
    )


def test_basic_income_is_recorded_as_public_transfer():
    ratio = 0.20

    params = Parameters(
        seed=1761,
        post_growth_brown_credit_cap=1.0,
        post_growth_brown_capital_retention=1.0,
        post_growth_emissions_multiplier=1.0,
        post_growth_basic_income_ratio=ratio,
    )

    model = Model(
        params=params,
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    model.run_period(period=0)

    unit_basic_income = (
        ratio
        * model.current_income_results[
            "minimum_wage"
        ]
    )

    expected_total = (
        len(model.households)
        * unit_basic_income
    )

    household_total = sum(
        household.basic_income_income
        for household in model.households
    )

    assert household_total == pytest.approx(
        expected_total
    )

    assert (
        model.government.basic_income_spending
        == pytest.approx(expected_total)
    )

    assert (
        model.current_basic_income_results[
            "basic_income_accounting_gap"
        ]
        == pytest.approx(0.0)
    )

    # Total public transfer spending includes basic income
    # and the pre-existing unemployment transfers.
    assert (
        model.government.transfer_spending
        == pytest.approx(
            sum(
                household.transfer_income
                for household in model.households
            )
        )
    )
def test_basic_income_net_effect_matches_transfer_tax_rule():
    """At period zero, net income equals BI minus its tax."""

    common_parameters = {
        "seed": 1761,
        "post_growth_brown_credit_cap": 1.0,
        "post_growth_brown_capital_retention": 1.0,
        "post_growth_emissions_multiplier": 1.0,
        "tax_household_transfers": True,
        "household_income_tax_rate": 0.10,
        "post_growth_progressive_tax_rate": 0.0,
        "post_growth_basic_income_offsets_unemployment_benefit": False,
    }

    model_without_bi = Model(
        params=Parameters(
            **common_parameters,
            post_growth_basic_income_ratio=0.0,
        ),
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    model_with_bi = Model(
        params=Parameters(
            **common_parameters,
            post_growth_basic_income_ratio=0.20,
        ),
        scenario=Scenario.POST_GROWTH,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    model_without_bi.run_period(period=0)
    model_with_bi.run_period(period=0)

    gross_basic_income = sum(
        household.basic_income_income
        for household in model_with_bi.households
    )

    additional_tax = (
        sum(
            household.income_tax_paid
            for household in model_with_bi.households
        )
        - sum(
            household.income_tax_paid
            for household in model_without_bi.households
        )
    )

    additional_disposable_income = (
        sum(
            household.economic_disposable_income
            for household in model_with_bi.households
        )
        - sum(
            household.economic_disposable_income
            for household in model_without_bi.households
        )
    )

    assert additional_tax == pytest.approx(
        0.10 * gross_basic_income
    )

    assert additional_disposable_income == pytest.approx(
        gross_basic_income - additional_tax
    )
