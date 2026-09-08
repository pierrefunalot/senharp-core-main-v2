"""Wages, transfers, and household gross income in SEN-HARP."""

from .entities import (
    EmploymentStatus,
    Firm,
    Household,
)
from .parameters import Parameters


PRIVATE_EMPLOYMENT_STATUSES = {
    EmploymentStatus.LOW_SKILLED_BROWN,
    EmploymentStatus.LOW_SKILLED_GREEN,
    EmploymentStatus.HIGH_SKILLED_BROWN,
    EmploymentStatus.HIGH_SKILLED_GREEN,
}


def status_income_multiplier(
    status: EmploymentStatus,
    params: Parameters,
) -> float:
    """Return gross income as a multiple of the base wage."""

    if status == EmploymentStatus.UNEMPLOYED:
        return (
            params.minimum_wage_ratio
            * params.unemployment_replacement_rate
        )

    if status == EmploymentStatus.LOW_SKILLED_BROWN:
        return 1.0

    if status == EmploymentStatus.LOW_SKILLED_GREEN:
        return (
            1.0
            + params.low_skill_green_wage_premium
        )

    if status == EmploymentStatus.JOB_GUARANTEE:
        return params.minimum_wage_ratio

    if status == EmploymentStatus.HIGH_SKILLED_BROWN:
        return (
            1.0
            + params.high_skill_wage_premium
        )

    if status == EmploymentStatus.HIGH_SKILLED_GREEN:
        # The two premia are treated additively.
        return (
            1.0
            + params.high_skill_wage_premium
            + params.high_skill_green_wage_premium
        )

    if status == EmploymentStatus.RESKILLING:
        return (
            params.minimum_wage_ratio
            * params.unemployment_replacement_rate
        )

    raise ValueError(
        f"Unknown employment status: {status}."
    )

def status_taxable_income_multiplier(
    status: EmploymentStatus,
    params: Parameters,
) -> float:
    """Return taxable income as a multiple of the base wage."""

    gross_multiplier = status_income_multiplier(
        status=status,
        params=params,
    )

    if params.tax_household_transfers:
        return gross_multiplier

    if status in {
        EmploymentStatus.LOW_SKILLED_BROWN,
        EmploymentStatus.LOW_SKILLED_GREEN,
        EmploymentStatus.JOB_GUARANTEE,
        EmploymentStatus.HIGH_SKILLED_BROWN,
        EmploymentStatus.HIGH_SKILLED_GREEN,
    }:
        return gross_multiplier

    return 0.0

def calibrate_initial_base_wage(
    households: list[Household],
    params: Parameters,
    reference_mean_income: float | None = None,
) -> float:
    """Calibrate the base wage to preserve mean net income.

    The calibration targets mean economic disposable income,
    after household income taxation.
    """

    if params.initial_base_wage is not None:
        if params.initial_base_wage <= 0.0:
            raise ValueError(
                "initial_base_wage must be positive."
            )

        return params.initial_base_wage

    if not households:
        raise ValueError(
            "At least one household is required."
        )

    if reference_mean_income is None:
        reference_mean_income = (
            sum(
                household.disposable_income
                for household in households
            )
            / len(households)
        )

    if reference_mean_income <= 0.0:
        raise ValueError(
            "reference_mean_income must be positive."
        )

    tax_rate = (
        params.household_income_tax_rate
    )

    if not 0.0 <= tax_rate <= 1.0:
        raise ValueError(
            "household_income_tax_rate must be "
            "between 0 and 1."
        )

    mean_net_income_multiplier = (
        sum(
            status_income_multiplier(
                status=household.employment_status,
                params=params,
            )
            - tax_rate
            * status_taxable_income_multiplier(
                status=household.employment_status,
                params=params,
            )
            for household in households
        )
        / len(households)
    )

    if mean_net_income_multiplier <= 0.0:
        raise ValueError(
            "Mean net income multiplier must be positive."
        )

    return (
        reference_mean_income
        / mean_net_income_multiplier
    )

def reset_income_flows(
    households: list[Household],
    firms: list[Firm],
) -> None:
    """Reset current-period household income and firm wage bills."""

    for household in households:
        household.private_wage_income = 0.0
        household.public_wage_income = 0.0
        household.transfer_income = 0.0
        household.gross_income = 0.0
        household.dividend_income = 0.0

    for firm in firms:
        firm.wage_bill = 0.0


def update_household_gross_incomes(
    households: list[Household],
    firms: list[Firm],
    base_wage: float,
    params: Parameters,
) -> dict[str, float]:
    """Compute household wages, transfers, and gross income."""

    if base_wage <= 0.0:
        raise ValueError(
            "base_wage must be strictly positive."
        )

    reset_income_flows(
        households=households,
        firms=firms,
    )

    firms_by_id = {
        firm.firm_id: firm
        for firm in firms
    }

    minimum_wage = (
        params.minimum_wage_ratio
        * base_wage
    )

    unemployment_benefit = (
        params.unemployment_replacement_rate
        * minimum_wage
    )

    for household in households:
        status = household.employment_status

        if status == EmploymentStatus.LOW_SKILLED_BROWN:
            household.private_wage_income = base_wage

        elif status == EmploymentStatus.LOW_SKILLED_GREEN:
            household.private_wage_income = (
                base_wage
                * (
                    1.0
                    + params.low_skill_green_wage_premium
                )
            )

        elif status == EmploymentStatus.HIGH_SKILLED_BROWN:
            household.private_wage_income = (
                base_wage
                * (
                    1.0
                    + params.high_skill_wage_premium
                )
            )

        elif status == EmploymentStatus.HIGH_SKILLED_GREEN:
            household.private_wage_income = (
                base_wage
                * (
                    1.0
                    + params.high_skill_wage_premium
                    + params.high_skill_green_wage_premium
                )
            )

        elif status == EmploymentStatus.JOB_GUARANTEE:
            household.public_wage_income = (
                minimum_wage
            )

        elif status in {
            EmploymentStatus.UNEMPLOYED,
            EmploymentStatus.RESKILLING,
        }:
            household.transfer_income = (
                unemployment_benefit
            )

        else:
            raise ValueError(
                f"Unknown employment status: {status}."
            )

        household.gross_income = (
            household.private_wage_income
            + household.public_wage_income
            + household.transfer_income
        )

        if status in PRIVATE_EMPLOYMENT_STATUSES:
            if household.employer_id not in firms_by_id:
                raise ValueError(
                    f"Household {household.household_id} "
                    f"is linked to unknown firm "
                    f"{household.employer_id}."
                )

            firms_by_id[
                household.employer_id
            ].wage_bill += (
                household.private_wage_income
            )

    total_private_wages = sum(
        household.private_wage_income
        for household in households
    )

    total_public_wages = sum(
        household.public_wage_income
        for household in households
    )

    total_transfers = sum(
        household.transfer_income
        for household in households
    )

    total_gross_income = sum(
        household.gross_income
        for household in households
    )

    return {
        "base_wage": base_wage,
        "minimum_wage": minimum_wage,
        "unemployment_benefit": (
            unemployment_benefit
        ),
        "total_private_wages": (
            total_private_wages
        ),
        "total_public_wages": (
            total_public_wages
        ),
        "total_transfers": total_transfers,
        "total_gross_income": (
            total_gross_income
        ),
    }


def distribute_firm_dividends(
    households: list[Household],
    firms: list[Firm],
) -> float:
    """Distribute last period's declared dividends equally."""

    total = sum(max(0.0, firm.dividends_paid) for firm in firms)
    if not households:
        return 0.0
    per_household = total / len(households)
    for household in households:
        household.dividend_income = per_household
        household.gross_income += per_household
    return total
