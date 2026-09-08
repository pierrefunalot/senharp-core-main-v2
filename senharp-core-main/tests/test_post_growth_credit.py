from types import SimpleNamespace

import pytest

from senharp_core.banking import (
    brown_credit_policy_factor,
    grant_firm_credit,
)
from senharp_core.entities import (
    Firm,
    Scenario,
)
from senharp_core.parameters import Parameters


def build_test_firm() -> Firm:
    """Create a firm with fixed brown and green credit demand."""

    firm = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=50.0,
    )

    firm.brown_loan_demand = 100.0
    firm.green_loan_demand = 100.0

    return firm


def test_active_post_growth_policy_caps_brown_credit_only():
    """The post-growth cap must apply only to brown credit."""

    params = Parameters(
        credit_constraint_rate=0.10,
        post_growth_brown_credit_cap=0.20,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.POST_GROWTH,
    )

    firm = build_test_firm()

    grant_firm_credit(
        firm=firm,
        policy=policy,
        params=params,
    )

    # General credit factor:
    # 1 - 0.10 = 0.90.
    assert firm.green_loans_granted == pytest.approx(
        100.0 * 0.90
    )

    # Brown credit also receives the post-growth factor:
    # 100 * 0.90 * 0.20 = 18.
    assert firm.brown_loans_granted == pytest.approx(
        100.0 * 0.90 * 0.20
    )

    # Realised investment is entirely credit-financed.
    assert firm.green_investment == pytest.approx(
        firm.green_loans_granted
    )

    assert firm.brown_investment == pytest.approx(
        firm.brown_loans_granted
    )


def test_inactive_post_growth_policy_does_not_cap_brown_credit():
    """An inactive package must leave brown credit uncapped."""

    params = Parameters(
        credit_constraint_rate=0.10,
        post_growth_brown_credit_cap=0.20,
    )

    policy = SimpleNamespace(
        active=False,
        scenario=Scenario.POST_GROWTH,
    )

    firm = build_test_firm()

    grant_firm_credit(
        firm=firm,
        policy=policy,
        params=params,
    )

    assert firm.green_loans_granted == pytest.approx(
        90.0
    )

    assert firm.brown_loans_granted == pytest.approx(
        90.0
    )


def test_active_non_post_growth_policy_does_not_cap_brown_credit():
    """The brown cap must not affect another policy package."""

    params = Parameters(
        credit_constraint_rate=0.10,
        post_growth_brown_credit_cap=0.20,
    )

    policy = SimpleNamespace(
        active=True,
        scenario=Scenario.CARBON_TAX,
    )

    firm = build_test_firm()

    assert brown_credit_policy_factor(
        policy=policy,
        params=params,
    ) == pytest.approx(1.0)

    grant_firm_credit(
        firm=firm,
        policy=policy,
        params=params,
    )

    assert firm.green_loans_granted == pytest.approx(
        90.0
    )

    assert firm.brown_loans_granted == pytest.approx(
        90.0
    )