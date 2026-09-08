"""Productive-capacity calculations for SEN-HARP.

This module computes firm productivity and potential output.
Potential output represents productive capacity, not output
effectively validated by aggregate demand.
"""

import random

from .entities import Firm
from .parameters import Parameters
from .climate import split_lagged_climate_damage

def update_firm_productive_capacity(
    firm: Firm,
    params: Parameters,
    rng: random.Random,
    lagged_climate_damage: float = 0.0,
) -> None:
    """Update one firm's productivity and potential output.

    Public green capital remains government-owned but provides
    productive services to firms. These services contribute to
    productive capacity and to the effective green-capital share,
    without being recorded as private firm assets.

    Parameters
    ----------
    firm
        Firm whose productive capacity is updated.
    params
        Model parameters.
    rng
        Dedicated random generator for production shocks.
    lagged_climate_damage
        Climate damage inherited from the previous period.
    """

    if params.production_shock_min > params.production_shock_max:
        raise ValueError(
            "production_shock_min cannot exceed "
            "production_shock_max."
        )

    # Private capital must remain non-negative.
    if firm.total_capital < 0.0:
        raise ValueError(
            f"Firm {firm.firm_id} has negative total capital."
        )

    # Public green-capital services are productive services,
    # not liabilities or negative assets.
    if firm.public_green_capital_service < 0.0:
        raise ValueError(
            f"Firm {firm.firm_id} has negative public green "
            "capital services."
        )

    if not 0.0 <= lagged_climate_damage <= 1.0:
        raise ValueError(
            "lagged_climate_damage must be between zero and one."
        )

    # Productive capital includes private capital and the services
    # received from government-owned public green infrastructure.
    productive_capital = (
        firm.productive_total_capital
    )

    if productive_capital < 0.0:
        raise ValueError(
            f"Firm {firm.firm_id} has negative productive capital."
        )

    # As in the initial SEN-HARP model, productivity rises with
    # the green share of capital. Here, the relevant green share
    # includes services supplied by public green infrastructure.
    structural_productivity = (
        params.base_productivity
        + params.green_productivity_gain
        * firm.productive_green_capital_ratio
    )

    (
        productivity_damage_rate,
        _,
    ) = split_lagged_climate_damage(
        lagged_climate_damage=(
            lagged_climate_damage
        ),
        params=params,
    )

    climate_productivity_multiplier = max(
        0.0,
        1.0 - productivity_damage_rate,
    )

    firm.productivity = (
        structural_productivity
        * climate_productivity_multiplier
    )

    firm.production_shock = rng.uniform(
        params.production_shock_min,
        params.production_shock_max,
    )

    firm.potential_output = (
        productive_capital
        * firm.productivity
        * firm.production_shock
    )

    # The legacy full-capacity benchmark must use the same
    # productive-capital perimeter as potential output.
    firm.full_capacity_output = (
        params.full_capacity_ratio
        * productive_capital
    )

    # Actual output will later be determined by demand.
    firm.actual_output = 0.0

def update_productive_capacity(
    firms: list[Firm],
    params: Parameters,
    rng: random.Random,
    lagged_climate_damage: float = 0.0,
) -> None:
    """Update productive capacity for all active firms."""

    for firm in firms:
        if not firm.active:
            firm.productivity = 0.0
            firm.production_shock = 1.0
            firm.potential_output = 0.0
            firm.full_capacity_output = 0.0
            firm.actual_output = 0.0
            continue

        update_firm_productive_capacity(
            firm=firm,
            params=params,
            rng=rng,
            lagged_climate_damage=lagged_climate_damage,
        )

def update_actual_output_from_employment(
    firms: list[Firm],
    labor_productivity: float,
    reference_prices: dict[int, float] | None = None,
    real_labor_productivity: float | None = None,
    work_time_factor: float = 1.0,
) -> None:
    """Determine output realised after labour matching.

    Actual output cannot exceed either planned output or the
    production capacity allowed by filled employment.
    """

    if labor_productivity <= 0.0:
        raise ValueError(
            "labor_productivity must be strictly positive."
        )
    if not 0.0 < work_time_factor <= 1.0:
        raise ValueError("work_time_factor must be in (0, 1].")

    use_fixed_price_productivity = bool(reference_prices)
    if use_fixed_price_productivity and (
        real_labor_productivity is None
        or real_labor_productivity <= 0.0
    ):
        raise ValueError(
            "A positive real_labor_productivity is required when "
            "reference prices are supplied."
        )

    for firm in firms:
        if not firm.active:
            firm.labor_constrained_output = 0.0
            firm.actual_output = 0.0
            continue

        if use_fixed_price_productivity:
            reference_price = float(
                reference_prices.get(firm.firm_id, 0.0)
            )
            if reference_price <= 0.0:
                raise ValueError(
                    "Every active firm requires a positive reference "
                    "price for fixed-price production."
                )
            firm.labor_constrained_output = (
                firm.total_employment
                * float(real_labor_productivity)
                * work_time_factor
                / reference_price
            )
        else:
            firm.labor_constrained_output = (
                firm.total_employment
                * labor_productivity
                * work_time_factor
            )

        firm.actual_output = min(
            firm.planned_output,
            firm.labor_constrained_output,
        )
