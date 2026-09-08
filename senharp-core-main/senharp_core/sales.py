"""Realised firm sales, revenues and operating profits."""

from .entities import Firm, Sector


def update_firm_sales_and_profits(
    firms: list[Firm],
    sector_market_results: (
        list[dict[str, float | str]]
    ),
) -> list[dict[str, float | str]]:
    """Realise sectoral sales and compute firm operating profits.

    Sectoral realised nominal sales equal the minimum of:

    - total nominal demand;
    - nominal value of available output.

    Sales are allocated among firms in proportion to the
    nominal value of their current output.

    Unsold output is recorded but is not yet carried forward
    as an inventory stock.
    """

    if sector_market_results is None:
        raise ValueError(
            "Sector market diagnostics must be computed "
            "before firm sales."
        )

    market_by_sector = {
        str(row["sector"]): row
        for row in sector_market_results
    }

    # Reset current-period transaction variables.
    for firm in firms:
        firm.sales_ratio = 0.0
        firm.sales_quantity = 0.0
        firm.unsold_output = max(
            0.0,
            firm.actual_output,
        )
        firm.revenue = 0.0
        firm.profits = 0.0

    results: list[
        dict[str, float | str]
    ] = []

    for sector in Sector:
        sector_name = sector.value

        if sector_name not in market_by_sector:
            raise KeyError(
                f"Missing market results for sector "
                f"{sector_name!r}."
            )

        sector_firms = [
            firm
            for firm in firms
            if (
                firm.active
                and firm.sector == sector
            )
        ]

        nominal_demand = max(
            0.0,
            float(
                market_by_sector[
                    sector_name
                ]["total_nominal_demand"]
            ),
        )

        nominal_supply = sum(
            max(
                0.0,
                firm.price,
            )
            * max(
                0.0,
                firm.actual_output,
            )
            for firm in sector_firms
        )

        realised_sales_value = min(
            nominal_demand,
            nominal_supply,
        )

        if nominal_supply > 0.0:
            sector_sales_ratio = (
                realised_sales_value
                / nominal_supply
            )
        else:
            sector_sales_ratio = 0.0

        sector_quantity_sold = 0.0
        sector_unsold_output = 0.0
        sector_revenue = 0.0
        sector_wage_bill = 0.0
        sector_interest_paid = 0.0
        sector_carbon_tax_paid = 0.0
        sector_profits = 0.0
        

        for firm in sector_firms:
            output = max(
                0.0,
                firm.actual_output,
            )

            price = max(
                0.0,
                firm.price,
            )

            firm.sales_ratio = (
                sector_sales_ratio
            )

            firm.sales_quantity = (
                sector_sales_ratio
                * output
            )

            firm.unsold_output = max(
                0.0,
                output
                - firm.sales_quantity,
            )

            firm.revenue = (
                price
                * firm.sales_quantity
            )

            # Interest is currently zero because the firm
            # interest-payment mechanism is not yet implemented.
            interest_paid = max(
                0.0,
                firm.interest_paid,
            )

            carbon_tax_paid = max(
                0.0,
                firm.carbon_tax_paid,
            )
            
            firm.profits = (
                firm.revenue
                - firm.wage_bill
                - interest_paid
                - carbon_tax_paid
            )

            sector_quantity_sold += (
                firm.sales_quantity
            )

            sector_unsold_output += (
                firm.unsold_output
            )

            sector_revenue += (
                firm.revenue
            )

            sector_wage_bill += (
                firm.wage_bill
            )

            sector_interest_paid += (
                interest_paid
            )

            sector_carbon_tax_paid += (
                carbon_tax_paid
            )

            sector_profits += (
                firm.profits
            )

        available_output = sum(
            max(
                0.0,
                firm.actual_output,
            )
            for firm in sector_firms
        )

        nominal_unmet_demand = max(
            0.0,
            nominal_demand
            - realised_sales_value,
        )

        nominal_unsold_supply = max(
            0.0,
            nominal_supply
            - realised_sales_value,
        )

        results.append(
            {
                "sector": sector_name,

                "nominal_demand": (
                    nominal_demand
                ),

                "nominal_supply": (
                    nominal_supply
                ),

                "realised_sales_value": (
                    realised_sales_value
                ),

                "sales_ratio": (
                    sector_sales_ratio
                ),

                "available_output": (
                    available_output
                ),

                "quantity_sold": (
                    sector_quantity_sold
                ),

                "unsold_output": (
                    sector_unsold_output
                ),

                "nominal_unmet_demand": (
                    nominal_unmet_demand
                ),

                "nominal_unsold_supply": (
                    nominal_unsold_supply
                ),

                "revenue": (
                    sector_revenue
                ),

                "wage_bill": (
                    sector_wage_bill
                ),

                "interest_paid": (
                    sector_interest_paid
                ),

                "carbon_tax_paid": (
                    sector_carbon_tax_paid
                ),

                "profits": (
                    sector_profits
                ),

                "sales_accounting_gap": (
                    realised_sales_value
                    - sector_revenue
                ),

                "output_accounting_gap": (
                    available_output
                    - sector_quantity_sold
                    - sector_unsold_output
                ),

                "profit_accounting_gap": (
                    sector_profits
                    - sector_revenue
                    + sector_wage_bill
                    + sector_interest_paid
                    + sector_carbon_tax_paid
                ),
            }
        )

    return results