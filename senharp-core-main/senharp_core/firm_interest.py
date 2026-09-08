"""Interest payments on firm loans."""

from .entities import Firm


def update_firm_interest_payments(
    firms: list[Firm],
    period: int,
) -> dict[str, float]:
    """Compute interest paid on opening firm-loan stocks.

    Current-period interest is calculated using:

    - previous-period brown and green loan stocks;
    - previous-period brown and green loan rates.

    Newly granted loans do not bear interest until the
    following period.
    """

    total_opening_brown_debt = 0.0
    total_opening_green_debt = 0.0

    total_brown_interest = 0.0
    total_green_interest = 0.0
    total_interest = 0.0

    interest_accounting_gap = 0.0

    for firm in firms:
        firm.brown_interest_paid = 0.0
        firm.green_interest_paid = 0.0
        firm.interest_paid = 0.0

        if not firm.active:
            continue

        opening_brown_debt = max(
            0.0,
            firm.previous_brown_loans,
        )

        opening_green_debt = max(
            0.0,
            firm.previous_green_loans,
        )

        brown_interest_rate = max(
            0.0,
            firm.previous_brown_loan_interest_rate,
        )

        green_interest_rate = max(
            0.0,
            firm.previous_green_loan_interest_rate,
        )

        # Period 0 is the initial state. Normally opening debt
        # is zero, but the explicit rule avoids charging
        # historical interest in an uncalibrated initial state.
        if period == 0:
            brown_interest = 0.0
            green_interest = 0.0
        else:
            brown_interest = (
                opening_brown_debt
                * brown_interest_rate
            )

            green_interest = (
                opening_green_debt
                * green_interest_rate
            )

        firm.brown_interest_paid = max(
            0.0,
            brown_interest,
        )

        firm.green_interest_paid = max(
            0.0,
            green_interest,
        )

        firm.interest_paid = (
            firm.brown_interest_paid
            + firm.green_interest_paid
        )

        total_opening_brown_debt += (
            opening_brown_debt
        )

        total_opening_green_debt += (
            opening_green_debt
        )

        total_brown_interest += (
            firm.brown_interest_paid
        )

        total_green_interest += (
            firm.green_interest_paid
        )

        total_interest += (
            firm.interest_paid
        )

        interest_accounting_gap += (
            firm.interest_paid
            - firm.brown_interest_paid
            - firm.green_interest_paid
        )

    return {
        "opening_brown_firm_debt": (
            total_opening_brown_debt
        ),

        "opening_green_firm_debt": (
            total_opening_green_debt
        ),

        "opening_total_firm_debt": (
            total_opening_brown_debt
            + total_opening_green_debt
        ),

        "brown_interest_paid": (
            total_brown_interest
        ),

        "green_interest_paid": (
            total_green_interest
        ),

        "total_interest_paid": (
            total_interest
        ),

        "interest_accounting_gap": (
            interest_accounting_gap
        ),
    }