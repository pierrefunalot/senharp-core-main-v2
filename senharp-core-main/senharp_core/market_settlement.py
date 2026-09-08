"""Priority-based settlement of sectoral final demand."""

from .entities import Sector


def allocate_priority_demand(
    planned_demand: float,
    remaining_supply_value: float,
) -> tuple[float, float, float]:
    """Allocate one demand category against remaining supply.

    Returns:
        realised demand,
        unmet demand,
        remaining nominal supply.
    """

    planned = max(
        0.0,
        planned_demand,
    )

    remaining_supply = max(
        0.0,
        remaining_supply_value,
    )

    realised = min(
        planned,
        remaining_supply,
    )

    unmet = max(
        0.0,
        planned - realised,
    )

    remaining_supply_after = max(
        0.0,
        remaining_supply - realised,
    )

    return (
        realised,
        unmet,
        remaining_supply_after,
    )


def compute_market_settlement(
    sector_market_results: (
        list[dict[str, float | str]]
    ),
    sector_consumption_results: dict[str, float],
    sector_investment_demand_results: dict[str, float],
    sector_government_demand_results: dict[str, float],
) -> list[dict[str, float | str]]:
    """Settle sectoral demands according to a fixed priority.

    Priority order:

    1. essential household consumption;
    2. current government purchases;
    3. supplementary household consumption;
    4. private investment;
    5. public capital purchases.
    """

    if sector_market_results is None:
        raise ValueError(
            "Sector market results must be computed "
            "before market settlement."
        )

    if sector_consumption_results is None:
        raise ValueError(
            "Sector consumption results are missing."
        )

    if sector_investment_demand_results is None:
        raise ValueError(
            "Sector investment demand results are missing."
        )

    if sector_government_demand_results is None:
        raise ValueError(
            "Sector government demand results are missing."
        )

    market_by_sector = {
        str(row["sector"]): row
        for row in sector_market_results
    }

    results: list[
        dict[str, float | str]
    ] = []

    for sector in Sector:
        sector_name = sector.value

        market_row = market_by_sector[
            sector_name
        ]

        nominal_supply = max(
            0.0,
            float(
                market_row[
                    "nominal_supply_value"
                ]
            ),
        )

        market_total_nominal_demand = max(
            0.0,
            float(
                market_row[
                    "total_nominal_demand"
                ]
            ),
        )

        planned_demands = {
            "essential_household": max(
                0.0,
                sector_consumption_results[
                    f"essential_{sector_name}_demand"
                ],
            ),

            "current_government": max(
                0.0,
                sector_government_demand_results[
                    f"{sector_name}_current_government_demand"
                ],
            ),

            "supplementary_household": max(
                0.0,
                sector_consumption_results[
                    f"supplementary_{sector_name}_demand"
                ],
            ),

            "private_investment": max(
                0.0,
                sector_investment_demand_results[
                    f"{sector_name}_investment_demand"
                ],
            ),

            "capital_government": max(
                0.0,
                sector_government_demand_results[
                    f"{sector_name}_capital_government_demand"
                ],
            ),
        }

        remaining_supply = nominal_supply

        realised_demands: dict[str, float] = {}
        unmet_demands: dict[str, float] = {}

        for demand_category in [
            "essential_household",
            "current_government",
            "supplementary_household",
            "private_investment",
            "capital_government",
        ]:
            (
                realised,
                unmet,
                remaining_supply,
            ) = allocate_priority_demand(
                planned_demand=(
                    planned_demands[
                        demand_category
                    ]
                ),
                remaining_supply_value=(
                    remaining_supply
                ),
            )

            realised_demands[
                demand_category
            ] = realised

            unmet_demands[
                demand_category
            ] = unmet

        planned_total_demand = sum(
            planned_demands.values()
        )

        realised_total_demand = sum(
            realised_demands.values()
        )

        unmet_total_demand = sum(
            unmet_demands.values()
        )

        expected_realised_sales = min(
            nominal_supply,
            planned_total_demand,
        )

        demand_fulfilment_ratio = (
            realised_total_demand
            / planned_total_demand
            if planned_total_demand > 0.0
            else 1.0
        )

        supply_utilisation_ratio = (
            realised_total_demand
            / nominal_supply
            if nominal_supply > 0.0
            else 0.0
        )

        row: dict[str, float | str] = {
            "sector": sector_name,

            "nominal_supply": (
                nominal_supply
            ),

            "market_total_nominal_demand": (
                market_total_nominal_demand
            ),

            "planned_total_demand": (
                planned_total_demand
            ),

            "realised_total_demand": (
                realised_total_demand
            ),

            "unmet_total_demand": (
                unmet_total_demand
            ),

            "unused_nominal_supply": (
                remaining_supply
            ),

            "demand_fulfilment_ratio": (
                demand_fulfilment_ratio
            ),

            "supply_utilisation_ratio": (
                supply_utilisation_ratio
            ),

            "planned_demand_accounting_gap": (
                market_total_nominal_demand
                - planned_total_demand
            ),

            "settlement_accounting_gap": (
                expected_realised_sales
                - realised_total_demand
            ),

            "demand_balance_gap": (
                planned_total_demand
                - realised_total_demand
                - unmet_total_demand
            ),

            "supply_balance_gap": (
                nominal_supply
                - realised_total_demand
                - remaining_supply
            ),
        }

        for demand_category in planned_demands:
            row[
                f"planned_{demand_category}_demand"
            ] = planned_demands[
                demand_category
            ]

            row[
                f"realised_{demand_category}_demand"
            ] = realised_demands[
                demand_category
            ]

            row[
                f"unmet_{demand_category}_demand"
            ] = unmet_demands[
                demand_category
            ]

        results.append(
            row
        )

    return results