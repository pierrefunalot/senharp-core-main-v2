"""Allocation of household consumption across sectors."""

import random

from .entities import Household
from .parameters import Parameters


def validate_consumption_shares(
    params: Parameters,
) -> None:
    """Check that essential and supplementary shares sum to one."""

    essential_sum = (
        params.essential_agriculture_share
        + params.essential_energy_share
        + params.essential_housing_share
        + params.essential_transport_share
    )

    rural_sum = (
        params.rural_agriculture_preference
        + params.rural_energy_preference
        + params.rural_housing_preference
        + params.rural_transport_preference
        + params.rural_industry_preference
        + params.rural_technology_preference
    )

    urban_sum = (
        params.urban_agriculture_preference
        + params.urban_energy_preference
        + params.urban_housing_preference
        + params.urban_transport_preference
        + params.urban_industry_preference
        + params.urban_technology_preference
    )

    if abs(essential_sum - 1.0) > 1e-12:
        raise ValueError(
            "Essential consumption shares must sum to one."
        )

    if abs(rural_sum - 1.0) > 1e-12:
        raise ValueError(
            "Rural consumption preferences must sum to one."
        )

    if abs(urban_sum - 1.0) > 1e-12:
        raise ValueError(
            "Urban consumption preferences must sum to one."
        )


def initialize_household_consumption_preferences(
    households: list[Household],
    params: Parameters,
) -> dict[int, int]:
    """Assign territory and supplementary preferences.

    The assignment uses an independent random stream and therefore
    does not alter the political or labour-market random sequences.
    """

    validate_consumption_shares(
        params=params,
    )

    rural_share = params.rural_household_share

    if not 0.0 <= rural_share <= 1.0:
        raise ValueError(
            "rural_household_share must be between zero and one."
        )

    rng = random.Random(
        params.seed
        + params.household_consumption_preference_seed_offset
    )

    ordered_households = sorted(
        households,
        key=lambda household: household.household_id,
    )

    number_households = len(
        ordered_households
    )

    number_rural = round(
        rural_share
        * number_households
    )

    number_urban = (
        number_households
        - number_rural
    )

    territories = (
        [0] * number_rural
        + [1] * number_urban
    )

    rng.shuffle(
        territories
    )

    for household, territory_id in zip(
        ordered_households,
        territories,
    ):
        household.territory_id = territory_id

        if territory_id == 0:
            household.agriculture_preference = (
                params.rural_agriculture_preference
            )

            household.energy_preference = (
                params.rural_energy_preference
            )

            household.housing_preference = (
                params.rural_housing_preference
            )

            household.transport_preference = (
                params.rural_transport_preference
            )

            household.industry_preference = (
                params.rural_industry_preference
            )

            household.technology_preference = (
                params.rural_technology_preference
            )

        else:
            household.agriculture_preference = (
                params.urban_agriculture_preference
            )

            household.energy_preference = (
                params.urban_energy_preference
            )

            household.housing_preference = (
                params.urban_housing_preference
            )

            household.transport_preference = (
                params.urban_transport_preference
            )

            household.industry_preference = (
                params.urban_industry_preference
            )

            household.technology_preference = (
                params.urban_technology_preference
            )

    return {
        0: number_rural,
        1: number_urban,
    }


def reset_sector_consumption_flows(
    households: list[Household],
) -> None:
    """Reset all current-period sectoral consumption flows."""

    sector_fields = [
        "essential_agriculture_consumption",
        "essential_energy_consumption",
        "essential_housing_consumption",
        "essential_transport_consumption",
        "essential_industry_consumption",
        "essential_technology_consumption",

        "supplementary_agriculture_consumption",
        "supplementary_energy_consumption",
        "supplementary_housing_consumption",
        "supplementary_transport_consumption",
        "supplementary_industry_consumption",
        "supplementary_technology_consumption",

        "agriculture_consumption",
        "energy_consumption",
        "housing_consumption",
        "transport_consumption",
        "industry_consumption",
        "technology_consumption",
    ]

    for household in households:
        for field_name in sector_fields:
            setattr(
                household,
                field_name,
                0.0,
            )


def allocate_household_consumption_by_sector(
    households: list[Household],
    params: Parameters,
) -> dict[str, float]:
    """Allocate essential and supplementary consumption by sector."""

    validate_consumption_shares(
        params=params,
    )

    reset_sector_consumption_flows(
        households=households,
    )

    for household in households:
        essential = max(
            0.0,
            household.essential_consumption,
        )

        supplementary = max(
            0.0,
            household.supplementary_consumption,
        )

        # Essential basket:
        # agriculture, energy, housing and transport only.
        household.essential_agriculture_consumption = (
            essential
            * params.essential_agriculture_share
        )

        household.essential_energy_consumption = (
            essential
            * params.essential_energy_share
        )

        household.essential_housing_consumption = (
            essential
            * params.essential_housing_share
        )

        household.essential_transport_consumption = (
            essential
            * params.essential_transport_share
        )

        household.essential_industry_consumption = 0.0
        household.essential_technology_consumption = 0.0

        # Supplementary expenditure follows household preferences.
        household.supplementary_agriculture_consumption = (
            supplementary
            * household.agriculture_preference
        )

        household.supplementary_energy_consumption = (
            supplementary
            * household.energy_preference
        )

        household.supplementary_housing_consumption = (
            supplementary
            * household.housing_preference
        )

        household.supplementary_transport_consumption = (
            supplementary
            * household.transport_preference
        )

        household.supplementary_industry_consumption = (
            supplementary
            * household.industry_preference
        )

        household.supplementary_technology_consumption = (
            supplementary
            * household.technology_preference
        )

        household.agriculture_consumption = (
            household.essential_agriculture_consumption
            + household.supplementary_agriculture_consumption
        )

        household.energy_consumption = (
            household.essential_energy_consumption
            + household.supplementary_energy_consumption
        )

        household.housing_consumption = (
            household.essential_housing_consumption
            + household.supplementary_housing_consumption
        )

        household.transport_consumption = (
            household.essential_transport_consumption
            + household.supplementary_transport_consumption
        )

        household.industry_consumption = (
            household.essential_industry_consumption
            + household.supplementary_industry_consumption
        )

        household.technology_consumption = (
            household.essential_technology_consumption
            + household.supplementary_technology_consumption
        )

    agriculture_demand = sum(
        household.agriculture_consumption
        for household in households
    )

    energy_demand = sum(
        household.energy_consumption
        for household in households
    )

    housing_demand = sum(
        household.housing_consumption
        for household in households
    )

    transport_demand = sum(
        household.transport_consumption
        for household in households
    )

    industry_demand = sum(
        household.industry_consumption
        for household in households
    )

    technology_demand = sum(
        household.technology_consumption
        for household in households
    )

    total_sector_demand = (
        agriculture_demand
        + energy_demand
        + housing_demand
        + transport_demand
        + industry_demand
        + technology_demand
    )

    total_household_consumption = sum(
        household.total_consumption
        for household in households
    )

    total_essential_consumption = sum(
        household.essential_consumption
        for household in households
    )

    total_supplementary_consumption = sum(
        household.supplementary_consumption
        for household in households
    )

    allocated_essential_consumption = sum(
        household.essential_agriculture_consumption
        + household.essential_energy_consumption
        + household.essential_housing_consumption
        + household.essential_transport_consumption
        + household.essential_industry_consumption
        + household.essential_technology_consumption
        for household in households
    )

    allocated_supplementary_consumption = sum(
        household.supplementary_agriculture_consumption
        + household.supplementary_energy_consumption
        + household.supplementary_housing_consumption
        + household.supplementary_transport_consumption
        + household.supplementary_industry_consumption
        + household.supplementary_technology_consumption
        for household in households
    )

    results = {
        "agriculture_demand": agriculture_demand,
        "energy_demand": energy_demand,
        "housing_demand": housing_demand,
        "transport_demand": transport_demand,
        "industry_demand": industry_demand,
        "technology_demand": technology_demand,

        "total_sector_demand": total_sector_demand,

        "total_household_consumption": (
            total_household_consumption
        ),

        "total_essential_consumption": (
            total_essential_consumption
        ),

        "allocated_essential_consumption": (
            allocated_essential_consumption
        ),

        "total_supplementary_consumption": (
            total_supplementary_consumption
        ),

        "allocated_supplementary_consumption": (
            allocated_supplementary_consumption
        ),

        "sector_allocation_gap": (
            total_household_consumption
            - total_sector_demand
        ),

        "essential_allocation_gap": (
            total_essential_consumption
            - allocated_essential_consumption
        ),

        "supplementary_allocation_gap": (
            total_supplementary_consumption
            - allocated_supplementary_consumption
        ),
    }

    essential_sector_demand = {
        "agriculture": sum(
            household.essential_agriculture_consumption
            for household in households
        ),
        "energy": sum(
            household.essential_energy_consumption
            for household in households
        ),
        "housing": sum(
            household.essential_housing_consumption
            for household in households
        ),
        "transport": sum(
            household.essential_transport_consumption
            for household in households
        ),
        "industry": sum(
            household.essential_industry_consumption
            for household in households
        ),
        "technology": sum(
            household.essential_technology_consumption
            for household in households
        ),
    }

    supplementary_sector_demand = {
        "agriculture": sum(
            household.supplementary_agriculture_consumption
            for household in households
        ),
        "energy": sum(
            household.supplementary_energy_consumption
            for household in households
        ),
        "housing": sum(
            household.supplementary_housing_consumption
            for household in households
        ),
        "transport": sum(
            household.supplementary_transport_consumption
            for household in households
        ),
        "industry": sum(
            household.supplementary_industry_consumption
            for household in households
        ),
        "technology": sum(
            household.supplementary_technology_consumption
            for household in households
        ),
    }

    for sector_name in essential_sector_demand:
        results[
            f"essential_{sector_name}_demand"
        ] = essential_sector_demand[
            sector_name
        ]

        results[
            f"supplementary_{sector_name}_demand"
        ] = supplementary_sector_demand[
            sector_name
        ]

    results[
        "essential_sector_detail_gap"
    ] = (
        results["total_essential_consumption"]
        - sum(
            essential_sector_demand.values()
        )
    )

    results[
        "supplementary_sector_detail_gap"
    ] = (
        results["total_supplementary_consumption"]
        - sum(
            supplementary_sector_demand.values()
        )
    )

    return results

    