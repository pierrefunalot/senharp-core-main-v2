"""Interest payments and accumulation of public debt."""

from .entities import Government


def prepare_government_debt_service(
    government: Government,
    period: int,
) -> dict[str, float]:
    """Compute interest on the opening public-debt stock.

    Interest paid in period t is based on the debt stock
    inherited from period t-1.

    Period 0 represents the initial state and does not generate
    an historical interest payment.
    """

    if government.government_interest_rate < 0.0:
        raise ValueError(
            "government_interest_rate cannot be negative."
        )

    government.previous_public_debt = max(
        0.0,
        government.public_debt,
    )

    if period == 0:
        government.interest_payment = 0.0
    else:
        government.interest_payment = (
            government.previous_public_debt
            * government.government_interest_rate
        )

    government.public_debt_change = 0.0

    government.excess_surplus_after_debt_repayment = (
        0.0
    )

    expected_interest = (
        0.0
        if period == 0
        else (
            government.previous_public_debt
            * government.government_interest_rate
        )
    )

    return {
        "opening_public_debt": (
            government.previous_public_debt
        ),

        "government_interest_rate": (
            government.government_interest_rate
        ),

        "interest_payment": (
            government.interest_payment
        ),

        "interest_accounting_gap": (
            government.interest_payment
            - expected_interest
        ),
    }


def close_government_debt_account(
    government: Government,
) -> dict[str, float]:
    """Update the end-of-period public-debt stock.

    A positive deficit increases public debt. A surplus first
    reduces outstanding public debt.

    If the surplus exceeds opening debt, the residual is
    recorded separately rather than allowing negative debt.
    """

    opening_public_debt = max(
        0.0,
        government.previous_public_debt,
    )

    primary_deficit = (
        government.primary_deficit
    )

    interest_payment = max(
        0.0,
        government.interest_payment,
    )

    total_deficit = (
        primary_deficit
        + interest_payment
    )

    # Reaffirm the total-deficit identity after settlement.
    government.deficit = (
        total_deficit
    )

    raw_closing_public_debt = (
        opening_public_debt
        + total_deficit
    )

    government.excess_surplus_after_debt_repayment = (
        max(
            0.0,
            -raw_closing_public_debt,
        )
    )

    government.public_debt = max(
        0.0,
        raw_closing_public_debt,
    )

    government.public_debt_change = (
        government.public_debt
        - opening_public_debt
    )

    return {
        "opening_public_debt": (
            opening_public_debt
        ),

        "primary_deficit": (
            primary_deficit
        ),

        "interest_payment": (
            interest_payment
        ),

        "total_deficit": (
            total_deficit
        ),

        "closing_public_debt": (
            government.public_debt
        ),

        "public_debt_change": (
            government.public_debt_change
        ),

        "excess_surplus_after_debt_repayment": (
            government
            .excess_surplus_after_debt_repayment
        ),

        "deficit_accounting_gap": (
            total_deficit
            - primary_deficit
            - interest_payment
        ),

        "public_debt_stock_flow_gap": (
            opening_public_debt
            + total_deficit
            + government
            .excess_surplus_after_debt_repayment
            - government.public_debt
        ),

        "public_debt_change_gap": (
            government.public_debt_change
            - total_deficit
            - government
            .excess_surplus_after_debt_repayment
        ),
    }