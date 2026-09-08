"""Household income taxation in SEN-HARP."""

from .entities import Household, PolicyState, Scenario
from .parameters import Parameters


def reset_household_tax_flows(
    households: list[Household],
) -> None:
    """Reset current-period household tax variables."""

    for household in households:
        household.taxable_income = 0.0
        household.income_tax_paid = 0.0
        household.progressive_income_tax_paid = 0.0
        household.economic_disposable_income = 0.0


def compute_household_taxable_income(
    household: Household,
    params: Parameters,
) -> float:
    """Compute the household income-tax base."""

    if params.tax_household_transfers:
        taxable_income = household.gross_income
    else:
        taxable_income = (
            household.private_wage_income
            + household.public_wage_income
        )

    return max(
        0.0,
        taxable_income,
    )


def update_household_income_tax(
    households: list[Household],
    params: Parameters,
    policy: PolicyState | None = None,
) -> dict[str, float]:
    """Compute household taxes and economic disposable income."""

    tax_rate = params.household_income_tax_rate

    if not 0.0 <= tax_rate <= 1.0:
        raise ValueError(
            "household_income_tax_rate must be "
            "between 0 and 1."
        )

    reset_household_tax_flows(
        households=households,
    )

    taxable_incomes = [
        compute_household_taxable_income(household, params)
        for household in households
    ]
    mean_taxable_income = (
        sum(taxable_incomes) / len(taxable_incomes)
        if taxable_incomes else 0.0
    )
    progressive_active = bool(
        policy is not None
        and policy.active
        and policy.scenario == Scenario.POST_GROWTH
    )
    progressive_rate = params.post_growth_progressive_tax_rate
    progressive_threshold = (
        params.post_growth_progressive_tax_threshold_mean
        * mean_taxable_income
    )
    if not 0.0 <= progressive_rate <= 1.0:
        raise ValueError(
            "post_growth_progressive_tax_rate must be between 0 and 1."
        )
    if params.post_growth_progressive_tax_threshold_mean < 0.0:
        raise ValueError(
            "post_growth_progressive_tax_threshold_mean cannot be negative."
        )

    for household, taxable_income in zip(households, taxable_incomes):
        household.taxable_income = taxable_income

        base_tax = tax_rate * household.taxable_income
        household.progressive_income_tax_paid = (
            progressive_rate
            * max(0.0, household.taxable_income - progressive_threshold)
            if progressive_active else 0.0
        )
        household.income_tax_paid = (
            base_tax + household.progressive_income_tax_paid
        )

        household.economic_disposable_income = max(
            0.0,
            household.gross_income
            - household.income_tax_paid,
        )

    total_taxable_income = sum(
        household.taxable_income
        for household in households
    )

    total_income_tax = sum(
        household.income_tax_paid
        for household in households
    )
    total_progressive_income_tax = sum(
        household.progressive_income_tax_paid
        for household in households
    )

    total_economic_disposable_income = sum(
        household.economic_disposable_income
        for household in households
    )

    number_households = len(
        households
    )

    if number_households > 0:
        mean_economic_disposable_income = (
            total_economic_disposable_income
            / number_households
        )
    else:
        mean_economic_disposable_income = 0.0

    accounting_gap = (
        sum(
            household.gross_income
            for household in households
        )
        - total_income_tax
        - total_economic_disposable_income
    )

    return {
        "household_income_tax_rate": tax_rate,
        "total_taxable_income": (
            total_taxable_income
        ),
        "total_household_income_tax": (
            total_income_tax
        ),
        "total_progressive_income_tax": total_progressive_income_tax,
        "total_economic_disposable_income": (
            total_economic_disposable_income
        ),
        "mean_economic_disposable_income": (
            mean_economic_disposable_income
        ),
        "household_income_accounting_gap": (
            accounting_gap
        ),
    }
