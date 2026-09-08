"""Capital and firm-debt accumulation in SEN-HARP."""

from .entities import (
    Firm,
    PolicyState,
    Scenario,
)
from .parameters import Parameters
from .climate import split_lagged_climate_damage

def reset_accumulation_flows(
    firm: Firm,
) -> None:
    """Reset current-period depreciation and repayment flows."""

    firm.brown_depreciation = 0.0
    firm.green_depreciation = 0.0
    firm.brown_policy_retirement = 0.0

    firm.brown_loan_repayment = 0.0
    firm.green_loan_repayment = 0.0


def brown_capital_retention_factor(
    policy: PolicyState,
    params: Parameters,
) -> float:
    """Return the policy-specific brown-capital retention rate."""

    post_growth_active = (
        policy.active
        and policy.scenario == Scenario.POST_GROWTH
    )

    if post_growth_active:
        return params.post_growth_brown_capital_retention

    return 1.0

def apply_lagged_climate_capital_damage(
    firms: list[Firm],
    lagged_climate_damage: float,
    params: Parameters,
) -> None:
    """Destroy part of opening productive capital.

    The climate damage calculated at the end of period t-1
    affects the opening capital available for production in t.

    The loss does not reduce deposits or outstanding loans.
    """

    (
        _,
        capital_damage_rate,
    ) = split_lagged_climate_damage(
        lagged_climate_damage=(
            lagged_climate_damage
        ),
        params=params,
    )

    for firm in firms:
        firm.climate_capital_damage_rate = 0.0

        firm.climate_brown_capital_loss = 0.0
        firm.climate_green_capital_loss = 0.0
        firm.climate_capital_loss = 0.0

        firm.opening_brown_capital_before_climate_damage = (
            max(
                0.0,
                firm.brown_capital,
            )
        )

        firm.opening_green_capital_before_climate_damage = (
            max(
                0.0,
                firm.green_capital,
            )
        )

        if not firm.active:
            continue

        firm.climate_capital_damage_rate = (
            capital_damage_rate
        )

        firm.climate_brown_capital_loss = (
            capital_damage_rate
            * firm.opening_brown_capital_before_climate_damage
        )

        firm.climate_green_capital_loss = (
            capital_damage_rate
            * firm.opening_green_capital_before_climate_damage
        )

        firm.climate_capital_loss = (
            firm.climate_brown_capital_loss
            + firm.climate_green_capital_loss
        )

        firm.brown_capital = max(
            0.0,
            (
                firm.opening_brown_capital_before_climate_damage
                - firm.climate_brown_capital_loss
            ),
        )

        firm.green_capital = max(
            0.0,
            (
                firm.opening_green_capital_before_climate_damage
                - firm.climate_green_capital_loss
            ),
        )
   
def accumulate_firm_capital_and_debt(
    firm: Firm,
    period: int,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Update one firm's end-of-period capital and loan stocks.

    Opening capital is used for current-period production.
    Current investment enters the closing capital stock and
    becomes productive in the following period.
    """

    reset_accumulation_flows(
        firm=firm,
    )

    if not firm.active:
        return

    if not 0.0 <= params.capital_depreciation_rate <= 1.0:
        raise ValueError(
            "capital_depreciation_rate must be "
            "between 0 and 1."
        )

    if not 0.0 <= params.firm_loan_repayment_rate <= 1.0:
        raise ValueError(
            "firm_loan_repayment_rate must be "
            "between 0 and 1."
        )

    if not (
        0.0
        <= params.post_growth_brown_capital_retention
        <= 1.0
    ):
        raise ValueError(
            "post_growth_brown_capital_retention must be "
            "between 0 and 1."
        )

    previous_brown_capital = max(
        0.0,
        firm.previous_brown_capital,
    )

    previous_green_capital = max(
        0.0,
        firm.previous_green_capital,
    )

    climate_adjusted_brown_capital = max(
        0.0,
        (
            previous_brown_capital
            - firm.climate_brown_capital_loss
        ),
    )

    climate_adjusted_green_capital = max(
        0.0,
        (
            previous_green_capital
            - firm.climate_green_capital_loss
        ),
    )
    
    previous_brown_loans = max(
        0.0,
        firm.previous_brown_loans,
    )

    previous_green_loans = max(
        0.0,
        firm.previous_green_loans,
    )

    
    # Normal depreciation applies only to capital that survived
# the opening climate shock.
    firm.brown_depreciation = (
        params.capital_depreciation_rate
        * climate_adjusted_brown_capital
    )

    firm.green_depreciation = (
        params.capital_depreciation_rate
        * climate_adjusted_green_capital
    )

    remaining_brown_capital = (
        climate_adjusted_brown_capital
        - firm.brown_depreciation
    )

    remaining_green_capital = (
        climate_adjusted_green_capital
        - firm.green_depreciation
    )

    # Additional retirement of brown capital under
    # an active post-growth package.
    brown_retention = (
        brown_capital_retention_factor(
            policy=policy,
            params=params,
        )
    )

    firm.brown_policy_retirement = (
        (1.0 - brown_retention)
        * remaining_brown_capital
    )

    remaining_brown_capital -= (
        firm.brown_policy_retirement
    )

    # Closing productive-capital stocks.
    firm.brown_capital = max(
        0.0,
        remaining_brown_capital
        + firm.brown_investment,
    )

    firm.green_capital = max(
        0.0,
        remaining_green_capital
        + firm.green_investment,
    )

    # Repayment of loan principal.
    firm.brown_loan_repayment = (
        params.firm_loan_repayment_rate
        * previous_brown_loans
    )

    firm.green_loan_repayment = (
        params.firm_loan_repayment_rate
        * previous_green_loans
    )

    # Closing loan stocks.
    firm.brown_loans = max(
        0.0,
        previous_brown_loans
        - firm.brown_loan_repayment
        + firm.brown_loans_granted,
    )

    firm.green_loans = max(
        0.0,
        previous_green_loans
        - firm.green_loan_repayment
        + firm.green_loans_granted,
    )


def accumulate_capital_and_debt(
    firms: list[Firm],
    period: int,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Update capital and loan stocks for all firms."""

    for firm in firms:
        accumulate_firm_capital_and_debt(
            firm=firm,
            period=period,
            policy=policy,
            params=params,
        )
