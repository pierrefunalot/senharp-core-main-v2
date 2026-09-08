"""Firm credit conditions in SEN-HARP.

The canonical specification assumes no general bank credit rationing. Policy may nevertheless restrict brown credit
under an active post-growth package.
"""

from .entities import (
    Bank,
    CentralBank,
    Firm,
    PolicyState,
    Scenario,
)
from .parameters import Parameters


def update_central_bank_credit_rates(
    central_bank: CentralBank,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Set green and brown refinancing rates."""

    green_deal_active = (
        policy.active
        and policy.scenario == Scenario.GREEN_DEAL
    )

    if green_deal_active:
        central_bank.green_policy_rate = (
            params.green_deal_green_credit_rate
        )
        central_bank.brown_policy_rate = (
            params.green_deal_brown_credit_rate
        )
    else:
        central_bank.green_policy_rate = (
            params.standard_green_credit_rate
        )
        central_bank.brown_policy_rate = (
            params.standard_brown_credit_rate
        )

    # General policy rate retained as a reference rate.
    central_bank.policy_rate = (
        central_bank.green_policy_rate
        + central_bank.brown_policy_rate
    ) / 2.0

    central_bank.reserve_rate = (
        central_bank.policy_rate
    )


def compute_bank_markup(
    bank: Bank,
    params: Parameters,
) -> float:
    """Return the commercial-bank interest-rate markup."""

    if bank.market_share < 0.0:
        raise ValueError(
            f"Bank {bank.bank_id} has a negative market share."
        )

    return (
        params.bank_markup_coefficient
        * bank.market_share
    )


def update_firm_credit_rates(
    firms: list[Firm],
    banks: list[Bank],
    central_bank: CentralBank,
    params: Parameters,
) -> None:
    """Assign current green and brown credit rates to firms."""

    banks_by_id = {
        bank.bank_id: bank
        for bank in banks
    }

    for firm in firms:
        if firm.bank_id not in banks_by_id:
            raise ValueError(
                f"Firm {firm.firm_id} is linked to "
                f"unknown bank {firm.bank_id}."
            )

        bank = banks_by_id[firm.bank_id]

        markup = compute_bank_markup(
            bank=bank,
            params=params,
        )

        firm.green_loan_interest_rate = (
            central_bank.green_policy_rate
            + markup
        )

        firm.brown_loan_interest_rate = (
            central_bank.brown_policy_rate
            + markup
        )


def brown_credit_policy_factor(
    policy: PolicyState,
    params: Parameters,
) -> float:
    """Return the policy factor applied to brown credit."""

    post_growth_active = (
        policy.active
        and policy.scenario == Scenario.POST_GROWTH
    )

    if post_growth_active:
        active_periods = max(
            1,
            int(getattr(policy, "consecutive_active_periods", 1)),
        )
        extinction_after = int(
            params.post_growth_brown_credit_extinction_after
        )
        if extinction_after > 0 and active_periods >= extinction_after:
            return 0.0
        return max(
            params.post_growth_brown_credit_cap_floor,
            params.post_growth_brown_credit_cap
            * (1.0 - params.post_growth_brown_credit_cap_decay_rate)
            ** (active_periods - 1),
        )

    return 1.0


def grant_firm_credit(
    firm: Firm,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Grant credit and determine realised investment."""

    if not firm.active:
        firm.brown_loans_granted = 0.0
        firm.green_loans_granted = 0.0
        firm.brown_investment = 0.0
        firm.green_investment = 0.0
        return

    if not 0.0 <= params.credit_constraint_rate <= 1.0:
        raise ValueError(
            "credit_constraint_rate must be "
            "between 0 and 1."
        )

    if not 0.0 <= params.post_growth_brown_credit_cap <= 1.0:
        raise ValueError(
            "post_growth_brown_credit_cap must be "
            "between 0 and 1."
        )
    if not 0.0 <= params.post_growth_brown_credit_cap_decay_rate <= 1.0:
        raise ValueError(
            "post_growth_brown_credit_cap_decay_rate must be "
            "between 0 and 1."
        )
    if not 0.0 <= params.post_growth_brown_credit_cap_floor <= 1.0:
        raise ValueError(
            "post_growth_brown_credit_cap_floor must be between 0 and 1."
        )
    if params.post_growth_brown_credit_extinction_after < 0:
        raise ValueError(
            "post_growth_brown_credit_extinction_after must be "
            "non-negative."
        )

    general_credit_factor = (
        1.0
        - params.credit_constraint_rate
    )

    brown_policy_factor = (
        brown_credit_policy_factor(
            policy=policy,
            params=params,
        )
    )

    firm.green_loans_granted = max(
        0.0,
        firm.green_loan_demand
        * general_credit_factor,
    )

    firm.brown_loans_granted = max(
        0.0,
        firm.brown_loan_demand
        * general_credit_factor
        * brown_policy_factor,
    )

    firm.green_investment = (
        firm.green_loans_granted
        + firm.green_self_financed_investment
    )

    firm.brown_investment = (
        firm.brown_loans_granted
        + firm.brown_self_financed_investment
    )


def update_credit_conditions(
    firms: list[Firm],
    banks: list[Bank],
    central_bank: CentralBank,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Update rates and grant credit to all firms."""

    update_central_bank_credit_rates(
        central_bank=central_bank,
        policy=policy,
        params=params,
    )

    update_firm_credit_rates(
        firms=firms,
        banks=banks,
        central_bank=central_bank,
        params=params,
    )

    for firm in firms:
        grant_firm_credit(
            firm=firm,
            policy=policy,
            params=params,
        )
