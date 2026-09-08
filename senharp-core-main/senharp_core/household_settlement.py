"""Settlement of household consumption after sectoral rationing."""

from .entities import Household, Sector


def compute_fulfilment_ratio(
    planned: float,
    realised: float,
) -> float:
    """Return a bounded realised-to-planned demand ratio."""

    planned_value = max(
        0.0,
        planned,
    )

    realised_value = max(
        0.0,
        realised,
    )

    if planned_value <= 1e-12:
        if realised_value > 1e-8:
            raise ValueError(
                "Realised demand cannot be positive "
                "when planned demand is zero."
            )

        return 1.0

    return min(
        1.0,
        max(
            0.0,
            realised_value / planned_value,
        ),
    )


def build_household_fulfilment_ratios(
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
) -> dict[str, dict[str, float]]:
    """Extract essential and supplementary ratios by sector."""

    if market_settlement_results is None:
        raise ValueError(
            "Market settlement results are required."
        )

    ratios: dict[
        str,
        dict[str, float],
    ] = {}

    for row in market_settlement_results:
        sector_name = str(
            row["sector"]
        )

        ratios[sector_name] = {
            "essential": compute_fulfilment_ratio(
                planned=float(
                    row[
                        "planned_essential_household_demand"
                    ]
                ),
                realised=float(
                    row[
                        "realised_essential_household_demand"
                    ]
                ),
            ),

            "supplementary": compute_fulfilment_ratio(
                planned=float(
                    row[
                        "planned_supplementary_household_demand"
                    ]
                ),
                realised=float(
                    row[
                        "realised_supplementary_household_demand"
                    ]
                ),
            ),
        }

    missing_sectors = [
        sector.value
        for sector in Sector
        if sector.value not in ratios
    ]

    if missing_sectors:
        raise KeyError(
            "Missing household settlement ratios for: "
            + ", ".join(missing_sectors)
        )

    return ratios


def apply_household_market_settlement(
    households: list[Household],
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
) -> dict[str, float]:
    """Apply sectoral rationing to individual households.

    Within each sector and demand category, realised consumption
    is allocated proportionally across households.

    Unspent resources first cancel unnecessary current-period
    consumer credit. Any remaining refund increases savings.
    """

    fulfilment_ratios = (
        build_household_fulfilment_ratios(
            market_settlement_results=(
                market_settlement_results
            ),
        )
    )

    initial_total_savings = sum(
        household.savings
        for household in households
    )

    initial_total_new_debt = sum(
        household.new_household_debt
        for household in households
    )

    total_planned_essential = 0.0
    total_planned_supplementary = 0.0
    total_planned_consumption = 0.0

    total_realised_essential = 0.0
    total_realised_supplementary = 0.0
    total_realised_consumption = 0.0

    total_unmet_essential = 0.0
    total_unmet_supplementary = 0.0
    total_unmet_consumption = 0.0

    total_cancelled_credit = 0.0
    total_refund_to_savings = 0.0

    for household in households:
        household.planned_essential_consumption = max(
            0.0,
            household.essential_consumption,
        )

        household.planned_supplementary_consumption = max(
            0.0,
            household.supplementary_consumption,
        )

        household.planned_total_consumption = max(
            0.0,
            household.total_consumption,
        )

        initial_new_debt = max(
            0.0,
            household.new_household_debt,
        )

        realised_essential_total = 0.0
        realised_supplementary_total = 0.0

        for sector in Sector:
            sector_name = sector.value

            essential_field = (
                f"essential_{sector_name}_consumption"
            )

            supplementary_field = (
                f"supplementary_{sector_name}_consumption"
            )

            total_field = (
                f"{sector_name}_consumption"
            )

            planned_essential_sector = max(
                0.0,
                float(
                    getattr(
                        household,
                        essential_field,
                    )
                ),
            )

            planned_supplementary_sector = max(
                0.0,
                float(
                    getattr(
                        household,
                        supplementary_field,
                    )
                ),
            )

            realised_essential_sector = (
                planned_essential_sector
                * fulfilment_ratios[
                    sector_name
                ]["essential"]
            )

            realised_supplementary_sector = (
                planned_supplementary_sector
                * fulfilment_ratios[
                    sector_name
                ]["supplementary"]
            )

            setattr(
                household,
                essential_field,
                realised_essential_sector,
            )

            setattr(
                household,
                supplementary_field,
                realised_supplementary_sector,
            )

            setattr(
                household,
                total_field,
                realised_essential_sector
                + realised_supplementary_sector,
            )

            realised_essential_total += (
                realised_essential_sector
            )

            realised_supplementary_total += (
                realised_supplementary_sector
            )

        household.essential_consumption = (
            realised_essential_total
        )

        household.supplementary_consumption = (
            realised_supplementary_total
        )

        household.total_consumption = (
            realised_essential_total
            + realised_supplementary_total
        )

        household.unmet_essential_consumption = max(
            0.0,
            household.planned_essential_consumption
            - household.essential_consumption,
        )

        household.unmet_supplementary_consumption = max(
            0.0,
            household.planned_supplementary_consumption
            - household.supplementary_consumption,
        )

        household.unmet_total_consumption = max(
            0.0,
            household.planned_total_consumption
            - household.total_consumption,
        )

        # New credit is cancelled before any refund is added
        # to household savings.
        household.cancelled_household_credit = min(
            initial_new_debt,
            household.unmet_total_consumption,
        )

        household.new_household_debt = max(
            0.0,
            initial_new_debt
            - household.cancelled_household_credit,
        )

        household.household_debt = max(
            0.0,
            household.previous_household_debt
            + household.new_household_debt
            - household.household_debt_repayment,
        )

        household.settlement_refund_to_savings = max(
            0.0,
            household.unmet_total_consumption
            - household.cancelled_household_credit,
        )

        # Recompute the household budget identity using realised
        # consumption and revised current-period borrowing.
        household.savings = max(
            0.0,
            household.previous_savings
            + household.economic_disposable_income
            + household.new_household_debt
            - household.total_consumption
            - household.household_debt_repayment,
        )

        total_planned_essential += (
            household.planned_essential_consumption
        )

        total_planned_supplementary += (
            household.planned_supplementary_consumption
        )

        total_planned_consumption += (
            household.planned_total_consumption
        )

        total_realised_essential += (
            household.essential_consumption
        )

        total_realised_supplementary += (
            household.supplementary_consumption
        )

        total_realised_consumption += (
            household.total_consumption
        )

        total_unmet_essential += (
            household.unmet_essential_consumption
        )

        total_unmet_supplementary += (
            household.unmet_supplementary_consumption
        )

        total_unmet_consumption += (
            household.unmet_total_consumption
        )

        total_cancelled_credit += (
            household.cancelled_household_credit
        )

        total_refund_to_savings += (
            household.settlement_refund_to_savings
        )

    final_total_savings = sum(
        household.savings
        for household in households
    )

    final_total_new_debt = sum(
        household.new_household_debt
        for household in households
    )

    final_total_household_debt = sum(
        household.household_debt
        for household in households
    )

    household_accounting_gap = sum(
        household.previous_savings
        + household.economic_disposable_income
        + household.new_household_debt
        - household.total_consumption
        - household.household_debt_repayment
        - household.savings
        for household in households
    )

    settlement_planned_essential = sum(
        float(
            row[
                "planned_essential_household_demand"
            ]
        )
        for row in market_settlement_results
    )

    settlement_realised_essential = sum(
        float(
            row[
                "realised_essential_household_demand"
            ]
        )
        for row in market_settlement_results
    )

    settlement_planned_supplementary = sum(
        float(
            row[
                "planned_supplementary_household_demand"
            ]
        )
        for row in market_settlement_results
    )

    settlement_realised_supplementary = sum(
        float(
            row[
                "realised_supplementary_household_demand"
            ]
        )
        for row in market_settlement_results
    )

    return {
        "planned_essential_consumption": (
            total_planned_essential
        ),

        "realised_essential_consumption": (
            total_realised_essential
        ),

        "unmet_essential_consumption": (
            total_unmet_essential
        ),

        "planned_supplementary_consumption": (
            total_planned_supplementary
        ),

        "realised_supplementary_consumption": (
            total_realised_supplementary
        ),

        "unmet_supplementary_consumption": (
            total_unmet_supplementary
        ),

        "planned_total_consumption": (
            total_planned_consumption
        ),

        "realised_total_consumption": (
            total_realised_consumption
        ),

        "unmet_total_consumption": (
            total_unmet_consumption
        ),

        "initial_total_new_household_debt": (
            initial_total_new_debt
        ),

        "cancelled_household_credit": (
            total_cancelled_credit
        ),

        "final_total_new_household_debt": (
            final_total_new_debt
        ),

        "final_total_household_debt": (
            final_total_household_debt
        ),

        "initial_total_savings": (
            initial_total_savings
        ),

        "refund_to_savings": (
            total_refund_to_savings
        ),

        "final_total_savings": (
            final_total_savings
        ),

        "planned_essential_settlement_gap": (
            total_planned_essential
            - settlement_planned_essential
        ),

        "realised_essential_settlement_gap": (
            total_realised_essential
            - settlement_realised_essential
        ),

        "planned_supplementary_settlement_gap": (
            total_planned_supplementary
            - settlement_planned_supplementary
        ),

        "realised_supplementary_settlement_gap": (
            total_realised_supplementary
            - settlement_realised_supplementary
        ),

        "consumption_balance_gap": (
            total_planned_consumption
            - total_realised_consumption
            - total_unmet_consumption
        ),

        "credit_cancellation_gap": (
            initial_total_new_debt
            - total_cancelled_credit
            - final_total_new_debt
        ),

        "savings_refund_gap": (
            final_total_savings
            - initial_total_savings
            - total_refund_to_savings
        ),

        "household_accounting_gap": (
            household_accounting_gap
        ),
    }