"""Initialization of SEN-HARP economic agents.

This module creates firms, banks, the central bank, and the government without running economic dynamics.
"""

import random
from collections import defaultdict

from .entities import (
    Bank,
    CentralBank,
    Firm,
    Government,
    Sector,
)
from .parameters import Parameters


# Initial productive capital by sector.
# These values reproduce the calibration used in the original SEN-HARP source code.
INITIAL_SECTOR_CAPITAL = {
    Sector.AGRICULTURE: 1785.78087,
    Sector.ENERGY: 2483.52562,
    Sector.HOUSING: 1616.43662,
    Sector.TRANSPORT: 4509.23822,
    Sector.INDUSTRY: 6911.55628,
    Sector.TECHNOLOGY: 2457.81971,
}


def initialize_factual_firm_loans(
    firms: list[Firm],
    banks: list[Bank],
    params: Parameters,
) -> None:
    """Apply the factual opening green/brown loan calibration."""

    green_share = params.initial_green_loan_portfolio_share
    if not 0.0 < green_share <= 1.0:
        raise ValueError(
            "initial_green_loan_portfolio_share must be in (0, 1]."
        )

    green_by_sector = {
        Sector.AGRICULTURE: params.initial_green_loans_agriculture,
        Sector.ENERGY: params.initial_green_loans_energy,
        Sector.HOUSING: params.initial_green_loans_housing,
        Sector.TRANSPORT: params.initial_green_loans_transport,
        Sector.INDUSTRY: params.initial_green_loans_industry,
        Sector.TECHNOLOGY: params.initial_green_loans_technology,
    }

    for sector, amount in green_by_sector.items():
        if amount < 0.0:
            raise ValueError("Opening green loans cannot be negative.")
        sector_firms = [firm for firm in firms if firm.sector == sector]
        if sector_firms:
            per_firm = amount / len(sector_firms)
            for firm in sector_firms:
                firm.green_loans = per_firm

    total_green = sum(green_by_sector.values())
    balance_sheet_scale = params.initial_private_capital_scale
    if balance_sheet_scale <= 0.0:
        raise ValueError("initial_private_capital_scale must be positive.")

    for firm in firms:
        firm.green_loans *= balance_sheet_scale

    total_green *= balance_sheet_scale
    total_brown = total_green * (1.0 - green_share) / green_share
    total_brown_capital = sum(max(0.0, firm.brown_capital) for firm in firms)

    for firm in firms:
        weight = (
            max(0.0, firm.brown_capital) / total_brown_capital
            if total_brown_capital > 0.0 else 0.0
        )
        firm.brown_loans = total_brown * weight

    banks_by_id = {bank.bank_id: bank for bank in banks}
    for bank in banks:
        bank.green_loans = 0.0
        bank.brown_loans = 0.0
    for firm in firms:
        bank = banks_by_id[firm.bank_id]
        bank.green_loans += firm.green_loans
        bank.brown_loans += firm.brown_loans


def create_banks(
    params: Parameters,
    rng: random.Random,
) -> list[Bank]:
    """Create commercial banks with heterogeneous target leverage."""

    if params.n_banks <= 0:
        raise ValueError(
            "n_banks must be strictly positive."
        )

    equal_market_share = 1.0 / params.n_banks

    banks: list[Bank] = []

    for bank_id in range(params.n_banks):
        target_leverage = (
            2.0
            * (
                1.0
                + rng.uniform(-0.10, 0.10)
            )
        )

        banks.append(
            Bank(
                bank_id=bank_id,
                target_leverage=target_leverage,
                animal_spirits=1.0,
                risk_appetite=0.82,
                market_share=equal_market_share,
            )
        )

    return banks


def create_firms(
    params: Parameters,
    rng: random.Random,
) -> list[Firm]:
    """Create firms and allocate sectoral capital.

    Firms are assigned to sectors in a round-robin sequence.
    Capital is heterogeneous across firms but sectoral totals are preserved exactly.
    """

    if params.n_firms <= 0:
        raise ValueError(
            "n_firms must be strictly positive."
        )

    if params.n_banks <= 0:
        raise ValueError(
            "n_banks must be strictly positive."
        )

    green_share = (
        params.initial_green_capital_share
    )

    if not 0.0 <= green_share <= 1.0:
        raise ValueError(
            "initial_green_capital_share "
            "must be between 0 and 1."
        )

    sectors = list(Sector)

    firms: list[Firm] = []

    # First create firms without productive capital.
    for firm_id in range(params.n_firms):
        sector = sectors[
            firm_id % len(sectors)
        ]

        bank_id = rng.randrange(
            params.n_banks
        )

        firms.append(
            Firm(
                firm_id=firm_id,
                sector=sector,
                bank_id=bank_id,
                productivity_factor=(
                    rng.uniform(0.0, 0.30)
                ),
                animal_spirits_brown=(
                    rng.uniform(
                        params.min_firm_animal_spirits,
                        params.max_firm_animal_spirits,
                    )
                ),
                animal_spirits_green=(
                    rng.uniform(
                        params.min_firm_animal_spirits,
                        params.max_firm_animal_spirits,
                    )
                ),
            )
        )

    firms_by_sector: dict[
        Sector,
        list[Firm],
    ] = defaultdict(list)

    for firm in firms:
        firms_by_sector[
            firm.sector
        ].append(firm)

    # Allocate each sector's capital using positive
    # heterogeneous weights normalized to one.
    for sector, sector_total_capital in (
        INITIAL_SECTOR_CAPITAL.items()
    ):
        sector_firms = firms_by_sector[
            sector
        ]

        if not sector_firms:
            continue

        raw_weights = [
            rng.random()
            for _ in sector_firms
        ]

        weights_sum = sum(raw_weights)

        if weights_sum <= 0.0:
            normalized_weights = [
                1.0 / len(sector_firms)
                for _ in sector_firms
            ]
        else:
            normalized_weights = [
                weight / weights_sum
                for weight in raw_weights
            ]

        total_green_capital = (
            sector_total_capital
            * params.initial_private_capital_scale
            * green_share
        )

        total_brown_capital = (
            sector_total_capital
            * params.initial_private_capital_scale
            * (1.0 - green_share)
        )

        for firm, weight in zip(
            sector_firms,
            normalized_weights,
        ):
            firm.green_capital = (
                weight
                * total_green_capital
            )

            firm.brown_capital = (
                weight
                * total_brown_capital
            )

    return firms


def initialize_economy(
    params: Parameters,
) -> tuple[
    list[Firm],
    list[Bank],
    CentralBank,
    Government,
]:
    """Create all economic institutions.

    Separate random streams prevent economic initialization from altering household and voting draws.
    """

    firm_rng = random.Random(
        params.seed
        + params.firm_seed_offset
    )

    bank_rng = random.Random(
        params.seed
        + params.bank_seed_offset
    )

    skill_mix_rng = random.Random(
        params.seed
        + params.skill_mix_seed_offset
    )

    firms = create_firms(
        params=params,
        rng=firm_rng,
    )

    if (
        params.min_high_skill_job_share
        > params.max_high_skill_job_share
    ):
        raise ValueError(
            "min_high_skill_job_share cannot exceed "
            "max_high_skill_job_share."
        )

    if not (
        0.0
        <= params.min_high_skill_job_share
        <= 1.0
    ):
        raise ValueError(
            "min_high_skill_job_share must be "
            "between 0 and 1."
        )

    if not (
        0.0
        <= params.max_high_skill_job_share
        <= 1.0
    ):
        raise ValueError(
            "max_high_skill_job_share must be "
            "between 0 and 1."
        )

    for firm in firms:
        firm.high_skill_job_share = (
            skill_mix_rng.uniform(
                params.min_high_skill_job_share,
                params.max_high_skill_job_share,
            )
        )

    banks = create_banks(
        params=params,
        rng=bank_rng,
    )

    initialize_factual_firm_loans(
        firms=firms,
        banks=banks,
        params=params,
    )

    central_bank = CentralBank()
    government = Government()

    return (
        firms,
        banks,
        central_bank,
        government,
    )
