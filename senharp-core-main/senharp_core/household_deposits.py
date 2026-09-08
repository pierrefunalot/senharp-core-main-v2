"""Bank liabilities corresponding to household savings."""

from .entities import Bank, Household


def update_bank_household_deposit_accounts(
    households: list[Household],
    banks: list[Bank],
    period: int,
) -> dict[str, float]:
    """Mirror household savings in commercial-bank deposits.

    Household savings are treated as deposits held at the
    household's assigned commercial bank.

    At period zero, opening bank deposits are initialised from
    household previous savings. From period one onward, the
    opening bank stock must equal the previous-period closing
    household deposits.
    """

    if not banks:
        raise ValueError(
            "At least one commercial bank is required."
        )

    banks_by_id = {
        bank.bank_id: bank
        for bank in banks
    }

    for household in households:
        if household.bank_id not in banks_by_id:
            raise ValueError(
                f"Household {household.household_id} is linked "
                f"to unknown bank {household.bank_id}."
            )

    total_opening_household_savings = sum(
        max(
            0.0,
            household.previous_savings,
        )
        for household in households
    )

    total_closing_household_savings = sum(
        max(
            0.0,
            household.savings,
        )
        for household in households
    )

    total_previous_bank_deposits = 0.0
    total_closing_bank_deposits = 0.0
    total_bank_deposit_change = 0.0

    total_initialisation_adjustment = 0.0
    maximum_opening_bank_gap = 0.0
    maximum_closing_bank_gap = 0.0

    for bank in banks:
        bank_households = [
            household
            for household in households
            if household.bank_id == bank.bank_id
        ]

        calculated_opening_deposits = sum(
            max(
                0.0,
                household.previous_savings,
            )
            for household in bank_households
        )

        observed_opening_deposits = max(
            0.0,
            bank.household_deposits,
        )

        opening_bank_gap = (
            observed_opening_deposits
            - calculated_opening_deposits
        )

        maximum_opening_bank_gap = max(
            maximum_opening_bank_gap,
            abs(opening_bank_gap),
        )

        if period > 0 and abs(
            opening_bank_gap
        ) > 1e-8:
            raise ValueError(
                "Opening household-deposit mismatch for "
                f"bank {bank.bank_id}: {opening_bank_gap}."
            )

        if period == 0:
            total_initialisation_adjustment += (
                calculated_opening_deposits
                - observed_opening_deposits
            )

        bank.previous_household_deposits = (
            calculated_opening_deposits
        )

        calculated_closing_deposits = sum(
            max(
                0.0,
                household.savings,
            )
            for household in bank_households
        )

        bank.household_deposits = (
            calculated_closing_deposits
        )

        bank.household_deposit_change = (
            bank.household_deposits
            - bank.previous_household_deposits
        )

        closing_household_savings = sum(
            max(
                0.0,
                household.savings,
            )
            for household in bank_households
        )

        closing_bank_gap = (
            bank.household_deposits
            - closing_household_savings
        )

        maximum_closing_bank_gap = max(
            maximum_closing_bank_gap,
            abs(closing_bank_gap),
        )

        total_previous_bank_deposits += (
            bank.previous_household_deposits
        )

        total_closing_bank_deposits += (
            bank.household_deposits
        )

        total_bank_deposit_change += (
            bank.household_deposit_change
        )

    return {
        "opening_household_savings": (
            total_opening_household_savings
        ),

        "opening_bank_household_deposits": (
            total_previous_bank_deposits
        ),

        "closing_household_savings": (
            total_closing_household_savings
        ),

        "closing_bank_household_deposits": (
            total_closing_bank_deposits
        ),

        "household_deposit_change": (
            total_bank_deposit_change
        ),

        "period_zero_initialisation_adjustment": (
            total_initialisation_adjustment
        ),

        "opening_household_deposit_gap": (
            total_previous_bank_deposits
            - total_opening_household_savings
        ),

        "closing_household_deposit_gap": (
            total_closing_bank_deposits
            - total_closing_household_savings
        ),

        "household_deposit_flow_gap": (
            total_previous_bank_deposits
            + total_bank_deposit_change
            - total_closing_bank_deposits
        ),

        "maximum_opening_bank_gap": (
            maximum_opening_bank_gap
        ),

        "maximum_closing_bank_gap": (
            maximum_closing_bank_gap
        ),
    }