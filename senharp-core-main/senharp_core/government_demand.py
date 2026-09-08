"""Sectoral allocation of direct government purchases."""

from .entities import Government
from .parameters import Parameters


def validate_government_demand_shares(
    params: Parameters,
) -> None:
    """Validate current and capital public-purchase shares."""

    current_shares = [
        params.government_current_agriculture_share,
        params.government_current_energy_share,
        params.government_current_housing_share,
        params.government_current_transport_share,
        params.government_current_industry_share,
        params.government_current_technology_share,
    ]

    capital_shares = [
        params.government_capital_agriculture_share,
        params.government_capital_energy_share,
        params.government_capital_housing_share,
        params.government_capital_transport_share,
        params.government_capital_industry_share,
        params.government_capital_technology_share,
    ]

    if any(
        share < 0.0 or share > 1.0
        for share in current_shares + capital_shares
    ):
        raise ValueError(
            "Government demand shares must be "
            "between zero and one."
        )

    if abs(sum(current_shares) - 1.0) > 1e-12:
        raise ValueError(
            "Current government-purchase shares "
            "must sum to one."
        )

    if abs(sum(capital_shares) - 1.0) > 1e-12:
        raise ValueError(
            "Capital government-purchase shares "
            "must sum to one."
        )

    basic_services_shares = [
        params.post_growth_basic_services_agriculture_share,
        params.post_growth_basic_services_energy_share,
        params.post_growth_basic_services_housing_share,
        params.post_growth_basic_services_transport_share,
        params.post_growth_basic_services_industry_share,
        params.post_growth_basic_services_technology_share,
    ]

    if any(
        not 0.0 <= share <= 1.0
        for share in basic_services_shares
    ):
        raise ValueError(
            "Universal-basic-services sector shares must "
            "be between zero and one."
        )

    if abs(sum(basic_services_shares) - 1.0) > 1e-12:
        raise ValueError(
            "Universal-basic-services sector shares "
            "must sum to one."
        )


def compute_sector_government_demand(
    government: Government,
    params: Parameters,
) -> dict[str, float]:
    """Allocate direct government purchases across sectors.

    Transfers and public wages are excluded because they already
    enter household income and household consumption.
    """

    validate_government_demand_shares(
        params=params,
    )

    current_purchases = max(
        0.0,
        government.current_purchases,
    )

    planned_basic_services = max(
        0.0,
        government.planned_basic_services_spending,
    )

    base_current_purchases = max(
        0.0,
        government.base_current_purchases,
    )

    # Backward-compatible case for tests or mechanisms that
    # call this function without prior UBS planning.
    if planned_basic_services <= 1e-12:
        base_current_purchases = current_purchases

    current_purchase_decomposition_gap = (
        current_purchases
        - base_current_purchases
        - planned_basic_services
    )

    if abs(current_purchase_decomposition_gap) > 1e-9:
        raise ValueError(
            "Current government purchases must equal base "
            "current purchases plus planned basic services."
        )

    base_capital_purchases = max(
        0.0,
        government.base_capital_purchases,
    )
    
    public_green_investment = max(
        0.0,
        government.planned_public_green_investment,
    )

    capital_purchases = (
        base_capital_purchases
        + public_green_investment
    )

    base_current_shares = {
        "agriculture": (
            params.government_current_agriculture_share
        ),
        "energy": (
            params.government_current_energy_share
        ),
        "housing": (
            params.government_current_housing_share
        ),
        "transport": (
            params.government_current_transport_share
        ),
        "industry": (
            params.government_current_industry_share
        ),
        "technology": (
            params.government_current_technology_share
        ),
    }

    basic_services_shares = {
        "agriculture": (
            params.post_growth_basic_services_agriculture_share
        ),
        "energy": (
            params.post_growth_basic_services_energy_share
        ),
        "housing": (
            params.post_growth_basic_services_housing_share
        ),
        "transport": (
            params.post_growth_basic_services_transport_share
        ),
        "industry": (
            params.post_growth_basic_services_industry_share
        ),
        "technology": (
            params.post_growth_basic_services_technology_share
        ),
    }

    base_current_demand = {
        sector: (
            base_current_purchases
            * base_current_shares[sector]
        )
        for sector in base_current_shares
    }

    basic_services_demand = {
        sector: (
            planned_basic_services
            * basic_services_shares[sector]
        )
        for sector in basic_services_shares
    }

    current_demand = {
        sector: (
            base_current_demand[sector]
            + basic_services_demand[sector]
        )
        for sector in base_current_demand
    }

    capital_demand = {
        "agriculture": (
            base_capital_purchases
            * params.government_capital_agriculture_share
        ),
        "energy": (
            base_capital_purchases
            * params.government_capital_energy_share
        ),
        "housing": (
            base_capital_purchases
            * params.government_capital_housing_share
        ),
        "transport": (
            base_capital_purchases
            * params.government_capital_transport_share
        ),
        "industry": (
            base_capital_purchases
            * params.government_capital_industry_share
        ),
        "technology": (
            base_capital_purchases
            * params.government_capital_technology_share
             + public_green_investment
        ),
    }

    total_demand = {
        sector: (
            current_demand[sector]
            + capital_demand[sector]
        )
        for sector in current_demand
    }

    total_current_allocation = sum(
        current_demand.values()
    )

    total_capital_allocation = sum(
        capital_demand.values()
    )

    total_sector_government_demand = sum(
        total_demand.values()
    )

    results: dict[str, float] = {
        "total_current_government_demand": (
            current_purchases
        ),
        "total_capital_government_demand": (
            capital_purchases
        ),
        "total_sector_government_demand": (
            total_sector_government_demand
        ),
        "current_government_allocation_gap": (
            current_purchases
            - total_current_allocation
        ),
        "capital_government_allocation_gap": (
            capital_purchases
            - total_capital_allocation
        ),
        "total_government_allocation_gap": (
            current_purchases
            + capital_purchases
            - total_sector_government_demand
        ),
        "base_capital_government_demand": (
            base_capital_purchases
        ),
        "planned_public_green_investment": (
            public_green_investment
        ),

        "base_current_government_demand": (
            base_current_purchases
        ),

        "planned_basic_services_government_demand": (
            planned_basic_services
        ),

        "current_purchase_decomposition_gap": (
            current_purchase_decomposition_gap
        ),

        "basic_services_allocation_gap": (
            planned_basic_services
            - sum(basic_services_demand.values())
        ),
    }

    for sector in current_demand:
        results[
            f"{sector}_current_government_demand"
        ] = current_demand[sector]

        results[
            f"{sector}_capital_government_demand"
        ] = capital_demand[sector]

        results[
            f"{sector}_government_demand"
        ] = total_demand[sector]

        results[
            f"{sector}_base_current_government_demand"
        ] = base_current_demand[sector]

        results[
            f"{sector}_basic_services_government_demand"
        ] = basic_services_demand[sector]

    return results