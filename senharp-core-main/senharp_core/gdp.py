"""Market-GDP accounting for the SEN-HARP economy.

The current Core has no intermediate-input matrix.  The value of final sales
can therefore be used as a transparent measure of market GDP.  Unsold output
is excluded because inventories are not yet carried as a stock in the model.
"""

from .entities import Firm


def compute_market_gdp(
    firms: list[Firm],
    market_settlement_results: list[dict[str, float | str]],
    reference_prices: dict[int, float],
    previous_real_gdp: float | None,
) -> dict[str, float]:
    """Return nominal GDP, real GDP at period-0 prices and its deflator.

    ``reference_prices`` is populated the first time the function is called
    and then kept fixed for the remainder of the simulation.
    """

    active_firms = [firm for firm in firms if firm.active]

    for firm in active_firms:
        price = max(0.0, float(firm.price))
        if firm.firm_id not in reference_prices:
            reference_prices[firm.firm_id] = price

    nominal_sales = sum(
        max(0.0, float(firm.price))
        * max(0.0, float(firm.sales_quantity))
        for firm in active_firms
    )

    real_sales = sum(
        reference_prices[firm.firm_id]
        * max(0.0, float(firm.sales_quantity))
        for firm in active_firms
    )

    categories = {
        "household_consumption": (
            "realised_essential_household_demand",
            "realised_supplementary_household_demand",
        ),
        "private_investment": (
            "realised_private_investment_demand",
        ),
        "government_consumption": (
            "realised_current_government_demand",
        ),
        "public_investment": (
            "realised_capital_government_demand",
        ),
    }

    nominal_components = {
        name: sum(
            sum(max(0.0, float(row[key])) for key in keys)
            for row in market_settlement_results
        )
        for name, keys in categories.items()
    }

    firms_by_sector: dict[str, list[Firm]] = {}
    for firm in active_firms:
        firms_by_sector.setdefault(firm.sector.value, []).append(firm)

    real_components = {name: 0.0 for name in categories}
    for row in market_settlement_results:
        sector_name = str(row["sector"])
        sector_nominal = max(0.0, float(row["realised_total_demand"]))
        sector_real = sum(
            reference_prices[firm.firm_id]
            * max(0.0, float(firm.sales_quantity))
            for firm in firms_by_sector.get(sector_name, [])
        )
        if sector_nominal <= 0.0:
            continue
        for name, keys in categories.items():
            category_nominal = sum(
                max(0.0, float(row[key])) for key in keys
            )
            real_components[name] += (
                sector_real * category_nominal / sector_nominal
            )

    nominal_gdp = sum(nominal_components.values())
    real_gdp = sum(real_components.values())

    gdp_deflator = (
        100.0 * nominal_gdp / real_gdp
        if real_gdp > 0.0
        else 0.0
    )

    real_gdp_growth = (
        real_gdp / previous_real_gdp - 1.0
        if previous_real_gdp is not None
        and previous_real_gdp > 0.0
        else 0.0
    )

    revenue_identity_gap = nominal_gdp - sum(
        max(0.0, float(firm.revenue))
        for firm in active_firms
    )

    return {
        "nominal_household_consumption": nominal_components[
            "household_consumption"
        ],
        "nominal_private_investment": nominal_components[
            "private_investment"
        ],
        "nominal_government_consumption": nominal_components[
            "government_consumption"
        ],
        "nominal_public_investment": nominal_components[
            "public_investment"
        ],
        "real_household_consumption": real_components[
            "household_consumption"
        ],
        "real_private_investment": real_components[
            "private_investment"
        ],
        "real_government_consumption": real_components[
            "government_consumption"
        ],
        "real_public_investment": real_components[
            "public_investment"
        ],
        "nominal_gdp": nominal_gdp,
        "real_gdp": real_gdp,
        "gdp_deflator": gdp_deflator,
        "real_gdp_growth": real_gdp_growth,
        "gdp_revenue_identity_gap": revenue_identity_gap,
        "nominal_gdp_expenditure_identity_gap": (
            nominal_sales - nominal_gdp
        ),
        "real_gdp_expenditure_identity_gap": real_sales - real_gdp,
    }
