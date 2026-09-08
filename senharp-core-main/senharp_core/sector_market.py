"""Sector-level household demand diagnostics in SEN-HARP."""

from .entities import Firm, Sector


def get_sector_nominal_household_demand(
    sector: Sector,
    sector_consumption_results: dict[str, float],
) -> float:
    """Return nominal household demand for one sector."""

    demand_keys = {
        Sector.AGRICULTURE: "agriculture_demand",
        Sector.ENERGY: "energy_demand",
        Sector.HOUSING: "housing_demand",
        Sector.TRANSPORT: "transport_demand",
        Sector.INDUSTRY: "industry_demand",
        Sector.TECHNOLOGY: "technology_demand",
    }

    return sector_consumption_results[
        demand_keys[sector]
    ]

def get_sector_nominal_investment_demand(
    sector: Sector,
    sector_investment_demand_results: dict[str, float],
) -> float:
    """Return nominal investment demand for one sector."""

    demand_keys = {
        Sector.AGRICULTURE: (
            "agriculture_investment_demand"
        ),
        Sector.ENERGY: (
            "energy_investment_demand"
        ),
        Sector.HOUSING: (
            "housing_investment_demand"
        ),
        Sector.TRANSPORT: (
            "transport_investment_demand"
        ),
        Sector.INDUSTRY: (
            "industry_investment_demand"
        ),
        Sector.TECHNOLOGY: (
            "technology_investment_demand"
        ),
    }

    return sector_investment_demand_results[
        demand_keys[sector]
    ]

def compute_sector_household_market_diagnostics(
    firms: list[Firm],
    sector_consumption_results: dict[str, float],
) -> list[dict[str, float | str]]:
    """Convert nominal household demand into quantity demand.

    This function is diagnostic only. It does not yet ration
    households, change firm production, or calculate revenues.
    """

    rows: list[
        dict[str, float | str]
    ] = []

    for sector in Sector:
        sector_firms = [
            firm
            for firm in firms
            if (
                firm.sector == sector
                and firm.active
            )
        ]

        nominal_household_demand = (
            get_sector_nominal_household_demand(
                sector=sector,
                sector_consumption_results=(
                    sector_consumption_results
                ),
            )
        )

        available_output = sum(
            firm.actual_output
            for firm in sector_firms
        )

        nominal_supply_value = sum(
            firm.price
            * firm.actual_output
            for firm in sector_firms
        )

        if available_output > 0.0:
            sector_price = (
                nominal_supply_value
                / available_output
            )
        else:
            positive_prices = [
                firm.price
                for firm in sector_firms
                if firm.price > 0.0
            ]

            sector_price = (
                sum(positive_prices)
                / len(positive_prices)
                if positive_prices
                else 0.0
            )

        if sector_price > 0.0:
            household_quantity_demand = (
                nominal_household_demand
                / sector_price
            )
        else:
            household_quantity_demand = 0.0

        if available_output > 0.0:
            household_demand_supply_ratio = (
                household_quantity_demand
                / available_output
            )
        else:
            household_demand_supply_ratio = 0.0

        quantity_excess_demand = max(
            0.0,
            household_quantity_demand
            - available_output,
        )

        potential_unsold_output = max(
            0.0,
            available_output
            - household_quantity_demand,
        )

        nominal_excess_demand = max(
            0.0,
            nominal_household_demand
            - nominal_supply_value,
        )

        rows.append(
            {
                "sector": sector.value,

                "sector_price": sector_price,

                "nominal_household_demand": (
                    nominal_household_demand
                ),

                "household_quantity_demand": (
                    household_quantity_demand
                ),

                "available_output": (
                    available_output
                ),

                "nominal_supply_value": (
                    nominal_supply_value
                ),

                "household_demand_supply_ratio": (
                    household_demand_supply_ratio
                ),

                "quantity_excess_demand": (
                    quantity_excess_demand
                ),

                "potential_unsold_output": (
                    potential_unsold_output
                ),

                "nominal_excess_demand": (
                    nominal_excess_demand
                ),
            }
        )
    return rows
def get_sector_nominal_government_demand(
    sector: Sector,
    sector_government_demand_results: dict[str, float],
) -> float:
    """Return nominal government demand for one sector."""

    demand_keys = {
        Sector.AGRICULTURE: (
            "agriculture_government_demand"
        ),
        Sector.ENERGY: (
            "energy_government_demand"
        ),
        Sector.HOUSING: (
            "housing_government_demand"
        ),
        Sector.TRANSPORT: (
            "transport_government_demand"
        ),
        Sector.INDUSTRY: (
            "industry_government_demand"
        ),
        Sector.TECHNOLOGY: (
            "technology_government_demand"
        ),
    }

    return sector_government_demand_results[
        demand_keys[sector]
    ]

def compute_sector_market_diagnostics(
    firms: list[Firm],
    sector_consumption_results: dict[str, float],
    sector_investment_demand_results: dict[str, float],
    sector_government_demand_results: dict[str, float],
) -> list[dict[str, float | str]]:
    """Combine household, investment and government demand."""

    if sector_consumption_results is None:
        raise ValueError(
            "Sectoral household consumption must be "
            "computed before market diagnostics."
        )

    if sector_investment_demand_results is None:
        raise ValueError(
            "Sectoral investment demand must be "
            "computed before market diagnostics."
        )

    if sector_government_demand_results is None:
        raise ValueError(
            "Sectoral government demand must be "
            "computed before market diagnostics."
        )

    rows: list[
        dict[str, float | str]
    ] = []

    for sector in Sector:
        sector_firms = [
            firm
            for firm in firms
            if (
                firm.sector == sector
                and firm.active
            )
        ]

        nominal_household_demand = (
            get_sector_nominal_household_demand(
                sector=sector,
                sector_consumption_results=(
                    sector_consumption_results
                ),
            )
        )

        nominal_investment_demand = (
            get_sector_nominal_investment_demand(
                sector=sector,
                sector_investment_demand_results=(
                    sector_investment_demand_results
                ),
            )
        )

        nominal_government_demand = (
            get_sector_nominal_government_demand(
                sector=sector,
                sector_government_demand_results=(
                    sector_government_demand_results
                ),
            )
        )

        total_nominal_demand = (
            nominal_household_demand
            + nominal_investment_demand
            + nominal_government_demand
        )

        available_output = sum(
            firm.actual_output
            for firm in sector_firms
        )

        nominal_supply_value = sum(
            firm.price
            * firm.actual_output
            for firm in sector_firms
        )

        if available_output > 0.0:
            sector_price = (
                nominal_supply_value
                / available_output
            )
        else:
            positive_prices = [
                firm.price
                for firm in sector_firms
                if firm.price > 0.0
            ]

            sector_price = (
                sum(positive_prices)
                / len(positive_prices)
                if positive_prices
                else 0.0
            )

        if sector_price > 0.0:
            household_quantity_demand = (
                nominal_household_demand
                / sector_price
            )

            investment_quantity_demand = (
                nominal_investment_demand
                / sector_price
            )

            government_quantity_demand = (
                nominal_government_demand
                / sector_price
            )
        else:
            household_quantity_demand = 0.0
            investment_quantity_demand = 0.0
            government_quantity_demand = 0.0

        total_quantity_demand = (
            household_quantity_demand
            + investment_quantity_demand
            + government_quantity_demand
        )

        household_demand_supply_ratio = (
            household_quantity_demand
            / available_output
            if available_output > 0.0
            else 0.0
        )

        investment_demand_supply_ratio = (
            investment_quantity_demand
            / available_output
            if available_output > 0.0
            else 0.0
        )

        government_demand_supply_ratio = (
            government_quantity_demand
            / available_output
            if available_output > 0.0
            else 0.0
        )

        total_demand_supply_ratio = (
            total_quantity_demand
            / available_output
            if available_output > 0.0
            else 0.0
        )

        quantity_excess_demand = max(
            0.0,
            total_quantity_demand
            - available_output,
        )

        potential_unsold_output = max(
            0.0,
            available_output
            - total_quantity_demand,
        )

        nominal_excess_demand = max(
            0.0,
            total_nominal_demand
            - nominal_supply_value,
        )

        potential_unsold_supply_value = max(
            0.0,
            nominal_supply_value
            - total_nominal_demand,
        )

        rows.append(
            {
                "sector": sector.value,
                "sector_price": sector_price,

                "nominal_household_demand": (
                    nominal_household_demand
                ),

                "nominal_investment_demand": (
                    nominal_investment_demand
                ),

                "nominal_government_demand": (
                    nominal_government_demand
                ),

                "total_nominal_demand": (
                    total_nominal_demand
                ),

                "household_quantity_demand": (
                    household_quantity_demand
                ),

                "investment_quantity_demand": (
                    investment_quantity_demand
                ),

                "government_quantity_demand": (
                    government_quantity_demand
                ),

                "total_quantity_demand": (
                    total_quantity_demand
                ),

                "available_output": (
                    available_output
                ),

                "nominal_supply_value": (
                    nominal_supply_value
                ),

                "household_demand_supply_ratio": (
                    household_demand_supply_ratio
                ),

                "investment_demand_supply_ratio": (
                    investment_demand_supply_ratio
                ),

                "government_demand_supply_ratio": (
                    government_demand_supply_ratio
                ),

                "total_demand_supply_ratio": (
                    total_demand_supply_ratio
                ),

                "quantity_excess_demand": (
                    quantity_excess_demand
                ),

                "potential_unsold_output": (
                    potential_unsold_output
                ),

                "nominal_excess_demand": (
                    nominal_excess_demand
                ),

                "potential_unsold_supply_value": (
                    potential_unsold_supply_value
                ),
            }
        )

    return rows

def get_sector_nominal_government_demand(
    sector: Sector,
    sector_government_demand_results: dict[str, float],
) -> float:
    """Return nominal government demand for one sector."""

    demand_keys = {
        Sector.AGRICULTURE: (
            "agriculture_government_demand"
        ),
        Sector.ENERGY: (
            "energy_government_demand"
        ),
        Sector.HOUSING: (
            "housing_government_demand"
        ),
        Sector.TRANSPORT: (
            "transport_government_demand"
        ),
        Sector.INDUSTRY: (
            "industry_government_demand"
        ),
        Sector.TECHNOLOGY: (
            "technology_government_demand"
        ),
    }

    return sector_government_demand_results[
        demand_keys[sector]
    ]