"""Universal basic income for the post-growth package."""

from .entities import (
    EmploymentStatus,
    Household,
    PolicyState,
    Scenario,
)
from .parameters import Parameters


def apply_post_growth_basic_income(
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
    minimum_wage: float,
) -> dict[str, float | int]:
    """Add a universal basic income to household gross income.

    The transfer is paid only when the post-growth package is
    active. It is added before household income taxation.

    Consequently, its net effect on economic disposable income
    depends on whether transfers are included in the tax base.
    """

    ratio = params.post_growth_basic_income_ratio

    if not 0.0 <= ratio <= 1.0:
        raise ValueError(
            "post_growth_basic_income_ratio must be "
            "between zero and one."
        )

    if minimum_wage < 0.0:
        raise ValueError(
            "minimum_wage cannot be negative."
        )

    post_growth_active = (
        policy.active
        and policy.scenario == Scenario.POST_GROWTH
    )

    unit_basic_income = (
        ratio * minimum_wage
        if post_growth_active
        else 0.0
    )

    for household in households:
        # Reset the current-period flow before applying it.
        household.basic_income_income = 0.0
        household.unemployment_benefit_offset_by_basic_income = 0.0

        if not post_growth_active:
            continue

        if (
            params.post_growth_basic_income_offsets_unemployment_benefit
            and getattr(household, "employment_status", None)
            in {EmploymentStatus.UNEMPLOYED, EmploymentStatus.RESKILLING}
        ):
            offset = min(
                max(0.0, household.transfer_income),
                unit_basic_income,
            )
            household.transfer_income -= offset
            household.gross_income -= offset
            household.unemployment_benefit_offset_by_basic_income = offset

        household.basic_income_income = unit_basic_income

        # Basic income is an explicit transfer included in
        # gross household income before income taxation.
        household.transfer_income += (
            unit_basic_income
        )

        household.gross_income += (
            unit_basic_income
        )

    total_basic_income = sum(
        household.basic_income_income
        for household in households
    )
    total_unemployment_benefit_offset = sum(
        household.unemployment_benefit_offset_by_basic_income
        for household in households
    )

    expected_total_basic_income = (
        len(households)
        * unit_basic_income
    )

    return {
        "post_growth_basic_income_active": int(
            post_growth_active
        ),
        "basic_income_ratio": ratio,
        "unit_basic_income": unit_basic_income,
        "number_basic_income_recipients": (
            len(households)
            if post_growth_active
            else 0
        ),
        "total_basic_income": total_basic_income,
        "total_unemployment_benefit_offset": (
            total_unemployment_benefit_offset
        ),
        "basic_income_accounting_gap": (
            total_basic_income
            - expected_total_basic_income
        ),
    }
