"""Planning of Green Deal public green investment."""

from .entities import (
    Firm,
    Government,
    PolicyState,
    Scenario,
)
from .parameters import Parameters


def plan_public_green_investment(
    government: Government,
    policy: PolicyState,
    params: Parameters,
    firms: list[Firm] | None = None,
    lagged_nominal_gdp: float | None = None,
) -> dict[str, float]:
    """Plan Green Deal investment using the factual-model rule.

    The state fills the gap required to grow the aggregate green
    capital base by 10%, capped at 10% of lagged nominal GDP. These
    defaults reproduce ``sen harp factuel.py``. There is no direct
    mechanical conversion of brown private capital into green capital.
    """

    investment_share = (
        params.green_deal_public_investment_share
    )

    if not 0.0 <= investment_share <= 1.0:
        raise ValueError(
            "green_deal_public_investment_share "
            "must be between zero and one."
        )

    base_capital_purchases = max(
        0.0,
        government.capital_purchases,
    )

    green_deal_active = (
        policy.active
        and policy.scenario == Scenario.GREEN_DEAL
    )

    growth_target = params.green_deal_green_capital_growth_target
    gdp_cap_share = params.green_deal_public_investment_gdp_cap

    if growth_target < 0.0:
        raise ValueError(
            "green_deal_green_capital_growth_target must be non-negative."
        )
    if not 0.0 <= gdp_cap_share <= 1.0:
        raise ValueError(
            "green_deal_public_investment_gdp_cap must be between zero and one."
        )

    private_green_capital = sum(
        max(0.0, firm.previous_green_capital)
        for firm in (firms or [])
        if firm.active
    )
    opening_green_capital = (
        private_green_capital
        + max(0.0, government.public_green_capital)
    )
    planned_private_green_investment = sum(
        max(0.0, firm.green_investment)
        for firm in (firms or [])
        if firm.active
    )
    green_capital_target = opening_green_capital * (1.0 + growth_target)
    expected_green_depreciation = (
        params.capital_depreciation_rate * private_green_capital
        + params.capital_depreciation_rate
        * max(0.0, government.public_green_capital)
    )
    green_investment_gap = max(
        0.0,
        green_capital_target
        - opening_green_capital
        + expected_green_depreciation
        - planned_private_green_investment,
    )
    public_green_budget_cap = (
        gdp_cap_share * max(0.0, lagged_nominal_gdp or 0.0)
    )

    if green_deal_active and lagged_nominal_gdp is not None:
        planned_public_green_investment = min(
            green_investment_gap,
            public_green_budget_cap,
        )
    elif green_deal_active and firms is None:
        # Backward-compatible fallback for direct legacy calls.
        planned_public_green_investment = (
            investment_share * max(0.0, government.carbon_tax_revenue)
        )
    else:
        planned_public_green_investment = 0.0

    government.base_capital_purchases = (
        base_capital_purchases
    )

    government.planned_public_green_investment = (
        planned_public_green_investment
    )

    # These flows will be determined after market settlement.
    government.realised_public_green_investment = 0.0
    government.unmet_public_green_investment = 0.0

    government.capital_purchases = (
        base_capital_purchases
        + planned_public_green_investment
    )

    government.capital_spending = (
        government.capital_purchases
    )

    # Government spending was initially calculated before the
    # additional Green Deal investment. Update the budget flows.
    government.primary_deficit = (
        government.current_spending
        + government.capital_spending
        - government.total_revenue
    )

    government.deficit = (
        government.primary_deficit
        + government.interest_payment
    )

    return {
        "base_capital_purchases": (
            base_capital_purchases
        ),
        "planned_public_green_investment": (
            planned_public_green_investment
        ),
        "total_planned_capital_purchases": (
            government.capital_purchases
        ),
        "green_deal_public_investment_share": (
            investment_share
        ),
        "opening_green_capital": opening_green_capital,
        "green_capital_target": green_capital_target,
        "planned_private_green_investment": planned_private_green_investment,
        "expected_green_depreciation": expected_green_depreciation,
        "green_investment_gap": green_investment_gap,
        "public_green_investment_gdp_cap": public_green_budget_cap,
    }
