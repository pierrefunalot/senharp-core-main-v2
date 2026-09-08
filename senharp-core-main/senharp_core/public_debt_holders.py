"""Allocation of public debt among financial institutions."""

from .entities import (
    Bank,
    CentralBank,
    Government,
)
from .parameters import Parameters


def update_public_debt_holdings(
    government: Government,
    banks: list[Bank],
    central_bank: CentralBank,
    params: Parameters,
) -> dict[str, float]:
    """Allocate public debt and related interest income.

    Opening government-bond holdings must equal the opening
    public-debt stock.

    Closing public debt is allocated between:

    - the central bank, according to the parameter
      central_bank_public_debt_share;
    - commercial banks, according to their market shares.

    Government interest payments are distributed according to
    opening bond holdings.
    """

    central_bank_share = (
        params.central_bank_public_debt_share
    )

    if not 0.0 <= central_bank_share <= 1.0:
        raise ValueError(
            "central_bank_public_debt_share must be "
            "between zero and one."
        )

    if not banks:
        raise ValueError(
            "At least one commercial bank is required."
        )

    total_market_share = sum(
        max(
            0.0,
            bank.market_share,
        )
        for bank in banks
    )

    if total_market_share <= 0.0:
        raise ValueError(
            "Commercial-bank market shares must have "
            "a strictly positive sum."
        )

    opening_public_debt = max(
        0.0,
        government.previous_public_debt,
    )

    closing_public_debt = max(
        0.0,
        government.public_debt,
    )

    government_interest_payment = max(
        0.0,
        government.interest_payment,
    )

    # Preserve opening financial-asset stocks.
    for bank in banks:
        bank.previous_government_bonds = max(
            0.0,
            bank.government_bonds,
        )

        bank.government_bond_change = 0.0
        bank.government_bond_interest_income = 0.0

    central_bank.previous_government_bonds = max(
        0.0,
        central_bank.government_bonds,
    )

    central_bank.government_bond_change = 0.0
    central_bank.government_bond_interest_income = 0.0

    opening_commercial_bank_bonds = sum(
        bank.previous_government_bonds
        for bank in banks
    )

    opening_central_bank_bonds = (
        central_bank.previous_government_bonds
    )

    opening_total_bond_holdings = (
        opening_commercial_bank_bonds
        + opening_central_bank_bonds
    )

    opening_stock_gap = (
        opening_total_bond_holdings
        - opening_public_debt
    )

    if abs(opening_stock_gap) > 1e-8:
        raise ValueError(
            "Opening government-bond holdings do not "
            "match opening public debt: "
            f"{opening_stock_gap}."
        )

    # =========================================================
    # INTEREST INCOME ON OPENING HOLDINGS
    # =========================================================

    if opening_public_debt > 0.0:
        for bank in banks:
            bank.government_bond_interest_income = (
                government_interest_payment
                * bank.previous_government_bonds
                / opening_public_debt
            )

        central_bank.government_bond_interest_income = (
            government_interest_payment
            * central_bank.previous_government_bonds
            / opening_public_debt
        )

    elif government_interest_payment > 1e-8:
        raise ValueError(
            "Government cannot pay interest when opening "
            "public debt is zero."
        )

    # =========================================================
    # CLOSING BOND HOLDINGS
    # =========================================================

    closing_central_bank_bonds = (
        closing_public_debt
        * central_bank_share
    )

    closing_commercial_bank_bonds = (
        closing_public_debt
        - closing_central_bank_bonds
    )

    for bank in banks:
        normalised_market_share = (
            max(
                0.0,
                bank.market_share,
            )
            / total_market_share
        )

        target_bond_holdings = (
            closing_commercial_bank_bonds
            * normalised_market_share
        )

        bank.government_bonds = max(
            0.0,
            target_bond_holdings,
        )

        bank.government_bond_change = (
            bank.government_bonds
            - bank.previous_government_bonds
        )

    central_bank.government_bonds = max(
        0.0,
        closing_central_bank_bonds,
    )

    central_bank.government_bond_change = (
        central_bank.government_bonds
        - central_bank.previous_government_bonds
    )

    closing_commercial_holdings = sum(
        bank.government_bonds
        for bank in banks
    )

    closing_central_bank_holdings = (
        central_bank.government_bonds
    )

    closing_total_holdings = (
        closing_commercial_holdings
        + closing_central_bank_holdings
    )

    commercial_bank_bond_change = sum(
        bank.government_bond_change
        for bank in banks
    )

    central_bank_bond_change = (
        central_bank.government_bond_change
    )

    total_bond_change = (
        commercial_bank_bond_change
        + central_bank_bond_change
    )

    commercial_bank_interest_income = sum(
        bank.government_bond_interest_income
        for bank in banks
    )

    central_bank_interest_income = (
        central_bank.government_bond_interest_income
    )

    total_bond_interest_income = (
        commercial_bank_interest_income
        + central_bank_interest_income
    )

    return {
        "opening_public_debt": (
            opening_public_debt
        ),

        "opening_commercial_bank_bonds": (
            opening_commercial_bank_bonds
        ),

        "opening_central_bank_bonds": (
            opening_central_bank_bonds
        ),

        "opening_total_bond_holdings": (
            opening_total_bond_holdings
        ),

        "closing_public_debt": (
            closing_public_debt
        ),

        "closing_commercial_bank_bonds": (
            closing_commercial_holdings
        ),

        "closing_central_bank_bonds": (
            closing_central_bank_holdings
        ),

        "closing_total_bond_holdings": (
            closing_total_holdings
        ),

        "commercial_bank_bond_change": (
            commercial_bank_bond_change
        ),

        "central_bank_bond_change": (
            central_bank_bond_change
        ),

        "total_bond_change": (
            total_bond_change
        ),

        "government_interest_payment": (
            government_interest_payment
        ),

        "commercial_bank_interest_income": (
            commercial_bank_interest_income
        ),

        "central_bank_interest_income": (
            central_bank_interest_income
        ),

        "total_bond_interest_income": (
            total_bond_interest_income
        ),

        "opening_public_debt_holder_gap": (
            opening_total_bond_holdings
            - opening_public_debt
        ),

        "closing_public_debt_holder_gap": (
            closing_total_holdings
            - closing_public_debt
        ),

        "public_debt_change_holder_gap": (
            total_bond_change
            - government.public_debt_change
        ),

        "government_interest_holder_gap": (
            government_interest_payment
            - total_bond_interest_income
        ),
    }