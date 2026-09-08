from types import SimpleNamespace

import pytest

from senharp_core.capital_accumulation import (
    accumulate_firm_capital_and_debt,
    brown_capital_retention_factor,
)
from senharp_core.entities import (
    Firm,
    Scenario,
)
from senharp_core.parameters import Parameters


def build_test_firm() -> Firm:
    """Create a firm with controlled opening stocks and flows."""

    firm = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=50.0,
    )

    # Opening capital stocks.
    firm.previous_brown_capital = 100.0
    firm.previous_green_capital = 50.0

    # Opening climate losses.
    firm.climate_brown_capital_loss = 10.0
    firm.climate_green_capital_loss = 5.0

    # New investment delivered during the period.
    firm.brown_investment = 20.0
    firm.green_investment = 10.0

    # Opening loan stocks and newly granted loans.
    firm.previous_brown_loans = 30.0
    firm.previous_green_loans = 20.0
    firm.brown_loans_granted = 5.0
    firm.green_loans_granted = 7.0

    return firm


def test_active_post_growth_policy_retires_inherited_brown_capital():
    """Post-growth retirement applies before new brown investment."""

    params = Parameters(
        capital_depreciation_rate=0.10,
        post_growth_brown_capital_retention=0.80,
        firm_loan_repayment_rate=0.0,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.POST_GROWTH,
    )

    firm = build_test_firm()

    accumulate_firm_capital_and_debt(
        firm=firm,
        period=1,
        policy=policy,
        params=params,
    )

    # Brown capital after the climate loss:
    # 100 - 10 = 90.
    assert firm.brown_depreciation == pytest.approx(
        9.0
    )

    # Capital remaining after ordinary depreciation:
    # 90 - 9 = 81.
    #
    # Additional post-growth retirement:
    # (1 - 0.80) * 81 = 16.2.
    assert firm.brown_policy_retirement == pytest.approx(
        16.2
    )

    # Retained inherited capital:
    # 81 - 16.2 = 64.8.
    #
    # New investment is added afterwards:
    # 64.8 + 20 = 84.8.
    assert firm.brown_capital == pytest.approx(
        84.8
    )

    # The post-growth retirement does not apply
    # to green capital:
    #
    # (50 - 5) * (1 - 0.10) + 10 = 50.5.
    assert firm.green_depreciation == pytest.approx(
        4.5
    )

    assert firm.green_capital == pytest.approx(
        50.5
    )

    # The retirement of productive capital does not
    # automatically cancel the corresponding bank loans.
    assert firm.brown_loans == pytest.approx(
        35.0
    )

    assert firm.green_loans == pytest.approx(
        27.0
    )


def test_inactive_post_growth_policy_does_not_retire_brown_capital():
    """An inactive post-growth package must not accelerate retirement."""

    params = Parameters(
        capital_depreciation_rate=0.10,
        post_growth_brown_capital_retention=0.80,
        firm_loan_repayment_rate=0.0,
    )

    policy = SimpleNamespace(
        active=False,
        scenario=Scenario.POST_GROWTH,
    )

    firm = build_test_firm()

    assert brown_capital_retention_factor(
        policy=policy,
        params=params,
    ) == pytest.approx(1.0)

    accumulate_firm_capital_and_debt(
        firm=firm,
        period=1,
        policy=policy,
        params=params,
    )

    assert firm.brown_policy_retirement == pytest.approx(
        0.0
    )

    # (100 - 10) * (1 - 0.10) + 20 = 101.
    assert firm.brown_capital == pytest.approx(
        101.0
    )


def test_non_post_growth_policy_does_not_retire_brown_capital():
    """The retention parameter must not affect another package."""

    params = Parameters(
        capital_depreciation_rate=0.10,
        post_growth_brown_capital_retention=0.80,
        firm_loan_repayment_rate=0.0,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.CARBON_TAX,
    )

    firm = build_test_firm()

    assert brown_capital_retention_factor(
        policy=policy,
        params=params,
    ) == pytest.approx(1.0)

    accumulate_firm_capital_and_debt(
        firm=firm,
        period=1,
        policy=policy,
        params=params,
    )

    assert firm.brown_policy_retirement == pytest.approx(
        0.0
    )

    assert firm.brown_capital == pytest.approx(
        101.0
    )