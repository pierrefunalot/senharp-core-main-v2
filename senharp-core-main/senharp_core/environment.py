"""Environmental module for SEN-HARP Core.

This module computes:
- household emissions;
- aggregate emissions;
- the pollution stock;
- heterogeneous environmental damages.
"""

from .entities import Household, PolicyState, Scenario
from .parameters import Parameters


def get_emissions_multiplier(
    policy: PolicyState,
    params: Parameters,
) -> float:
    """Return the emissions multiplier associated with the policy regime.

    When the policy is inactive, emissions return to their
    reference level.
    """

    if not policy.active:
        return 1.0

    multipliers = {
        Scenario.CARBON_TAX: (
            params.carbon_tax_emissions_multiplier
        ),

        # The Green Deal skeleton initially has the same
        # reduced-form household-emissions effect as the
        # market-oriented carbon-tax package.
        Scenario.GREEN_DEAL: (
            params.carbon_tax_emissions_multiplier
        ),

        Scenario.POST_GROWTH: (
            params.post_growth_emissions_multiplier
        ),
    }

    return multipliers[policy.scenario]


def compute_household_emissions(
    household: Household,
    policy: PolicyState,
    params: Parameters,
) -> float:
    """Compute and store one household's emissions."""

    multiplier = get_emissions_multiplier(
        policy=policy,
        params=params,
    )

    energy_emissions = (
        params.base_energy_emissions
        * household.energy_exposure
        * multiplier
    )

    transport_factor = max(
        household.transport_cost
        / params.reference_transport_cost,
        0.0,
    )

    transport_emissions = (
        params.base_transport_emissions
        * transport_factor
        * multiplier
    )

    consumption_factor = max(
        household.disposable_income
        / params.reference_disposable_income,
        0.0,
    )

    consumption_emissions = (
        params.base_consumption_emissions
        * consumption_factor
        * multiplier
    )

    total_emissions = (
        energy_emissions
        + transport_emissions
        + consumption_emissions
    )

    household.energy_emissions = energy_emissions
    household.transport_emissions = transport_emissions
    household.consumption_emissions = (
        consumption_emissions
    )
    household.total_emissions = total_emissions

    return total_emissions


def update_environment(
    households: list[Household],
    policy: PolicyState,
    previous_pollution_stock: float,
    params: Parameters,
) -> tuple[float, float, float]:
    """Update emissions, pollution stock and environmental damages.

    Returns:
        total_emissions
        new_pollution_stock
        mean_environmental_damage
    """

    total_emissions = sum(
        compute_household_emissions(
            household=household,
            policy=policy,
            params=params,
        )
        for household in households
    )

    new_pollution_stock = (
        (
            1.0
            - params.pollution_decay_rate
        )
        * previous_pollution_stock
        + total_emissions
    )

    mean_damage_reference = (
        params.environmental_damage_scale
        * new_pollution_stock
        / len(households)
    )

    for household in households:

        # Vulnérabilité environnementale stylisée :
        # exposition énergétique, territoriale et professionnelle.
        vulnerability = (
            0.40
            * household.energy_exposure
            + 0.30
            * household.distance_to_public_services
            + 0.30
            * household.brown_job_exposure
        )

        household.environmental_damage = (
            mean_damage_reference
            * (
                0.50
                + vulnerability
            )
        )

    mean_environmental_damage = (
        sum(
            household.environmental_damage
            for household in households
        )
        / len(households)
    )

    return (
        total_emissions,
        new_pollution_stock,
        mean_environmental_damage,
    )