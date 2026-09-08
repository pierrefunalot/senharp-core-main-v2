"""Productive services supplied by public green capital."""

from .entities import Firm, Government
from .parameters import Parameters


def allocate_public_green_capital_services(
    firms: list[Firm],
    government: Government,
    params: Parameters,
) -> dict[str, float]:
    """Allocate public green-capital services among active firms.

    The government retains ownership of public green capital.
    Firms receive only productive services from that stock.

    Services are allocated in proportion to each active firm's
    private capital stock. If all active firms have zero private
    capital, services are allocated equally.
    """

    efficiency = (
        params.green_deal_public_capital_service_efficiency
    )

    if not 0.0 <= efficiency <= 1.0:
        raise ValueError(
            "green_deal_public_capital_service_efficiency "
            "must be between zero and one."
        )

    # Reset the current-period service before reallocating it.
    for firm in firms:
        firm.public_green_capital_service = 0.0

    active_firms = [
        firm
        for firm in firms
        if firm.active
    ]

    public_stock = max(
        0.0,
        government.public_green_capital,
    )

    service_pool = (
        efficiency
        * public_stock
    )

    if not active_firms or service_pool <= 0.0:
        return {
            "public_green_capital_stock": public_stock,
            "public_green_capital_service_efficiency": (
                efficiency
            ),
            "public_green_capital_service_pool": 0.0,
            "allocated_public_green_capital_service": 0.0,
            "public_green_capital_allocation_gap": 0.0,
        }

    aggregate_private_capital = sum(
        max(
            0.0,
            firm.total_capital,
        )
        for firm in active_firms
    )

    if aggregate_private_capital > 0.0:
        for firm in active_firms:
            capital_weight = (
                max(
                    0.0,
                    firm.total_capital,
                )
                / aggregate_private_capital
            )

            firm.public_green_capital_service = (
                service_pool
                * capital_weight
            )

    else:
        equal_service = (
            service_pool
            / len(active_firms)
        )

        for firm in active_firms:
            firm.public_green_capital_service = (
                equal_service
            )

    allocated_service = sum(
        firm.public_green_capital_service
        for firm in active_firms
    )

    return {
        "public_green_capital_stock": public_stock,
        "public_green_capital_service_efficiency": (
            efficiency
        ),
        "public_green_capital_service_pool": service_pool,
        "allocated_public_green_capital_service": (
            allocated_service
        ),
        "public_green_capital_allocation_gap": (
            service_pool
            - allocated_service
        ),
    }