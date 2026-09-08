"""Government spending and public-purchase budget in SEN-HARP."""

from .entities import EmploymentStatus, Firm, Government, Household
from .parameters import Parameters


def update_government_spending(
    government: Government,
    households: list[Household],
    params: Parameters,
    period: int,
    firms: list[Firm] | None = None,
    purchase_growth_rate_override: float | None = None,
) -> dict[str, float]:
    """Compute public spending and the primary budget balance.

    In full-model runs, initial direct public purchases are calibrated
    as a share of opening C + I + G. Direct unit calls without firms
    retain the historical revenue-residual fallback. Purchases then
    follow an exogenous nominal growth rate.
    """

    capital_share = (
        params.government_capital_purchase_share
    )

    purchase_growth_rate = (
        params.government_purchase_growth_rate
        if purchase_growth_rate_override is None
        else purchase_growth_rate_override
    )

    if not 0.0 <= capital_share <= 1.0:
        raise ValueError(
            "government_capital_purchase_share "
            "must be between zero and one."
        )

    if purchase_growth_rate <= -1.0:
        raise ValueError(
            "government_purchase_growth_rate "
            "must be greater than -1."
        )

    initial_purchase_share = (
        params.initial_government_purchase_gdp_share
    )
    if not 0.0 <= initial_purchase_share < 1.0:
        raise ValueError(
            "initial_government_purchase_gdp_share must be "
            "between zero (inclusive) and one (exclusive)."
        )

    government.total_revenue = (
        government.taxes_households
        + government.taxes_firms
        + government.carbon_tax_revenue
    )

    government.basic_income_spending = sum(
        household.basic_income_income
        for household in households
    )

    government.transfer_spending = sum(
        household.transfer_income
        for household in households
    ) + government.carbon_dividend_spending

    government.public_wage_spending = sum(
        household.public_wage_income
        for household in households
    )

    mandatory_current_spending = (
        government.transfer_spending
        + government.public_wage_spending
    )

    # Calibrated once from the initial-period budget.
    if government.initial_public_purchase_budget is None:
        opening_household_consumption = sum(
            max(
                max(0.0, household.base_consumption_cost),
                params.propensity_to_consume_income
                * max(0.0, household.disposable_income),
            )
            for household in households
        )
        opening_private_investment = sum(
            max(0.0, firm.desired_brown_investment)
            + max(0.0, firm.desired_green_investment)
            for firm in (firms or [])
            if firm.active
        )
        opening_private_demand = (
            opening_household_consumption
            + opening_private_investment
        )
        expenditure_calibrated_budget = (
            initial_purchase_share
            / (1.0 - initial_purchase_share)
            * opening_private_demand
        )
        revenue_residual_budget = max(
            0.0,
            government.total_revenue - mandatory_current_spending,
        )
        government.initial_public_purchase_budget = (
            expenditure_calibrated_budget
            if firms is not None
            else revenue_residual_budget
        )

    structural_public_purchase_demand = (
        government.initial_public_purchase_budget
        * (
            1.0
            + purchase_growth_rate
        ) ** period
    )

    unemployment_reference = (
        params.government_unemployment_reference_rate
    )
    stabilizer = params.government_unemployment_stabilizer
    if not 0.0 <= unemployment_reference <= 1.0:
        raise ValueError(
            "government_unemployment_reference_rate must be between 0 and 1."
        )
    if stabilizer < 0.0:
        raise ValueError(
            "government_unemployment_stabilizer cannot be negative."
        )

    unemployment_rate = (
        sum(
            getattr(household, "employment_status", None)
            == EmploymentStatus.UNEMPLOYED
            for household in households
        )
        / len(households)
        if households else 0.0
    )
    unemployment_gap = max(
        0.0,
        unemployment_rate - unemployment_reference,
    )
    stabilizer_multiplier = (
        1.0 + stabilizer * unemployment_gap
        if period > 0 else 1.0
    )
    public_purchase_demand = (
        structural_public_purchase_demand
        * stabilizer_multiplier
    )

    government.capital_purchases = (
        capital_share
        * public_purchase_demand
    )

    government.current_purchases = (
        (1.0 - capital_share)
        * public_purchase_demand
    )
    
    government.planned_current_purchases = (
        government.current_purchases
    )

    government.planned_capital_purchases = (
        government.capital_purchases
    )

    # Before market settlement, realised purchases are
    # provisionally equal to planned purchases.
    government.realised_current_purchases = (
        government.current_purchases
    )

    government.realised_capital_purchases = (
        government.capital_purchases
    )

    government.unmet_current_purchases = 0.0
    government.unmet_capital_purchases = 0.0

    government.current_spending = (
        mandatory_current_spending
        + government.current_purchases
    )

    government.capital_spending = (
        government.capital_purchases
    )

    government.primary_deficit = (
        government.current_spending
        + government.capital_spending
        - government.total_revenue
    )

    # Interest payments and debt accumulation remain deferred.
    government.interest_payment = 0.0

    government.deficit = (
        government.primary_deficit
        + government.interest_payment
    )

    spending_identity_gap = (
        government.current_spending
        - government.transfer_spending
        - government.public_wage_spending
        - government.current_purchases
    )

    budget_identity_gap = (
        government.primary_deficit
        - (
            government.current_spending
            + government.capital_spending
            - government.total_revenue
        )
    )

    return {
        "total_revenue": government.total_revenue,

        "taxes_households": (
            government.taxes_households
        ),

        "taxes_firms": government.taxes_firms,

        "carbon_tax_revenue": (
            government.carbon_tax_revenue
        ),

        "transfer_spending": (
            government.transfer_spending
        ),
        
        "basic_income_spending": (
            government.basic_income_spending
        ),

        "public_wage_spending": (
            government.public_wage_spending
        ),

        "mandatory_current_spending": (
            mandatory_current_spending
        ),

        "initial_public_purchase_budget": (
            government.initial_public_purchase_budget
        ),

        "initial_government_purchase_gdp_share": (
            initial_purchase_share
        ),

        "government_purchase_growth_rate": (
            purchase_growth_rate
        ),
        "government_unemployment_rate": unemployment_rate,
        "government_unemployment_gap": unemployment_gap,
        "government_purchase_stabilizer_multiplier": (
            stabilizer_multiplier
        ),

        "current_purchases": (
            government.current_purchases
        ),

        "capital_purchases": (
            government.capital_purchases
        ),

        "public_purchase_demand": (
            public_purchase_demand
        ),

        "current_spending": (
            government.current_spending
        ),

        "capital_spending": (
            government.capital_spending
        ),

        "primary_deficit": (
            government.primary_deficit
        ),

        "deficit": government.deficit,

        "spending_identity_gap": (
            spending_identity_gap
        ),

        "budget_identity_gap": (
            budget_identity_gap
        ),
    }
