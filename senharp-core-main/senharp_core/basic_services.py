"""Universal basic services for the post-growth package."""

from .entities import (
    Government,
    Household,
    PolicyState,
    Scenario,
)
from .parameters import Parameters


def _factual_ubs_terms(params: Parameters) -> tuple[tuple[float, float, float, float], ...]:
    """Return essential share, socialised share, admin price and copay."""
    return (
        (params.essential_agriculture_share, params.post_growth_ubs_target_agriculture, params.post_growth_ubs_admin_agriculture, params.post_growth_ubs_copay_agriculture),
        (params.essential_energy_share, params.post_growth_ubs_target_energy, params.post_growth_ubs_admin_energy, params.post_growth_ubs_copay_energy),
        (params.essential_housing_share, params.post_growth_ubs_target_housing, params.post_growth_ubs_admin_housing, params.post_growth_ubs_copay_housing),
        (params.essential_transport_share, params.post_growth_ubs_target_transport, params.post_growth_ubs_admin_transport, params.post_growth_ubs_copay_transport),
    )


def _ubs_strength(policy: PolicyState, params: Parameters) -> float:
    """Three-period factual ramp, scaled by the experimental UBS ratio."""
    if not post_growth_basic_services_are_active(policy):
        return 0.0
    ratio_scale = params.post_growth_basic_services_ratio / 0.20
    active_periods = getattr(policy, "consecutive_active_periods", None)
    # Standalone unit calls without a model policy clock represent a
    # mature programme; full Model runs use the explicit three-period ramp.
    elapsed = (
        params.post_growth_basic_services_ramp_periods
        if active_periods is None
        else max(0, int(active_periods))
    )
    ramp = min(1.0, elapsed / max(1, params.post_growth_basic_services_ramp_periods))
    return min(1.0, max(0.0, ratio_scale * ramp))


def post_growth_basic_services_are_active(
    policy: PolicyState,
) -> bool:
    """Return whether the UBS programme is active."""

    return (
        policy.active
        and policy.scenario == Scenario.POST_GROWTH
    )


def prepare_household_basic_services_substitution(
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
    minimum_wage: float,
) -> dict[str, float]:
    """Prepare the simple factual substitution of UBS for private C."""

    no_respend_rate = params.post_growth_basic_services_no_respend_rate
    if not 0.0 <= no_respend_rate <= 1.0:
        raise ValueError(
            "post_growth_basic_services_no_respend_rate must be "
            "between zero and one."
        )

    strength = _ubs_strength(policy, params)
    total_replaced = 0.0
    total_public_cost = 0.0
    for household in households:
        base_cost = max(0.0, household.base_consumption_cost)
        replaced = 0.0
        public_cost = 0.0
        for essential_share, target, admin, copay in _factual_ubs_terms(params):
            socialised = base_cost * essential_share * target * strength
            household_payment = socialised * admin * copay
            replaced += socialised - household_payment
            public_cost += socialised * admin * (1.0 - copay)
        household.planned_basic_services_received = min(base_cost, replaced)
        household.planned_basic_services_public_cost = public_cost
        household.constrained_consumption_cost = base_cost
        total_replaced += household.planned_basic_services_received
        total_public_cost += public_cost

    return {
        "ubs_strength": strength,
        "planned_ubs_public_cost_per_household": total_public_cost / len(households) if households else 0.0,
        "planned_ubs_service_value_per_household": total_replaced / len(households) if households else 0.0,
        "planned_private_consumption_replaced": total_replaced,
    }


def plan_post_growth_basic_services(
    government: Government,
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
    minimum_wage: float,
) -> dict[str, float | int]:
    """Plan additional current public purchases for UBS.

    UBS are purchases of services in kind. They are therefore
    excluded from household transfers and disposable income.

    The function must be called once per period, after ordinary
    government spending has been computed and before sectoral
    government demand is allocated.
    """

    ratio = params.post_growth_basic_services_ratio
    admin_factor = params.post_growth_basic_services_admin_price_factor

    if not 0.0 <= ratio <= 1.0:
        raise ValueError(
            "post_growth_basic_services_ratio must be "
            "between zero and one."
        )

    if minimum_wage < 0.0:
        raise ValueError(
            "minimum_wage cannot be negative."
        )
    if not 0.0 < admin_factor <= 1.0:
        raise ValueError(
            "post_growth_basic_services_admin_price_factor must be "
            "strictly positive and at most one."
        )

    active = post_growth_basic_services_are_active(
        policy=policy,
    )

    if active and not any(
        getattr(h, "planned_basic_services_public_cost", 0.0) > 0.0
        for h in households
    ):
        if all(hasattr(h, "base_consumption_cost") for h in households):
            prepare_household_basic_services_substitution(
                households=households,
                policy=policy,
                params=params,
                minimum_wage=minimum_wage,
            )
        else:
            # Compatibility for standalone accounting calls that do not
            # provide household consumption baskets.
            legacy_cost = ratio * minimum_wage
            for household in households:
                household.planned_basic_services_public_cost = legacy_cost

    unit_basic_services = (
        sum(getattr(h, "planned_basic_services_public_cost", 0.0) for h in households) / len(households)
        if active and households else 0.0
    )

    number_households = len(households)

    planned_basic_services = (
        number_households
        * unit_basic_services
    )

    # Ordinary current purchases have already been determined
    # by update_government_spending.
    base_current_purchases = max(
        0.0,
        government.current_purchases,
    )

    government.base_current_purchases = (
        base_current_purchases
    )

    government.planned_basic_services_spending = (
        planned_basic_services
    )
    government.basic_services_admin_price_factor = admin_factor

    # Before market settlement, delivery is provisionally
    # assumed to be complete. PG-3A-2 will overwrite these
    # values after sectoral rationing.
    government.realised_basic_services_spending = (
        planned_basic_services
    )

    government.unmet_basic_services_spending = 0.0

    government.current_purchases = (
        base_current_purchases
        + planned_basic_services
    )

    government.planned_current_purchases = (
        government.current_purchases
    )

    government.realised_current_purchases = (
        government.current_purchases
    )

    government.unmet_current_purchases = 0.0

    # Recalculate the provisional public budget after adding
    # planned UBS purchases.
    government.current_spending = (
        government.transfer_spending
        + government.public_wage_spending
        + government.current_purchases
    )

    government.primary_deficit = (
        government.current_spending
        + government.capital_spending
        - government.total_revenue
    )

    government.deficit = (
        government.primary_deficit
        + government.interest_payment
    )

    expected_planned_basic_services = (
        number_households
        * unit_basic_services
    )

    return {
        "post_growth_basic_services_active": int(
            active
        ),
        "basic_services_ratio": ratio,
        "unit_basic_services": (
            unit_basic_services
        ),
        "number_basic_services_entitlements": (
            number_households
            if active
            else 0
        ),
        "base_current_purchases": (
            base_current_purchases
        ),
        "planned_basic_services_spending": (
            planned_basic_services
        ),
        "total_planned_current_purchases": (
            government.current_purchases
        ),
        "basic_services_planning_gap": (
            planned_basic_services
            - expected_planned_basic_services
        ),
    }

BASIC_SERVICES_SECTORS = (
    "agriculture",
    "energy",
    "housing",
    "transport",
    "industry",
    "technology",
)


def compute_bounded_delivery_ratio(
    planned: float,
    realised: float,
) -> float:
    """Return a current-purchase delivery ratio in [0, 1]."""

    planned_value = max(
        0.0,
        planned,
    )

    realised_value = max(
        0.0,
        realised,
    )

    if planned_value <= 1e-12:
        return 1.0

    return min(
        1.0,
        realised_value / planned_value,
    )


def settle_post_growth_basic_services(
    government: Government,
    households: list[Household],
    sector_government_demand_results: dict[str, float],
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
) -> dict[str, float]:
    """Settle UBS and distribute delivered services equally.

    UBS have the same sector-specific delivery ratio as the
    other current government purchases in the same sector.
    """

    if sector_government_demand_results is None:
        raise ValueError(
            "Sectoral government demand results are required "
            "for basic-services settlement."
        )

    if market_settlement_results is None:
        raise ValueError(
            "Market settlement results are required "
            "for basic-services settlement."
        )

    market_by_sector: dict[
        str,
        dict[str, float | str],
    ] = {}

    for row in market_settlement_results:
        sector_value = row["sector"]

        if hasattr(sector_value, "value"):
            sector_name = str(sector_value.value)
        else:
            sector_name = str(sector_value)

        market_by_sector[sector_name] = row

    total_sector_planned_basic_services = 0.0
    total_realised_basic_services = 0.0

    delivery_ratios: dict[str, float] = {}

    for sector in BASIC_SERVICES_SECTORS:
        if sector not in market_by_sector:
            raise KeyError(
                "Missing market-settlement row for "
                f"sector {sector!r}."
            )

        row = market_by_sector[sector]

        planned_current = max(
            0.0,
            float(
                row[
                    "planned_current_government_demand"
                ]
            ),
        )

        realised_current = max(
            0.0,
            float(
                row[
                    "realised_current_government_demand"
                ]
            ),
        )

        planned_sector_basic_services = max(
            0.0,
            float(
                sector_government_demand_results[
                    f"{sector}_basic_services_"
                    "government_demand"
                ]
            ),
        )

        if (
            planned_sector_basic_services
            > planned_current + 1e-9
        ):
            raise ValueError(
                "Sectoral UBS demand cannot exceed total "
                "current government demand."
            )

        delivery_ratio = (
            compute_bounded_delivery_ratio(
                planned=planned_current,
                realised=realised_current,
            )
        )

        realised_sector_basic_services = (
            planned_sector_basic_services
            * delivery_ratio
        )

        delivery_ratios[sector] = (
            delivery_ratio
        )

        total_sector_planned_basic_services += (
            planned_sector_basic_services
        )

        total_realised_basic_services += (
            realised_sector_basic_services
        )

    planned_basic_services = max(
        0.0,
        government.planned_basic_services_spending,
    )

    unmet_basic_services = max(
        0.0,
        planned_basic_services
        - total_realised_basic_services,
    )

    government.realised_basic_services_spending = (
        total_realised_basic_services
    )

    government.unmet_basic_services_spending = (
        unmet_basic_services
    )

    number_households = len(households)

    if (
        number_households == 0
        and total_realised_basic_services > 1e-12
    ):
        raise ValueError(
            "Delivered basic services cannot be allocated "
            "without households."
        )

    admin_factor = float(
        getattr(government, "basic_services_admin_price_factor", 1.0)
    )
    if not 0.0 < admin_factor <= 1.0:
        raise ValueError(
            "Government UBS administrative price factor must be "
            "strictly positive and at most one."
        )

    unit_basic_services_public_cost = (
        total_realised_basic_services
        / number_households
        if number_households > 0
        else 0.0
    )
    overall_delivery_ratio = (
        total_realised_basic_services / planned_basic_services
        if planned_basic_services > 1e-12 else 0.0
    )

    for household in households:
        household.previous_basic_services_coverage = min(
            1.0,
            max(
                0.0,
                getattr(household, "basic_services_coverage", 0.0),
            ),
        )

        planned_household_service = getattr(
            household,
            "planned_basic_services_received",
            planned_basic_services / number_households / admin_factor
            if number_households > 0 else 0.0,
        )
        household.basic_services_received = (
            planned_household_service * overall_delivery_ratio
        )

        essential_cost = max(
            1e-9,
            household.base_consumption_cost,
        )

        household.basic_services_coverage = min(
            1.0,
            household.basic_services_received
            / essential_cost,
        )

        household.basic_services_coverage_change = (
            household.basic_services_coverage
            - household.previous_basic_services_coverage
        )

        household.basic_services_component = 0.0
        household.constrained_consumption_cost = max(
            0.0,
            household.base_consumption_cost - household.basic_services_received,
        )

    allocated_to_households = sum(
        household.basic_services_received
        for household in households
    )
    realised_service_value = allocated_to_households

    results: dict[str, float] = {
        "planned_basic_services_spending": (
            planned_basic_services
        ),

        "realised_basic_services_spending": (
            total_realised_basic_services
        ),

        "unmet_basic_services_spending": (
            unmet_basic_services
        ),

        "unit_basic_services_received": (
            allocated_to_households / number_households if number_households else 0.0
        ),
        "unit_basic_services_public_cost": (
            unit_basic_services_public_cost
        ),

        "basic_services_sector_allocation_gap": (
            planned_basic_services
            - total_sector_planned_basic_services
        ),

        "basic_services_settlement_gap": (
            planned_basic_services
            - total_realised_basic_services
            - unmet_basic_services
        ),

        "basic_services_household_allocation_gap": (
            realised_service_value
            - allocated_to_households
        ),
    }

    for sector, ratio in delivery_ratios.items():
        results[
            f"{sector}_basic_services_delivery_ratio"
        ] = ratio

    return results
