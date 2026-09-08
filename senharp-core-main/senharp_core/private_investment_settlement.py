"""Settlement of private investment after goods-market rationing."""

from .entities import Firm
from .parameters import Parameters


def compute_private_investment_delivery_ratio(
    planned: float,
    realised: float,
) -> float:
    """Return a bounded investment-delivery ratio."""

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
                "Realised private investment cannot be "
                "positive when planned investment is zero."
            )

        return 1.0

    return min(
        1.0,
        max(
            0.0,
            realised_value / planned_value,
        ),
    )


def validate_investment_supplier_shares(
    params: Parameters,
) -> None:
    """Validate brown and green investment supplier shares."""

    brown_shares = [
        params.brown_investment_housing_share,
        params.brown_investment_industry_share,
        params.brown_investment_technology_share,
    ]

    green_shares = [
        params.green_investment_housing_share,
        params.green_investment_industry_share,
        params.green_investment_technology_share,
    ]

    if any(
        share < 0.0 or share > 1.0
        for share in brown_shares + green_shares
    ):
        raise ValueError(
            "Investment supplier shares must be "
            "between zero and one."
        )

    if abs(
        sum(brown_shares) - 1.0
    ) > 1e-12:
        raise ValueError(
            "Brown investment supplier shares "
            "must sum to one."
        )

    if abs(
        sum(green_shares) - 1.0
    ) > 1e-12:
        raise ValueError(
            "Green investment supplier shares "
            "must sum to one."
        )


def apply_private_investment_market_settlement(
    firms: list[Firm],
    market_settlement_results: (
        list[dict[str, float | str]]
    ),
    params: Parameters,
) -> dict[str, float]:
    """Apply realised investment deliveries to firms.

    Investment and the associated newly granted credit are
    reduced proportionally when investment goods are rationed.

    Current brown and green investment fields become realised
    flows used in end-of-period capital accumulation.
    """

    if market_settlement_results is None:
        raise ValueError(
            "Market settlement results are required "
            "before private-investment settlement."
        )

    validate_investment_supplier_shares(
        params=params,
    )

    delivery_ratios_by_sector: dict[
        str,
        float,
    ] = {}

    planned_sector_investment = 0.0
    realised_sector_investment = 0.0
    unmet_sector_investment = 0.0

    for row in market_settlement_results:
        sector_name = str(
            row["sector"]
        )

        planned = max(
            0.0,
            float(
                row[
                    "planned_private_investment_demand"
                ]
            ),
        )

        realised = max(
            0.0,
            float(
                row[
                    "realised_private_investment_demand"
                ]
            ),
        )

        unmet = max(
            0.0,
            float(
                row[
                    "unmet_private_investment_demand"
                ]
            ),
        )

        delivery_ratios_by_sector[
            sector_name
        ] = (
            compute_private_investment_delivery_ratio(
                planned=planned,
                realised=realised,
            )
        )

        planned_sector_investment += planned
        realised_sector_investment += realised
        unmet_sector_investment += unmet

    for required_sector in [
        "housing",
        "industry",
        "technology",
    ]:
        if (
            required_sector
            not in delivery_ratios_by_sector
        ):
            raise KeyError(
                "Missing private-investment settlement "
                f"for sector {required_sector!r}."
            )

    housing_delivery_ratio = (
        delivery_ratios_by_sector[
            "housing"
        ]
    )

    industry_delivery_ratio = (
        delivery_ratios_by_sector[
            "industry"
        ]
    )

    technology_delivery_ratio = (
        delivery_ratios_by_sector[
            "technology"
        ]
    )

    brown_delivery_ratio = (
        params.brown_investment_housing_share
        * housing_delivery_ratio
        + params.brown_investment_industry_share
        * industry_delivery_ratio
        + params.brown_investment_technology_share
        * technology_delivery_ratio
    )

    green_delivery_ratio = (
        params.green_investment_housing_share
        * housing_delivery_ratio
        + params.green_investment_industry_share
        * industry_delivery_ratio
        + params.green_investment_technology_share
        * technology_delivery_ratio
    )

    total_planned_brown_investment = 0.0
    total_realised_brown_investment = 0.0
    total_unmet_brown_investment = 0.0

    total_planned_green_investment = 0.0
    total_realised_green_investment = 0.0
    total_unmet_green_investment = 0.0

    total_planned_brown_credit = 0.0
    total_realised_brown_credit = 0.0
    total_cancelled_brown_credit = 0.0

    total_planned_green_credit = 0.0
    total_realised_green_credit = 0.0
    total_cancelled_green_credit = 0.0

    for firm in firms:
        planned_brown_self_financing = max(
            0.0, firm.brown_self_financed_investment
        )
        planned_green_self_financing = max(
            0.0, firm.green_self_financed_investment
        )
        firm.planned_brown_investment = max(
            0.0,
            firm.brown_investment,
        )

        firm.planned_green_investment = max(
            0.0,
            firm.green_investment,
        )

        firm.planned_brown_loans_granted = max(
            0.0,
            firm.brown_loans_granted,
        )

        firm.planned_green_loans_granted = max(
            0.0,
            firm.green_loans_granted,
        )

        firm.brown_investment = (
            firm.planned_brown_investment
            * brown_delivery_ratio
        )

        firm.green_investment = (
            firm.planned_green_investment
            * green_delivery_ratio
        )

        firm.brown_self_financed_investment = (
            planned_brown_self_financing * brown_delivery_ratio
        )
        firm.green_self_financed_investment = (
            planned_green_self_financing * green_delivery_ratio
        )
        firm.retained_earnings += (
            planned_brown_self_financing
            - firm.brown_self_financed_investment
            + planned_green_self_financing
            - firm.green_self_financed_investment
        )

        firm.unmet_brown_investment = max(
            0.0,
            firm.planned_brown_investment
            - firm.brown_investment,
        )

        firm.unmet_green_investment = max(
            0.0,
            firm.planned_green_investment
            - firm.green_investment,
        )

        firm.brown_loans_granted = (
            firm.planned_brown_loans_granted
            * brown_delivery_ratio
        )

        firm.green_loans_granted = (
            firm.planned_green_loans_granted
            * green_delivery_ratio
        )

        firm.cancelled_brown_credit = max(
            0.0,
            firm.planned_brown_loans_granted
            - firm.brown_loans_granted,
        )

        firm.cancelled_green_credit = max(
            0.0,
            firm.planned_green_loans_granted
            - firm.green_loans_granted,
        )

        total_planned_brown_investment += (
            firm.planned_brown_investment
        )

        total_realised_brown_investment += (
            firm.brown_investment
        )

        total_unmet_brown_investment += (
            firm.unmet_brown_investment
        )

        total_planned_green_investment += (
            firm.planned_green_investment
        )

        total_realised_green_investment += (
            firm.green_investment
        )

        total_unmet_green_investment += (
            firm.unmet_green_investment
        )

        total_planned_brown_credit += (
            firm.planned_brown_loans_granted
        )

        total_realised_brown_credit += (
            firm.brown_loans_granted
        )

        total_cancelled_brown_credit += (
            firm.cancelled_brown_credit
        )

        total_planned_green_credit += (
            firm.planned_green_loans_granted
        )

        total_realised_green_credit += (
            firm.green_loans_granted
        )

        total_cancelled_green_credit += (
            firm.cancelled_green_credit
        )

    total_planned_firm_investment = (
        total_planned_brown_investment
        + total_planned_green_investment
    )

    total_realised_firm_investment = (
        total_realised_brown_investment
        + total_realised_green_investment
    )

    total_unmet_firm_investment = (
        total_unmet_brown_investment
        + total_unmet_green_investment
    )

    total_planned_credit = (
        total_planned_brown_credit
        + total_planned_green_credit
    )

    total_realised_credit = (
        total_realised_brown_credit
        + total_realised_green_credit
    )

    total_cancelled_credit = (
        total_cancelled_brown_credit
        + total_cancelled_green_credit
    )

    return {
        "industry_delivery_ratio": (
            industry_delivery_ratio
        ),

        "technology_delivery_ratio": (
            technology_delivery_ratio
        ),

        "brown_delivery_ratio": (
            brown_delivery_ratio
        ),

        "green_delivery_ratio": (
            green_delivery_ratio
        ),

        "planned_brown_investment": (
            total_planned_brown_investment
        ),

        "realised_brown_investment": (
            total_realised_brown_investment
        ),

        "unmet_brown_investment": (
            total_unmet_brown_investment
        ),

        "planned_green_investment": (
            total_planned_green_investment
        ),

        "realised_green_investment": (
            total_realised_green_investment
        ),

        "unmet_green_investment": (
            total_unmet_green_investment
        ),

        "total_planned_firm_investment": (
            total_planned_firm_investment
        ),

        "total_realised_firm_investment": (
            total_realised_firm_investment
        ),

        "total_unmet_firm_investment": (
            total_unmet_firm_investment
        ),

        "total_planned_credit": (
            total_planned_credit
        ),

        "total_realised_credit": (
            total_realised_credit
        ),

        "total_cancelled_credit": (
            total_cancelled_credit
        ),

        "planned_investment_settlement_gap": (
            total_planned_firm_investment
            - planned_sector_investment
        ),

        "realised_investment_settlement_gap": (
            total_realised_firm_investment
            - realised_sector_investment
        ),

        "unmet_investment_settlement_gap": (
            total_unmet_firm_investment
            - unmet_sector_investment
        ),

        "investment_balance_gap": (
            total_planned_firm_investment
            - total_realised_firm_investment
            - total_unmet_firm_investment
        ),

        "planned_credit_investment_gap": (
            total_planned_credit
            + sum(
                firm.brown_self_financed_investment
                / brown_delivery_ratio
                if brown_delivery_ratio > 0.0 else 0.0
                for firm in firms
            )
            + sum(
                firm.green_self_financed_investment
                / green_delivery_ratio
                if green_delivery_ratio > 0.0 else 0.0
                for firm in firms
            )
            - total_planned_firm_investment
        ),

        "realised_credit_investment_gap": (
            total_realised_credit
            + sum(
                firm.brown_self_financed_investment
                + firm.green_self_financed_investment
                for firm in firms
            )
            - total_realised_firm_investment
        ),

        "credit_cancellation_gap": (
            total_planned_credit
            - total_realised_credit
            - total_cancelled_credit
        ),
    }
