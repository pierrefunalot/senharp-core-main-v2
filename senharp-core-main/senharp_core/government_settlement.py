"""Settlement of government purchases after sectoral rationing."""

from .entities import Government

def compute_public_green_investment_settlement(
    government: Government,
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
) -> dict[str, float]:
    """Settle public green investment through technology supply.

    Public green investment is included in the government's
    technology-sector capital demand. When this demand is
    rationed, ordinary and green public capital purchases are
    assumed to be delivered proportionally.
    """

    technology_rows = [
        row
        for row in market_settlement_results
        if str(
            row["sector"]
        ).lower() == "technology"
    ]

    if len(technology_rows) != 1:
        raise ValueError(
            "Exactly one technology-sector market-settlement "
            "row is required."
        )

    technology_row = technology_rows[0]

    planned_technology_capital = max(
        0.0,
        float(
            technology_row[
                "planned_capital_government_demand"
            ]
        ),
    )

    realised_technology_capital = max(
        0.0,
        float(
            technology_row[
                "realised_capital_government_demand"
            ]
        ),
    )

    planned_public_green_investment = max(
        0.0,
        government.planned_public_green_investment,
    )

    if (
        planned_public_green_investment
        > planned_technology_capital + 1e-8
    ):
        raise ValueError(
            "Planned public green investment cannot exceed "
            "planned technology-sector public capital demand."
        )

    if planned_technology_capital <= 1e-12:
        technology_delivery_ratio = 1.0
    else:
        technology_delivery_ratio = min(
            1.0,
            max(
                0.0,
                realised_technology_capital
                / planned_technology_capital,
            ),
        )

    realised_public_green_investment = (
        planned_public_green_investment
        * technology_delivery_ratio
    )

    unmet_public_green_investment = max(
        0.0,
        planned_public_green_investment
        - realised_public_green_investment,
    )

    government.realised_public_green_investment = (
        realised_public_green_investment
    )

    government.unmet_public_green_investment = (
        unmet_public_green_investment
    )

    return {
        "planned_public_green_investment": (
            planned_public_green_investment
        ),
        "realised_public_green_investment": (
            realised_public_green_investment
        ),
        "unmet_public_green_investment": (
            unmet_public_green_investment
        ),
        "planned_technology_capital_demand": (
            planned_technology_capital
        ),
        "realised_technology_capital_demand": (
            realised_technology_capital
        ),
        "technology_capital_delivery_ratio": (
            technology_delivery_ratio
        ),
        "public_green_investment_balance_gap": (
            planned_public_green_investment
            - realised_public_green_investment
            - unmet_public_green_investment
        ),
    }

def apply_government_market_settlement(
    government: Government,
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
) -> dict[str, float]:
    """Apply realised government purchases to public accounts.

    Transfers and public wages are not rationed because they
    are monetary payments to households.

    Only direct current and capital purchases are adjusted.
    """

    if market_settlement_results is None:
        raise ValueError(
            "Market settlement results are required "
            "before government settlement."
        )

    
    planned_current_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "planned_current_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    realised_current_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "realised_current_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    unmet_current_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "unmet_current_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    planned_capital_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "planned_capital_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    realised_capital_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "realised_capital_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    unmet_capital_purchases = sum(
        max(
            0.0,
            float(
                row[
                    "unmet_capital_government_demand"
                ]
            ),
        )
        for row in market_settlement_results
    )

    public_green_settlement = (
        compute_public_green_investment_settlement(
            government=government,
            market_settlement_results=(
                market_settlement_results
            ),
        )
    )

    planned_current_field_before = (
        government.planned_current_purchases
    )

    planned_capital_field_before = (
        government.planned_capital_purchases
    )

    planned_primary_deficit = (
        government.primary_deficit
    )

    government.planned_current_purchases = (
        planned_current_purchases
    )

    government.planned_capital_purchases = (
        planned_capital_purchases
    )

    government.realised_current_purchases = (
        realised_current_purchases
    )

    government.realised_capital_purchases = (
        realised_capital_purchases
    )

    government.unmet_current_purchases = (
        unmet_current_purchases
    )

    government.unmet_capital_purchases = (
        unmet_capital_purchases
    )

    # Existing purchase fields now represent realised flows.
    government.current_purchases = (
        realised_current_purchases
    )

    government.capital_purchases = (
        realised_capital_purchases
    )

    government.current_spending = (
        government.transfer_spending
        + government.public_wage_spending
        + government.current_purchases
    )

    government.capital_spending = (
        government.capital_purchases
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

    # Public debt is not updated here yet. Debt accumulation
    # will be introduced as a separate stock-flow mechanism.

    total_planned_purchases = (
        planned_current_purchases
        + planned_capital_purchases
    )

    total_realised_purchases = (
        realised_current_purchases
        + realised_capital_purchases
    )

    total_unmet_purchases = (
        unmet_current_purchases
        + unmet_capital_purchases
    )

    return {
        "planned_current_purchases": (
            planned_current_purchases
        ),

        "realised_current_purchases": (
            realised_current_purchases
        ),

        "unmet_current_purchases": (
            unmet_current_purchases
        ),

        "planned_capital_purchases": (
            planned_capital_purchases
        ),

        "realised_capital_purchases": (
            realised_capital_purchases
        ),

        "unmet_capital_purchases": (
            unmet_capital_purchases
        ),

        "total_planned_purchases": (
            total_planned_purchases
        ),

        "total_realised_purchases": (
            total_realised_purchases
        ),

        "total_unmet_purchases": (
            total_unmet_purchases
        ),

        "planned_primary_deficit": (
            planned_primary_deficit
        ),

        "realised_primary_deficit": (
            government.primary_deficit
        ),

        "deficit_reduction_from_rationing": (
            planned_primary_deficit
            - government.primary_deficit
        ),

        "planned_current_field_gap": (
            planned_current_field_before
            - planned_current_purchases
        ),

        "planned_capital_field_gap": (
            planned_capital_field_before
            - planned_capital_purchases
        ),

        "current_purchase_balance_gap": (
            planned_current_purchases
            - realised_current_purchases
            - unmet_current_purchases
        ),

        "capital_purchase_balance_gap": (
            planned_capital_purchases
            - realised_capital_purchases
            - unmet_capital_purchases
        ),

        "total_purchase_balance_gap": (
            total_planned_purchases
            - total_realised_purchases
            - total_unmet_purchases
        ),

        "deficit_adjustment_gap": (
            planned_primary_deficit
            - government.primary_deficit
            - total_unmet_purchases
        ),

        "government_deficit_accounting_gap": (
            government.deficit
            - government.primary_deficit
            - government.interest_payment
        ),
        "planned_public_green_investment": (
            public_green_settlement[
                "planned_public_green_investment"
                ]
        ),

        "realised_public_green_investment": (
            public_green_settlement[
                "realised_public_green_investment"
                ]
        ),

        "unmet_public_green_investment": (
            public_green_settlement[
                "unmet_public_green_investment"
                ]
        ),

        "technology_capital_delivery_ratio": (
            public_green_settlement[
                "technology_capital_delivery_ratio"
                ]
        ),

        "public_green_investment_balance_gap": (
            public_green_settlement[
                "public_green_investment_balance_gap"
                ]
        ),
    }