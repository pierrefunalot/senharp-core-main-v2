"""Household-bank relationships and consumer credit."""

import random

from .entities import Bank, Household
from .parameters import Parameters


def assign_households_to_banks(
    households: list[Household],
    banks: list[Bank],
    params: Parameters,
) -> dict[int, int]:
    """Assign households to banks using a balanced random allocation."""

    if not banks:
        raise ValueError(
            "At least one bank is required."
        )

    rng = random.Random(
        params.seed
        + params.household_bank_seed_offset
    )

    ordered_households = sorted(
        households,
        key=lambda household: household.household_id,
    )

    bank_ids = [
        bank.bank_id
        for bank in sorted(
            banks,
            key=lambda bank: bank.bank_id,
        )
    ]

    assignments = [
        bank_ids[index % len(bank_ids)]
        for index in range(len(ordered_households))
    ]

    rng.shuffle(assignments)

    for household, bank_id in zip(
        ordered_households,
        assignments,
    ):
        household.bank_id = bank_id

    return {
        bank_id: sum(
            household.bank_id == bank_id
            for household in households
        )
        for bank_id in bank_ids
    }


def reset_bank_consumer_credit_flows(
    banks: list[Bank],
) -> None:
    """Snapshot consumer-loan stocks and reset current flows."""

    for bank in banks:
        bank.previous_consumer_loans = (
            bank.consumer_loans
        )

        bank.new_consumer_loans = 0.0
        bank.consumer_loan_repayments = 0.0
        bank.consumer_loan_interest_income = 0.0


def update_household_bank_credit(
    households: list[Household],
    banks: list[Bank],
) -> dict[str, float]:
    """Record household borrowing as bank consumer-loan assets."""

    if not banks:
        raise ValueError(
            "At least one bank is required."
        )

    banks_by_id = {
        bank.bank_id: bank
        for bank in banks
    }

    reset_bank_consumer_credit_flows(
        banks=banks,
    )

    for household in households:
        if household.bank_id not in banks_by_id:
            raise ValueError(
                f"Household {household.household_id} "
                f"is linked to unknown bank "
                f"{household.bank_id}."
            )

        bank = banks_by_id[
            household.bank_id
        ]

        bank.new_consumer_loans += (
            household.new_household_debt
        )

        bank.consumer_loan_repayments += (
            household.household_debt_repayment
        )

        bank.consumer_loan_interest_income += (
            household.household_debt_interest
        )

    for bank in banks:
        bank.consumer_loans = max(
            0.0,
            bank.previous_consumer_loans
            + bank.new_consumer_loans
            - bank.consumer_loan_repayments,
        )

    total_new_household_debt = sum(
        household.new_household_debt
        for household in households
    )

    total_new_consumer_loans = sum(
        bank.new_consumer_loans
        for bank in banks
    )

    total_household_repayments = sum(
        household.household_debt_repayment
        for household in households
    )

    total_bank_repayments = sum(
        bank.consumer_loan_repayments
        for bank in banks
    )

    total_household_debt = sum(
        household.household_debt
        for household in households
    )

    total_bank_consumer_loans = sum(
        bank.consumer_loans
        for bank in banks
    )

    total_household_interest = sum(
        household.household_debt_interest
        for household in households
    )

    total_bank_interest_income = sum(
        bank.consumer_loan_interest_income
        for bank in banks
    )

    return {
        "total_new_household_debt": (
            total_new_household_debt
        ),
        "total_new_consumer_loans": (
            total_new_consumer_loans
        ),
        "total_household_repayments": (
            total_household_repayments
        ),
        "total_bank_consumer_loan_repayments": (
            total_bank_repayments
        ),
        "total_household_debt": (
            total_household_debt
        ),
        "total_bank_consumer_loans": (
            total_bank_consumer_loans
        ),
        "total_household_interest": (
            total_household_interest
        ),
        "total_bank_consumer_interest_income": (
            total_bank_interest_income
        ),
        "new_credit_accounting_gap": (
            total_new_household_debt
            - total_new_consumer_loans
        ),
        "repayment_accounting_gap": (
            total_household_repayments
            - total_bank_repayments
        ),
        "consumer_loan_stock_gap": (
            total_household_debt
            - total_bank_consumer_loans
        ),
        "consumer_interest_accounting_gap": (
            total_household_interest
            - total_bank_interest_income
        ),
    }