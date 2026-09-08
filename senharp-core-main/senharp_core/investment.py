"""Firm investment decisions in SEN-HARP.

This module computes desired green and brown investment.
It does not yet grant credit or update capital stocks.
"""

from .entities import (
    Firm,
    PolicyState,
    Scenario,
)
from .parameters import Parameters


def snapshot_firm_opening_state(
    firm: Firm,
) -> None:
    """Store the state inherited from the previous period."""

    firm.previous_brown_capital = (
        firm.brown_capital
    )
    firm.previous_green_capital = (
        firm.green_capital
    )

    firm.previous_brown_loans = (
        firm.brown_loans
    )
    firm.previous_green_loans = (
        firm.green_loans
    )

    firm.previous_profits = firm.profits

    firm.previous_brown_loan_interest_rate = (
        firm.brown_loan_interest_rate
    )
    firm.previous_green_loan_interest_rate = (
        firm.green_loan_interest_rate
    )


def reset_firm_investment_flows(
    firm: Firm,
) -> None:
    """Reset current-period investment flows."""

    firm.cash_flow_ratio = 0.0
    firm.investment_leverage = 0.0
    firm.investment_capacity_utilization = 0.0
    
    firm.firm_carbon_cost = 0.0
    firm.carbon_tax_paid = 0.0

    firm.desired_brown_capital_growth = 0.0
    firm.desired_green_capital_growth = 0.0

    firm.desired_brown_investment = 0.0
    firm.desired_green_investment = 0.0

    firm.brown_loan_demand = 0.0
    firm.green_loan_demand = 0.0

    firm.brown_loans_granted = 0.0
    firm.green_loans_granted = 0.0

    firm.brown_investment = 0.0
    firm.green_investment = 0.0
    firm.profit_tax_paid = 0.0
    firm.dividends_paid = 0.0
    firm.brown_self_financed_investment = 0.0
    firm.green_self_financed_investment = 0.0


def firm_carbon_tax_is_active(
    policy: PolicyState,
) -> bool:
    """Return whether brown firm capital is carbon-taxed."""

    return (
        policy.active
        and policy.scenario
        in {
            Scenario.CARBON_TAX,
            Scenario.GREEN_DEAL,
        }
    )


def compute_desired_investment(
    firm: Firm,
    period: int,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Compute desired investment for one firm."""

    reset_firm_investment_flows(
        firm=firm,
    )

    if not firm.active:
        return

    # Period 0 is the first observed economic period and therefore
    # contains the same reproducible investment flow as period 1.
    if period == 0:
        firm.desired_brown_investment = (
            params.initial_investment_rate
            * firm.previous_brown_capital
        )
        firm.desired_green_investment = (
            params.initial_investment_rate
            * firm.previous_green_capital
        )
        firm.brown_loan_demand = firm.desired_brown_investment
        firm.green_loan_demand = firm.desired_green_investment
        return

    if not 0.0 <= params.firm_profit_tax_rate <= 1.0:
        raise ValueError("firm_profit_tax_rate must be between zero and one.")
    if not 0.0 <= params.firm_dividend_payout_ratio <= 1.0:
        raise ValueError("firm_dividend_payout_ratio must be between zero and one.")

    positive_profit = max(0.0, firm.previous_profits)
    firm.profit_tax_paid = params.firm_profit_tax_rate * positive_profit
    after_tax_profit = positive_profit - firm.profit_tax_paid
    firm.dividends_paid = params.firm_dividend_payout_ratio * after_tax_profit
    firm.retained_earnings += after_tax_profit - firm.dividends_paid

    previous_total_capital = (
        firm.previous_brown_capital
        + firm.previous_green_capital
    )

    previous_total_debt = (
        firm.previous_brown_loans
        + firm.previous_green_loans
    )

    if previous_total_capital > 0.0:
        firm.cash_flow_ratio = (
            firm.previous_profits
            / previous_total_capital
        )

        firm.investment_leverage = (
            previous_total_debt
            / previous_total_capital
        )
    else:
        firm.cash_flow_ratio = 0.0
        firm.investment_leverage = 0.0

    # Investment decisions are made at the opening of the period,
    # before current productive capacity is recomputed. These fields
    # therefore contain the preceding period's realised and potential
    # output and provide a genuinely lagged utilisation signal.
    if firm.potential_output > 0.0:
        firm.investment_capacity_utilization = min(
            1.0,
            max(
                0.0,
                firm.actual_output / firm.potential_output,
            ),
        )

    # Current carbon-tax amount. It remains zero when
    # the package is inactive.
    carbon_tax_amount = 0.0

    if firm_carbon_tax_is_active(policy):
        carbon_tax_base = max(
            0.0,
            firm.previous_brown_capital,
        )

        carbon_tax_amount = (
            params.firm_carbon_tax_rate
            * carbon_tax_base
        )

    # Behavioural signal used in the investment equation.
    firm.firm_carbon_cost = carbon_tax_amount

    # Monetary payment deducted from profits and received
    # by the government.
    firm.carbon_tax_paid = carbon_tax_amount

    firm.desired_brown_capital_growth = max(
        0.0,
        firm.animal_spirits_brown
        + firm.gamma_cash_flow
        * firm.cash_flow_ratio
        - firm.gamma_leverage
        * firm.investment_leverage
        + firm.gamma_capacity
        * firm.investment_capacity_utilization
        - firm.gamma_interest
        * firm.previous_brown_loan_interest_rate
        - params.brown_investment_carbon_sensitivity
        * firm.firm_carbon_cost,
    )

    firm.desired_green_capital_growth = max(
        0.0,
        firm.animal_spirits_green
        + firm.gamma_cash_flow
        * firm.cash_flow_ratio
        - firm.gamma_leverage
        * firm.investment_leverage
        + firm.gamma_capacity
        * firm.investment_capacity_utilization
        - firm.gamma_interest
        * firm.previous_green_loan_interest_rate,
    )

    if period == params.initial_investment_period:
        firm.desired_brown_investment = (
            params.initial_investment_rate
            * firm.previous_brown_capital
        )

        firm.desired_green_investment = (
            params.initial_investment_rate
            * firm.previous_green_capital
        )
    else:
        firm.desired_brown_investment = max(
            0.0,
            (
                firm.desired_brown_capital_growth
                + params.capital_depreciation_rate
            )
            * firm.previous_brown_capital,
        )

        firm.desired_green_investment = max(
            0.0,
            (
                firm.desired_green_capital_growth
                + params.capital_depreciation_rate
            )
            * firm.previous_green_capital,
        )

    total_desired = firm.desired_brown_investment + firm.desired_green_investment
    self_financing = min(firm.retained_earnings, total_desired)
    if total_desired > 0.0:
        firm.brown_self_financed_investment = (
            self_financing * firm.desired_brown_investment / total_desired
        )
        firm.green_self_financed_investment = (
            self_financing - firm.brown_self_financed_investment
        )
    firm.retained_earnings -= self_financing

    firm.brown_loan_demand = max(
        0.0, firm.desired_brown_investment - firm.brown_self_financed_investment
    )
    firm.green_loan_demand = max(
        0.0, firm.desired_green_investment - firm.green_self_financed_investment
    )


def compute_investment_decisions(
    firms: list[Firm],
    period: int,
    policy: PolicyState,
    params: Parameters,
) -> None:
    """Snapshot and compute investment for all firms."""

    for firm in firms:
        snapshot_firm_opening_state(
            firm=firm,
        )

        compute_desired_investment(
            firm=firm,
            period=period,
            policy=policy,
            params=params,
        )
