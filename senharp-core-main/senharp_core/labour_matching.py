"""Household skill initialization and labour matching."""

import random

from .entities import (
    EmploymentStatus,
    Firm,
    Household,
    SkillLevel,
)
from .parameters import Parameters


def initialize_household_skills(
    households: list[Household],
    params: Parameters,
    rng: random.Random,
) -> None:
    """Assign initial skill levels to households."""

    high_skill_share = (
        params.initial_high_skill_household_share
    )

    if not 0.0 <= high_skill_share <= 1.0:
        raise ValueError(
            "initial_high_skill_household_share "
            "must be between 0 and 1."
        )

    number_high_skill = round(
        len(households)
        * high_skill_share
    )

    household_positions = list(
        range(len(households))
    )

    rng.shuffle(household_positions)

    high_skill_positions = set(
        household_positions[
            :number_high_skill
        ]
    )

    for position, household in enumerate(
        households
    ):
        household.skill_level = (
            SkillLevel.HIGH_SKILL
            if position in high_skill_positions
            else SkillLevel.LOW_SKILL
        )

        household.employment_status = (
            EmploymentStatus.UNEMPLOYED
        )

        household.employer_id = -1
        household.reskilling_counter = 0


def reset_firm_employment(
    firms: list[Firm],
) -> None:
    """Reset jobs effectively filled in each firm."""

    for firm in firms:
        firm.brown_low_skill_employment = 0
        firm.green_low_skill_employment = 0
        firm.brown_high_skill_employment = 0
        firm.green_high_skill_employment = 0


def build_job_slots(
    firms: list[Firm],
    skill_level: SkillLevel,
) -> list[tuple[Firm, EmploymentStatus]]:
    """Create job slots for one skill level."""

    slots: list[
        tuple[Firm, EmploymentStatus]
    ] = []

    for firm in sorted(
        firms,
        key=lambda item: item.firm_id,
    ):
        if not firm.active:
            continue

        if skill_level == SkillLevel.LOW_SKILL:
            slots.extend(
                [
                    (
                        firm,
                        EmploymentStatus.LOW_SKILLED_BROWN,
                    )
                ]
                * firm.brown_low_skill_demand
            )

            slots.extend(
                [
                    (
                        firm,
                        EmploymentStatus.LOW_SKILLED_GREEN,
                    )
                ]
                * firm.green_low_skill_demand
            )

        else:
            slots.extend(
                [
                    (
                        firm,
                        EmploymentStatus.HIGH_SKILLED_BROWN,
                    )
                ]
                * firm.brown_high_skill_demand
            )

            slots.extend(
                [
                    (
                        firm,
                        EmploymentStatus.HIGH_SKILLED_GREEN,
                    )
                ]
                * firm.green_high_skill_demand
            )

    return slots


def register_firm_employment(
    firm: Firm,
    status: EmploymentStatus,
) -> None:
    """Increase employment for the corresponding job type."""

    if status == EmploymentStatus.LOW_SKILLED_BROWN:
        firm.brown_low_skill_employment += 1

    elif status == EmploymentStatus.LOW_SKILLED_GREEN:
        firm.green_low_skill_employment += 1

    elif status == EmploymentStatus.HIGH_SKILLED_BROWN:
        firm.brown_high_skill_employment += 1

    elif status == EmploymentStatus.HIGH_SKILLED_GREEN:
        firm.green_high_skill_employment += 1

    else:
        raise ValueError(
            f"Status {status} is not a private-sector job."
        )


def match_one_skill_group(
    households: list[Household],
    firms: list[Firm],
    skill_level: SkillLevel,
    rng: random.Random,
) -> None:
    """Match households and jobs for one skill group."""

    candidates = [
        household
        for household in households
        if household.skill_level == skill_level
    ]

    job_slots = build_job_slots(
        firms=firms,
        skill_level=skill_level,
    )

    rng.shuffle(candidates)
    rng.shuffle(job_slots)

    number_matches = min(
        len(candidates),
        len(job_slots),
    )

    for household, job_slot in zip(
        candidates[:number_matches],
        job_slots[:number_matches],
    ):
        firm, employment_status = job_slot

        household.employment_status = (
            employment_status
        )

        household.employer_id = firm.firm_id

        register_firm_employment(
            firm=firm,
            status=employment_status,
        )


def match_households_to_jobs(
    households: list[Household],
    firms: list[Firm],
    rng: random.Random,
) -> dict[str, int]:
    """Match households to available private-sector jobs."""

    reset_firm_employment(
        firms=firms,
    )

    for household in households:
        household.employment_status = (
            EmploymentStatus.UNEMPLOYED
        )
        household.employer_id = -1

    match_one_skill_group(
        households=households,
        firms=firms,
        skill_level=SkillLevel.LOW_SKILL,
        rng=rng,
    )

    match_one_skill_group(
        households=households,
        firms=firms,
        skill_level=SkillLevel.HIGH_SKILL,
        rng=rng,
    )

    target_jobs = sum(
        firm.target_total_jobs
        for firm in firms
    )

    filled_jobs = sum(
        firm.total_employment
        for firm in firms
    )

    unemployed = sum(
        household.employment_status
        == EmploymentStatus.UNEMPLOYED
        for household in households
    )

    return {
        "target_jobs": target_jobs,
        "filled_jobs": filled_jobs,
        "vacancies": target_jobs - filled_jobs,
        "unemployed": unemployed,
    }


def initialize_labour_market(
    households: list[Household],
    firms: list[Firm],
    params: Parameters,
) -> dict[str, int]:
    """Initialize household skills and private employment."""

    skill_rng = random.Random(
        params.seed
        + params.household_skill_seed_offset
    )

    matching_rng = random.Random(
        params.seed
        + params.labour_matching_seed_offset
    )

    initialize_household_skills(
        households=households,
        params=params,
        rng=skill_rng,
    )

    return match_households_to_jobs(
        households=households,
        firms=firms,
        rng=matching_rng,
    )

def is_private_employment_status(
    status: EmploymentStatus,
) -> bool:
    """Return whether a status is a private-sector job."""

    return status in {
        EmploymentStatus.LOW_SKILLED_BROWN,
        EmploymentStatus.LOW_SKILLED_GREEN,
        EmploymentStatus.HIGH_SKILLED_BROWN,
        EmploymentStatus.HIGH_SKILLED_GREEN,
    }


def recount_firm_employment(
    households: list[Household],
    firms: list[Firm],
) -> None:
    """Reconstruct firm employment from household assignments."""

    reset_firm_employment(
        firms=firms,
    )

    firms_by_id = {
        firm.firm_id: firm
        for firm in firms
    }

    for household in households:
        if not is_private_employment_status(
            household.employment_status
        ):
            continue

        if household.employer_id not in firms_by_id:
            raise ValueError(
                f"Household {household.household_id} "
                f"is linked to unknown firm "
                f"{household.employer_id}."
            )

        register_firm_employment(
            firm=firms_by_id[
                household.employer_id
            ],
            status=household.employment_status,
        )


def job_demand_for_status(
    firm: Firm,
    status: EmploymentStatus,
) -> int:
    """Return the firm's target for one job category."""

    if status == EmploymentStatus.LOW_SKILLED_BROWN:
        return firm.brown_low_skill_demand

    if status == EmploymentStatus.LOW_SKILLED_GREEN:
        return firm.green_low_skill_demand

    if status == EmploymentStatus.HIGH_SKILLED_BROWN:
        return firm.brown_high_skill_demand

    if status == EmploymentStatus.HIGH_SKILLED_GREEN:
        return firm.green_high_skill_demand

    raise ValueError(
        f"Status {status} is not a private-sector job."
    )


def job_employment_for_status(
    firm: Firm,
    status: EmploymentStatus,
) -> int:
    """Return current employment for one job category."""

    if status == EmploymentStatus.LOW_SKILLED_BROWN:
        return firm.brown_low_skill_employment

    if status == EmploymentStatus.LOW_SKILLED_GREEN:
        return firm.green_low_skill_employment

    if status == EmploymentStatus.HIGH_SKILLED_BROWN:
        return firm.brown_high_skill_employment

    if status == EmploymentStatus.HIGH_SKILLED_GREEN:
        return firm.green_high_skill_employment

    raise ValueError(
        f"Status {status} is not a private-sector job."
    )


def lay_off_excess_workers(
    households: list[Household],
    firms: list[Firm],
    rng: random.Random,
) -> int:
    """Lay off workers exceeding firms' new job targets."""

    private_statuses = [
        EmploymentStatus.LOW_SKILLED_BROWN,
        EmploymentStatus.LOW_SKILLED_GREEN,
        EmploymentStatus.HIGH_SKILLED_BROWN,
        EmploymentStatus.HIGH_SKILLED_GREEN,
    ]

    layoffs = 0

    for firm in sorted(
        firms,
        key=lambda item: item.firm_id,
    ):
        for status in private_statuses:
            current_employment = (
                job_employment_for_status(
                    firm=firm,
                    status=status,
                )
            )

            target_employment = (
                job_demand_for_status(
                    firm=firm,
                    status=status,
                )
            )

            excess_workers = max(
                0,
                current_employment
                - target_employment,
            )

            if excess_workers == 0:
                continue

            eligible_workers = [
                household
                for household in households
                if (
                    household.employer_id
                    == firm.firm_id
                    and household.employment_status
                    == status
                )
            ]

            rng.shuffle(
                eligible_workers
            )

            for household in eligible_workers[:excess_workers]:
                household.employment_status = (
                    EmploymentStatus.UNEMPLOYED
                )
                household.employer_id = -1
                layoffs += 1

    recount_firm_employment(
        households=households,
        firms=firms,
    )

    return layoffs


def build_vacancy_slots(
    firms: list[Firm],
    skill_level: SkillLevel,
) -> list[tuple[Firm, EmploymentStatus]]:
    """Build currently unfilled job slots."""

    vacancies: list[
        tuple[Firm, EmploymentStatus]
    ] = []

    if skill_level == SkillLevel.LOW_SKILL:
        statuses = [
            EmploymentStatus.LOW_SKILLED_BROWN,
            EmploymentStatus.LOW_SKILLED_GREEN,
        ]
    else:
        statuses = [
            EmploymentStatus.HIGH_SKILLED_BROWN,
            EmploymentStatus.HIGH_SKILLED_GREEN,
        ]

    for firm in sorted(
        firms,
        key=lambda item: item.firm_id,
    ):
        if not firm.active:
            continue

        for status in statuses:
            vacancy_count = max(
                0,
                job_demand_for_status(
                    firm=firm,
                    status=status,
                )
                - job_employment_for_status(
                    firm=firm,
                    status=status,
                ),
            )

            vacancies.extend(
                [(firm, status)]
                * vacancy_count
            )

    return vacancies


def hire_unemployed_workers(
    households: list[Household],
    firms: list[Firm],
    skill_level: SkillLevel,
    rng: random.Random,
) -> int:
    """Hire unemployed households into compatible vacancies."""

    candidates = [
        household
        for household in households
        if (
            household.employment_status
            == EmploymentStatus.UNEMPLOYED
            and household.skill_level
            == skill_level
        )
    ]

    vacancies = build_vacancy_slots(
        firms=firms,
        skill_level=skill_level,
    )

    rng.shuffle(candidates)
    rng.shuffle(vacancies)

    number_hired = min(
        len(candidates),
        len(vacancies),
    )

    for household, vacancy in zip(
        candidates[:number_hired],
        vacancies[:number_hired],
    ):
        firm, status = vacancy

        household.employment_status = status
        household.employer_id = firm.firm_id

        register_firm_employment(
            firm=firm,
            status=status,
        )

    return number_hired


def update_labour_market(
    households: list[Household],
    firms: list[Firm],
    rng: random.Random,
) -> dict[str, int]:
    """Update private employment after period 0."""

    recount_firm_employment(
        households=households,
        firms=firms,
    )

    employment_before = sum(
        firm.total_employment
        for firm in firms
    )

    layoffs = lay_off_excess_workers(
        households=households,
        firms=firms,
        rng=rng,
    )

    low_skill_hires = hire_unemployed_workers(
        households=households,
        firms=firms,
        skill_level=SkillLevel.LOW_SKILL,
        rng=rng,
    )

    high_skill_hires = hire_unemployed_workers(
        households=households,
        firms=firms,
        skill_level=SkillLevel.HIGH_SKILL,
        rng=rng,
    )

    hires = (
        low_skill_hires
        + high_skill_hires
    )

    target_jobs = sum(
        firm.target_total_jobs
        for firm in firms
    )

    filled_jobs = sum(
        firm.total_employment
        for firm in firms
    )

    unemployed = sum(
        household.employment_status
        == EmploymentStatus.UNEMPLOYED
        for household in households
    )

    vacancies = sum(
        max(
            0,
            firm.target_total_jobs
            - firm.total_employment,
        )
        for firm in firms
    )

    return {
        "target_jobs": target_jobs,
        "employment_before": employment_before,
        "layoffs": layoffs,
        "hires": hires,
        "low_skill_hires": low_skill_hires,
        "high_skill_hires": high_skill_hires,
        "filled_jobs": filled_jobs,
        "vacancies": vacancies,
        "unemployed": unemployed,
    }
