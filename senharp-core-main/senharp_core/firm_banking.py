"""Bank accounting for loans granted to firms."""

from .entities import Bank, Firm


def update_bank_firm_loan_accounts(
    firms: list[Firm],
    banks: list[Bank],
) -> dict[str, float]:
    """Update bank assets corresponding to firm loan liabilities.

    This function must be called after firm capital and debt
    accumulation because firm closing loan stocks and principal
    repayments must already be known.
    """

    banks_by_id = {
        bank.bank_id: bank
        for bank in banks
    }

    for firm in firms:
        if firm.bank_id not in banks_by_id:
            raise ValueError(
                f"Firm {firm.firm_id} is linked to "
                f"unknown bank {firm.bank_id}."
            )

    total_previous_brown_bank_loans = 0.0
    total_previous_green_bank_loans = 0.0

    total_new_brown_bank_loans = 0.0
    total_new_green_bank_loans = 0.0

    total_brown_bank_repayments = 0.0
    total_green_bank_repayments = 0.0

    total_closing_brown_bank_loans = 0.0
    total_closing_green_bank_loans = 0.0

    total_firm_interest_income = 0.0

    maximum_brown_bank_gap = 0.0
    maximum_green_bank_gap = 0.0

    for bank in banks:
        bank_firms = [
            firm
            for firm in firms
            if firm.bank_id == bank.bank_id
        ]

        bank.previous_brown_loans = max(
            0.0,
            bank.brown_loans,
        )

        bank.previous_green_loans = max(
            0.0,
            bank.green_loans,
        )

        bank.new_brown_loans = sum(
            max(
                0.0,
                firm.brown_loans_granted,
            )
            for firm in bank_firms
        )

        bank.new_green_loans = sum(
            max(
                0.0,
                firm.green_loans_granted,
            )
            for firm in bank_firms
        )

        bank.brown_loan_repayments = sum(
            max(
                0.0,
                firm.brown_loan_repayment,
            )
            for firm in bank_firms
        )

        bank.green_loan_repayments = sum(
            max(
                0.0,
                firm.green_loan_repayment,
            )
            for firm in bank_firms
        )

        bank.firm_loan_interest_income = sum(
            max(
                0.0,
                firm.interest_paid,
            )
            for firm in bank_firms
        )

        expected_closing_brown_loans = max(
            0.0,
            bank.previous_brown_loans
            + bank.new_brown_loans
            - bank.brown_loan_repayments,
        )

        expected_closing_green_loans = max(
            0.0,
            bank.previous_green_loans
            + bank.new_green_loans
            - bank.green_loan_repayments,
        )

        closing_brown_firm_debt = sum(
            max(
                0.0,
                firm.brown_loans,
            )
            for firm in bank_firms
        )

        closing_green_firm_debt = sum(
            max(
                0.0,
                firm.green_loans,
            )
            for firm in bank_firms
        )

        brown_bank_gap = (
            expected_closing_brown_loans
            - closing_brown_firm_debt
        )

        green_bank_gap = (
            expected_closing_green_loans
            - closing_green_firm_debt
        )

        maximum_brown_bank_gap = max(
            maximum_brown_bank_gap,
            abs(
                brown_bank_gap
            ),
        )

        maximum_green_bank_gap = max(
            maximum_green_bank_gap,
            abs(
                green_bank_gap
            ),
        )

        if abs(
            brown_bank_gap
        ) > 1e-8:
            raise ValueError(
                "Brown-loan accounting mismatch for "
                f"bank {bank.bank_id}: "
                f"{brown_bank_gap}."
            )

        if abs(
            green_bank_gap
        ) > 1e-8:
            raise ValueError(
                "Green-loan accounting mismatch for "
                f"bank {bank.bank_id}: "
                f"{green_bank_gap}."
            )

        # Bank assets are set equal to the corresponding
        # closing liabilities recorded by borrowing firms.
        bank.brown_loans = (
            closing_brown_firm_debt
        )

        bank.green_loans = (
            closing_green_firm_debt
        )

        total_previous_brown_bank_loans += (
            bank.previous_brown_loans
        )

        total_previous_green_bank_loans += (
            bank.previous_green_loans
        )

        total_new_brown_bank_loans += (
            bank.new_brown_loans
        )

        total_new_green_bank_loans += (
            bank.new_green_loans
        )

        total_brown_bank_repayments += (
            bank.brown_loan_repayments
        )

        total_green_bank_repayments += (
            bank.green_loan_repayments
        )

        total_closing_brown_bank_loans += (
            bank.brown_loans
        )

        total_closing_green_bank_loans += (
            bank.green_loans
        )

        total_firm_interest_income += (
            bank.firm_loan_interest_income
        )

    total_closing_brown_firm_debt = sum(
        max(
            0.0,
            firm.brown_loans,
        )
        for firm in firms
    )

    total_closing_green_firm_debt = sum(
        max(
            0.0,
            firm.green_loans,
        )
        for firm in firms
    )

    total_previous_bank_loans = (
        total_previous_brown_bank_loans
        + total_previous_green_bank_loans
    )

    total_new_bank_loans = (
        total_new_brown_bank_loans
        + total_new_green_bank_loans
    )

    total_bank_repayments = (
        total_brown_bank_repayments
        + total_green_bank_repayments
    )

    total_closing_bank_loans = (
        total_closing_brown_bank_loans
        + total_closing_green_bank_loans
    )

    total_closing_firm_debt = (
        total_closing_brown_firm_debt
        + total_closing_green_firm_debt
    )

    return {
        "previous_brown_bank_loans": (
            total_previous_brown_bank_loans
        ),

        "new_brown_bank_loans": (
            total_new_brown_bank_loans
        ),

        "brown_bank_loan_repayments": (
            total_brown_bank_repayments
        ),

        "closing_brown_bank_loans": (
            total_closing_brown_bank_loans
        ),

        "closing_brown_firm_debt": (
            total_closing_brown_firm_debt
        ),

        "previous_green_bank_loans": (
            total_previous_green_bank_loans
        ),

        "new_green_bank_loans": (
            total_new_green_bank_loans
        ),

        "green_bank_loan_repayments": (
            total_green_bank_repayments
        ),

        "closing_green_bank_loans": (
            total_closing_green_bank_loans
        ),

        "closing_green_firm_debt": (
            total_closing_green_firm_debt
        ),

        "total_previous_bank_loans": (
            total_previous_bank_loans
        ),

        "total_new_bank_loans": (
            total_new_bank_loans
        ),

        "total_bank_loan_repayments": (
            total_bank_repayments
        ),

        "total_closing_bank_loans": (
            total_closing_bank_loans
        ),

        "total_closing_firm_debt": (
            total_closing_firm_debt
        ),

        "total_firm_interest_income": (
            total_firm_interest_income
        ),

        "brown_bank_firm_stock_gap": (
            total_closing_brown_bank_loans
            - total_closing_brown_firm_debt
        ),

        "green_bank_firm_stock_gap": (
            total_closing_green_bank_loans
            - total_closing_green_firm_debt
        ),

        "total_bank_firm_stock_gap": (
            total_closing_bank_loans
            - total_closing_firm_debt
        ),

        "brown_bank_flow_gap": (
            total_previous_brown_bank_loans
            + total_new_brown_bank_loans
            - total_brown_bank_repayments
            - total_closing_brown_bank_loans
        ),

        "green_bank_flow_gap": (
            total_previous_green_bank_loans
            + total_new_green_bank_loans
            - total_green_bank_repayments
            - total_closing_green_bank_loans
        ),

        "total_bank_flow_gap": (
            total_previous_bank_loans
            + total_new_bank_loans
            - total_bank_repayments
            - total_closing_bank_loans
        ),

        "maximum_brown_bank_gap": (
            maximum_brown_bank_gap
        ),

        "maximum_green_bank_gap": (
            maximum_green_bank_gap
        ),
    }