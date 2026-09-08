"""Cost-based firm pricing in SEN-HARP."""

from .entities import Firm
from .parameters import Parameters


def initialize_cost_based_prices(
    firms: list[Firm],
    params: Parameters,
) -> dict[str, float]:
    """Set firm prices as a mark-up over unit labour cost."""

    markup_rate = (
        params.initial_price_markup_rate
    )

    if markup_rate < 0.0:
        raise ValueError(
            "initial_price_markup_rate "
            "cannot be negative."
        )

    total_wage_bill = sum(
        firm.wage_bill
        for firm in firms
    )

    total_labor_feasible_output = sum(
        firm.labor_constrained_output
        for firm in firms
    )

    aggregate_unit_labor_cost = (
        total_wage_bill
        / total_labor_feasible_output
        if total_labor_feasible_output > 0.0
        else params.minimum_firm_price
    )

    for firm in firms:
        if (
            firm.labor_constrained_output > 0.0
            and firm.wage_bill > 0.0
        ):
            firm.unit_labor_cost = (
                firm.wage_bill
                / firm.labor_constrained_output
            )
        else:
            firm.unit_labor_cost = (
                aggregate_unit_labor_cost
            )

        firm.price_markup_rate = markup_rate

        firm.price = max(
            params.minimum_firm_price,
            firm.unit_labor_cost
            * (1.0 + markup_rate),
        )

    weighted_mean_price = (
        sum(
            firm.price
            * firm.labor_constrained_output
            for firm in firms
        )
        / total_labor_feasible_output
        if total_labor_feasible_output > 0.0
        else 0.0
    )

    return {
        "aggregate_unit_labor_cost": (
            aggregate_unit_labor_cost
        ),
        "weighted_mean_price": (
            weighted_mean_price
        ),
        "minimum_price": min(
            firm.price
            for firm in firms
        ),
        "maximum_price": max(
            firm.price
            for firm in firms
        ),
    }