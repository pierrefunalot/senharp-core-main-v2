"""Green Deal Job Guarantee transitions."""

from __future__ import annotations

import random

from .entities import EmploymentStatus, Household, PolicyState, Scenario
from .parameters import Parameters


def release_job_guarantee(households: list[Household]) -> int:
    """Return JG participants to the private-job candidate pool."""
    released = 0
    for household in households:
        if household.employment_status == EmploymentStatus.JOB_GUARANTEE:
            household.employment_status = EmploymentStatus.UNEMPLOYED
            household.employer_id = -1
            released += 1
    return released


def enrol_job_guarantee(
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
    rng: random.Random,
) -> dict[str, int]:
    """Enrol remaining unemployed people after private labour matching."""
    active = policy.active and policy.scenario == Scenario.GREEN_DEAL
    enrolled = 0
    if active:
        rate = params.green_deal_job_guarantee_entry_rate
        if not 0.0 <= rate <= 1.0:
            raise ValueError("green_deal_job_guarantee_entry_rate must be in [0, 1].")
        for household in households:
            if (
                household.employment_status == EmploymentStatus.UNEMPLOYED
                and rng.random() < rate
            ):
                household.employment_status = EmploymentStatus.JOB_GUARANTEE
                household.employer_id = -1
                enrolled += 1
    return {"job_guarantee_enrolled": enrolled}


def update_job_guarantee(
    households: list[Household], policy: PolicyState, params: Parameters, rng: random.Random
) -> dict[str, int]:
    """Standalone complete JG transition, primarily for direct use and tests."""
    released = release_job_guarantee(households)
    result = enrol_job_guarantee(households, policy, params, rng)
    return {"job_guarantee_released": released, **result}
