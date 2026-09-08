"""Planned output and aggregate labour demand in SEN-HARP.

This preliminary module determines firms' total target employment. It does not yet allocate jobs by technology, skill, or household.
"""

import math

from .entities import Firm, Sector
from .parameters import Parameters

def get_labor_productivity_reference_utilization(
    sector: Sector,
    params: Parameters,
) -> float:
    """Return the reference utilisation used for calibration.

    These reference rates calibrate structural labour
    productivity. They are independent from the operational
    period-0 utilisation rates used to plan output.
    """

    reference_by_sector = {
        Sector.AGRICULTURE: (
            params
            .labor_productivity_reference_agriculture_utilization
        ),
        Sector.ENERGY: (
            params
            .labor_productivity_reference_energy_utilization
        ),
        Sector.HOUSING: (
            params
            .labor_productivity_reference_housing_utilization
        ),
        Sector.TRANSPORT: (
            params
            .labor_productivity_reference_transport_utilization
        ),
        Sector.INDUSTRY: (
            params
            .labor_productivity_reference_industry_utilization
        ),
        Sector.TECHNOLOGY: (
            params
            .labor_productivity_reference_technology_utilization
        ),
    }

    if sector not in reference_by_sector:
        raise KeyError(
            "No labour-productivity reference utilisation "
            f"defined for sector {sector!r}."
        )

    reference_utilisation = float(
        reference_by_sector[sector]
    )

    if not 0.0 <= reference_utilisation <= 1.0:
        raise ValueError(
            "Labour-productivity reference utilisation must "
            "be between zero and one: "
            f"{sector}={reference_utilisation}."
        )

    return reference_utilisation
    
def calibrate_labor_productivity(
    firms: list[Firm],
    params: Parameters,
) -> float:
    """Return the common factual structural labour productivity."""

    if params.calibrated_labor_productivity <= 0.0:
        raise ValueError("calibrated_labor_productivity must be positive.")
    if params.n_households <= 0 or params.labor_productivity_reference_households <= 0:
        raise ValueError("Household-agent counts must be positive.")

    return float(
        params.calibrated_labor_productivity
        * params.labor_productivity_reference_households
        / params.n_households
    )


def calibrate_real_labor_productivity(
    params: Parameters,
) -> float:
    """Return common productivity in fixed-price output per worker."""

    value = params.calibrated_real_labor_productivity
    if value <= 0.0:
        raise ValueError(
            "calibrated_real_labor_productivity must be positive."
        )
    if (
        params.n_households <= 0
        or params.labor_productivity_reference_households <= 0
    ):
        raise ValueError("Household-agent counts must be positive.")

    return float(
        value
        * params.labor_productivity_reference_households
        / params.n_households
    )
    
def allocate_integer_job_targets(
    firms: list[Firm],
) -> None:
    """Convert continuous job targets into integer targets.

    The largest-remainder method preserves the rounded
    aggregate number of jobs.
    """

    active_firms = [
        firm
        for firm in firms
        if firm.active
    ]

    for firm in firms:
        firm.target_total_jobs = 0

    if not active_firms:
        return

    aggregate_continuous_target = sum(
        firm.desired_total_jobs
        for firm in active_firms
    )

    aggregate_integer_target = round(
        aggregate_continuous_target
    )

    allocated_jobs = 0
    fractional_parts: list[
        tuple[float, int, Firm]
    ] = []

    for firm in active_firms:
        base_target = math.floor(
            firm.desired_total_jobs
        )

        firm.target_total_jobs = int(
            base_target
        )

        allocated_jobs += base_target

        fractional_part = (
            firm.desired_total_jobs
            - base_target
        )

        fractional_parts.append(
            (
                fractional_part,
                firm.firm_id,
                firm,
            )
        )

    jobs_remaining = (
        aggregate_integer_target
        - allocated_jobs
    )

    # Largest fractional remainder first.
    # firm_id provides deterministic tie-breaking.
    fractional_parts.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    for _, _, firm in fractional_parts[
        :jobs_remaining
    ]:
        firm.target_total_jobs += 1

def get_previous_sector_quantity_demand(
    previous_sector_market_results: (
        list[dict[str, float | str]] | None
    ),
) -> dict[str, float]:
    """Return previous quantity demand indexed by sector name."""

    if previous_sector_market_results is None:
        return {}

    demand_by_sector: dict[str, float] = {}

    for row in previous_sector_market_results:
        sector_name = str(
            row["sector"]
        )

        quantity_demand = float(
            row["total_quantity_demand"]
        )

        demand_by_sector[
            sector_name
        ] = max(
            0.0,
            quantity_demand,
        )

    return demand_by_sector

def get_initial_sector_capacity_utilization(
    sector: Sector,
    params: Parameters,
) -> float:
    """Return the period-0 capacity-utilisation target."""

    utilization_by_sector = {
        Sector.AGRICULTURE: (
            params
            .initial_agriculture_capacity_utilization
        ),
        Sector.ENERGY: (
            params
            .initial_energy_capacity_utilization
        ),
        Sector.HOUSING: (
            params
            .initial_housing_capacity_utilization
        ),
        Sector.TRANSPORT: (
            params
            .initial_transport_capacity_utilization
        ),
        Sector.INDUSTRY: (
            params
            .initial_industry_capacity_utilization
        ),
        Sector.TECHNOLOGY: (
            params
            .initial_technology_capacity_utilization
        ),
    }

    if sector not in utilization_by_sector:
        raise KeyError(
            "No initial capacity-utilisation parameter "
            f"defined for sector {sector!r}."
        )

    utilization = float(
        utilization_by_sector[sector]
    )

    if not 0.0 <= utilization <= 1.0:
        raise ValueError(
            "Initial sector capacity utilisation must be "
            f"between zero and one: {sector}={utilization}."
        )

    return utilization

def update_planned_output_and_job_targets(
    firms: list[Firm],
    labor_productivity: float,
    params: Parameters,
    period: int = 0,
    previous_sector_market_results: (
        list[dict[str, float | str]] | None
    ) = None,
    reference_prices: dict[int, float] | None = None,
    real_labor_productivity: float | None = None,
    work_time_factor: float = 1.0,
) -> None:
    """Plan output and derive integer job targets.

    At period zero, firms plan production using
    sector-specific initial capacity-utilisation rates.

    From period one onward, sectoral planned output adjusts
    gradually toward previous-period quantity demand, subject
    to the current productive-capacity constraint.
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

    adjustment_speed = (
        params.production_adjustment_speed
    )

    if not 0.0 <= adjustment_speed <= 1.0:
        raise ValueError(
            "production_adjustment_speed must be "
            "between zero and one."
        )

    
    previous_demand_by_sector = (
        get_previous_sector_quantity_demand(
            previous_sector_market_results=(
                previous_sector_market_results
            ),
        )
    )

    # Preserve the preceding production plan before updating it.
    for firm in firms:
        firm.previous_planned_output = max(
            0.0,
            firm.planned_output,
        )

        firm.expected_demand = 0.0
        firm.desired_output = 0.0
        firm.desired_total_jobs = 0.0
        firm.target_total_jobs = 0

    for sector in Sector:
        sector_firms = [
            firm
            for firm in firms
            if (
                firm.sector == sector
                and firm.active
            )
        ]

        sector_potential_output = sum(
            max(
                0.0,
                firm.potential_output,
            )
            for firm in sector_firms
        )

        if sector_potential_output <= 0.0:
            for firm in sector_firms:
                firm.expected_demand = 0.0
                firm.desired_output = 0.0
                firm.planned_output = 0.0

            continue

        if (
            period == 0
            or sector.value
            not in previous_demand_by_sector
        ):
            initial_utilisation = (
                get_initial_sector_capacity_utilization(
                    sector=sector,
                    params=params,
                )
            )

            sector_expected_demand = (
                initial_utilisation
                * sector_potential_output
            )

            sector_desired_output = (
                sector_expected_demand
            )

            sector_planned_output = (
                sector_desired_output
            )

        else:
            sector_expected_demand = (
                previous_demand_by_sector[
                    sector.value
                ]
            )

            sector_desired_output = min(
                sector_expected_demand,
                sector_potential_output,
            )

            previous_sector_planned_output = sum(
                firm.previous_planned_output
                for firm in sector_firms
            )

            sector_planned_output = (
                (
                    1.0
                    - adjustment_speed
                )
                * previous_sector_planned_output
                + adjustment_speed
                * sector_desired_output
            )

            sector_planned_output = min(
                sector_potential_output,
                max(
                    0.0,
                    sector_planned_output,
                ),
            )

        # Demand and output are allocated among firms according
        # to their share of current sectoral productive capacity.
        for firm in sector_firms:
            capacity_share = (
                max(
                    0.0,
                    firm.potential_output,
                )
                / sector_potential_output
            )

            firm.expected_demand = (
                sector_expected_demand
                * capacity_share
            )

            firm.desired_output = min(
                firm.expected_demand,
                max(
                    0.0,
                    firm.potential_output,
                ),
            )

            firm.planned_output = (
                sector_planned_output
                * capacity_share
            )

            if use_fixed_price_productivity:
                reference_price = float(
                    reference_prices.get(firm.firm_id, 0.0)
                )
                if reference_price <= 0.0:
                    raise ValueError(
                        "Every active firm requires a positive reference "
                        "price for fixed-price labour demand."
                    )
                firm.desired_total_jobs = (
                    firm.planned_output
                    * reference_price
                    / (
                        float(real_labor_productivity)
                        * work_time_factor
                    )
                )
            else:
                # Period 0 precedes price formation and retains the documented
                # initial physical calibration before explicit alignment.
                firm.desired_total_jobs = (
                    firm.planned_output
                    / (labor_productivity * work_time_factor)
                )

    raw_job_targets = [
        (
            firm.desired_total_jobs
            if firm.active
            else 0.0
        )
        for firm in firms
    ]

    aggregate_job_target = max(
        0,
        int(
            round(
                sum(raw_job_targets)
            )
        ),
    )

    integer_job_targets = (
        allocate_largest_remainder(
            raw_job_targets,
            aggregate_job_target,
        )
    )

    for firm, target_jobs in zip(
        firms,
        integer_job_targets,
    ):
        firm.target_total_jobs = (
            target_jobs
            if firm.active
            else 0
        )
        
def allocate_largest_remainder(
    desired_values: list[float],
    aggregate_target: int,
) -> list[int]:
    """Convert continuous allocations into integer allocations."""

    if aggregate_target < 0:
        raise ValueError(
            "aggregate_target cannot be negative."
        )

    if not desired_values:
        return []

    base_values = [
        math.floor(max(0.0, value))
        for value in desired_values
    ]

    allocated_total = sum(base_values)

    remaining = (
        aggregate_target
        - allocated_total
    )

    if remaining < 0:
        raise ValueError(
            "aggregate_target is smaller than "
            "the sum of floor allocations."
        )

    remainders = [
        (
            max(0.0, value)
            - math.floor(max(0.0, value)),
            index,
        )
        for index, value in enumerate(
            desired_values
        )
    ]

    remainders.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    integer_values = list(base_values)

    for _, index in remainders[:remaining]:
        integer_values[index] += 1

    return integer_values


def align_initial_job_targets(
    firms: list[Firm], params: Parameters
) -> None:
    """Rescale period-0 firm targets to the documented initial employment rate."""
    aggregate_target = round(
        params.n_households * params.target_initial_private_employment_rate
    )
    if not 0 <= aggregate_target <= params.n_households:
        raise ValueError("Initial private-employment target is outside population bounds.")
    current_total = sum(firm.target_total_jobs for firm in firms if firm.active)
    if current_total <= 0:
        raise ValueError("Positive firm job targets are required at initialization.")
    desired = [
        aggregate_target * firm.target_total_jobs / current_total if firm.active else 0.0
        for firm in firms
    ]
    allocations = allocate_largest_remainder(desired, aggregate_target)
    for firm, jobs in zip(firms, allocations):
        firm.target_total_jobs = jobs if firm.active else 0


def decompose_jobs_by_technology(
    firms: list[Firm],
) -> None:
    """Split total job targets between green and brown jobs."""

    active_firms = [
        firm
        for firm in firms
        if firm.active
    ]

    for firm in firms:
        firm.target_green_jobs = 0
        firm.target_brown_jobs = 0

    if not active_firms:
        return

    desired_green_jobs = [
        firm.target_total_jobs
        * firm.productive_green_capital_ratio
        for firm in active_firms
    ]

    aggregate_green_target = round(
        sum(desired_green_jobs)
    )

    green_allocations = (
        allocate_largest_remainder(
            desired_values=desired_green_jobs,
            aggregate_target=(
                aggregate_green_target
            ),
        )
    )

    for firm, green_jobs in zip(
        active_firms,
        green_allocations,
    ):
        # The green allocation cannot exceed
        # the firm's total job target.
        green_jobs = min(
            green_jobs,
            firm.target_total_jobs,
        )

        firm.target_green_jobs = green_jobs

        firm.target_brown_jobs = (
            firm.target_total_jobs
            - green_jobs
        )


def allocate_high_skill_jobs(
    firms: list[Firm],
    technology: str,
) -> None:
    """Allocate high-skilled jobs for one technology."""

    if technology not in {
        "green",
        "brown",
    }:
        raise ValueError(
            "technology must be 'green' or 'brown'."
        )

    active_firms = [
        firm
        for firm in firms
        if firm.active
    ]

    if technology == "green":
        technology_jobs = [
            firm.target_green_jobs
            for firm in active_firms
        ]
    else:
        technology_jobs = [
            firm.target_brown_jobs
            for firm in active_firms
        ]

    desired_high_skill_jobs = [
        job_count
        * firm.high_skill_job_share
        for firm, job_count in zip(
            active_firms,
            technology_jobs,
        )
    ]

    aggregate_high_skill_target = round(
        sum(desired_high_skill_jobs)
    )

    high_skill_allocations = (
        allocate_largest_remainder(
            desired_values=(
                desired_high_skill_jobs
            ),
            aggregate_target=(
                aggregate_high_skill_target
            ),
        )
    )

    for firm, total_jobs, high_skill_jobs in zip(
        active_firms,
        technology_jobs,
        high_skill_allocations,
    ):
        high_skill_jobs = min(
            high_skill_jobs,
            total_jobs,
        )

        low_skill_jobs = (
            total_jobs
            - high_skill_jobs
        )

        if technology == "green":
            firm.green_high_skill_demand = (
                high_skill_jobs
            )
            firm.green_low_skill_demand = (
                low_skill_jobs
            )
        else:
            firm.brown_high_skill_demand = (
                high_skill_jobs
            )
            firm.brown_low_skill_demand = (
                low_skill_jobs
            )


def update_job_composition(
    firms: list[Firm],
) -> None:
    """Split total jobs by technology and skill."""

    for firm in firms:
        firm.brown_low_skill_demand = 0
        firm.green_low_skill_demand = 0
        firm.brown_high_skill_demand = 0
        firm.green_high_skill_demand = 0

    decompose_jobs_by_technology(
        firms=firms,
    )

    allocate_high_skill_jobs(
        firms=firms,
        technology="green",
    )

    allocate_high_skill_jobs(
        firms=firms,
        technology="brown",
    )
