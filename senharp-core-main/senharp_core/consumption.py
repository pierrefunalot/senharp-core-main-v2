"""Household consumption, savings, and essential borrowing."""

from .entities import Household
from .parameters import Parameters


def reset_household_consumption_flows(
    households: list[Household],
    snapshot_opening_stocks: bool = True,
) -> None:
    """Snapshot stocks and reset current-period flows."""

    for household in households:
        if snapshot_opening_stocks:
            household.previous_savings = (
                household.savings
            )

            household.previous_household_debt = (
                household.household_debt
            )

        household.desired_consumption = 0.0
        household.essential_consumption = 0.0
        household.supplementary_consumption = 0.0
        household.total_consumption = 0.0

        household.new_household_debt = 0.0
        household.household_debt_repayment = 0.0
        household.household_debt_interest = 0.0


def update_household_consumption(
    households: list[Household],
    params: Parameters,
    snapshot_opening_stocks: bool = True,
) -> dict[str, float]:
    """Compute consumption, savings, and essential borrowing."""

    income_propensity = params.propensity_to_consume_income

    savings_propensity = (
        params.propensity_to_consume_savings
    )

    if not 0.0 <= income_propensity <= 1.0:
        raise ValueError(
            "propensity_to_consume_income must be "
            "between 0 and 1."
        )

    if not 0.0 <= savings_propensity <= 1.0:
        raise ValueError(
            "propensity_to_consume_savings must be "
            "between 0 and 1."
        )

    reset_household_consumption_flows(
        households=households,
        snapshot_opening_stocks=snapshot_opening_stocks,
    )

    for household in households:
        disposable_income = (
            household.economic_disposable_income
        )

        replaced_essential_consumption = min(
            max(0.0, household.base_consumption_cost),
            max(0.0, household.planned_basic_services_received),
        )

        essential_cost = max(
            0.0,
            household.base_consumption_cost
            - replaced_essential_consumption,
        )

        available_resources = (
            disposable_income
            + household.previous_savings
        )

        unconstrained_desired_consumption = (
            income_propensity
            * disposable_income
            + savings_propensity
            * household.previous_savings
            - params.post_growth_basic_services_no_respend_rate
            * replaced_essential_consumption
        )

        household.desired_consumption = max(
            essential_cost,
            unconstrained_desired_consumption,
        )

        if (
            available_resources
            >= household.desired_consumption
        ):
            household.total_consumption = (
                household.desired_consumption
            )

        elif available_resources >= essential_cost:
            household.total_consumption = (
                available_resources
            )

        elif params.allow_essential_consumption_credit:
            household.total_consumption = (
                essential_cost
            )

            household.new_household_debt = (
                essential_cost
                - available_resources
            )

        else:
            household.total_consumption = max(
                0.0,
                available_resources,
            )

        household.essential_consumption = min(
            essential_cost,
            household.total_consumption,
        )

        household.supplementary_consumption = max(
            0.0,
            household.total_consumption
            - household.essential_consumption,
        )

        household.household_debt_repayment = (
            params.household_debt_repayment_rate
            * household.previous_household_debt
        )

        household.household_debt = max(
            0.0,
            household.previous_household_debt
            + household.new_household_debt
            - household.household_debt_repayment,
        )

        household.savings = max(
            0.0,
            household.previous_savings
            + disposable_income
            + household.new_household_debt
            - household.total_consumption
            - household.household_debt_repayment,
        )

    total_essential_consumption = sum(
        household.essential_consumption
        for household in households
    )

    total_supplementary_consumption = sum(
        household.supplementary_consumption
        for household in households
    )

    total_consumption = sum(
        household.total_consumption
        for household in households
    )

    total_new_household_debt = sum(
        household.new_household_debt
        for household in households
    )

    total_household_debt = sum(
        household.household_debt
        for household in households
    )

    total_savings = sum(
        household.savings
        for household in households
    )

    borrowers = sum(
        household.new_household_debt > 0.0
        for household in households
    )

    accounting_gap = sum(
        household.previous_savings
        + household.economic_disposable_income
        + household.new_household_debt
        - household.total_consumption
        - household.household_debt_repayment
        - household.savings
        for household in households
    )

    return {
        "total_essential_consumption": (
            total_essential_consumption
        ),
        "total_supplementary_consumption": (
            total_supplementary_consumption
        ),
        "total_consumption": total_consumption,
        "total_new_household_debt": (
            total_new_household_debt
        ),
        "total_household_debt": (
            total_household_debt
        ),
        "total_household_savings": (
            total_savings
        ),
        "household_borrowers": borrowers,
        "household_consumption_accounting_gap": (
            accounting_gap
        ),
    }
