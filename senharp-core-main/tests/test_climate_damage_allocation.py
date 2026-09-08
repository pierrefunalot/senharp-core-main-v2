
"""Tests for the allocation of climate damage in SEN-HARP.

The effective climate damage is allocated as follows:
- 70% to firm productivity;
- 30% to productive capital.

The damage calculated at the end of period t-1 affects
productivity and opening capital during period t.
"""

from collections import defaultdict

import pytest

from senharp_core.entities import Scenario
from senharp_core.model import Model
from senharp_core.parameters import Parameters


N_PERIODS = 26
TOLERANCE = 1e-8

PRODUCTIVITY_DAMAGE_SHARE = 0.70
CAPITAL_DAMAGE_SHARE = 0.30


def run_baseline(
    climate_damage_scale: float,
) -> Model:
    """Run a fresh baseline simulation from period 0 to 25."""

    params = Parameters(
        seed=1761,
        n_households=600,
        central_bank_public_debt_share=0.0,

        climate_damage_scale=(
            climate_damage_scale
        ),
        climate_productivity_damage_share=(
            PRODUCTIVITY_DAMAGE_SHARE
        ),
        climate_capital_damage_share=(
            CAPITAL_DAMAGE_SHARE
        ),

        initial_agriculture_capacity_utilization=1.00,
        initial_energy_capacity_utilization=0.33,
        initial_housing_capacity_utilization=1.00,
        initial_transport_capacity_utilization=0.33,
        initial_industry_capacity_utilization=0.05,
        initial_technology_capacity_utilization=0.10,
    )

    model = Model(
        params=params,
        scenario=Scenario.BASELINE,
        public_service_spending_growth=0.0,
    )

    for period in range(N_PERIODS):
        model.run_period(
            period=period,
        )

    return model


@pytest.fixture(scope="module")
def climate_cases() -> dict[str, Model]:
    """Run each climate case once for the whole test module."""

    return {
        "scale_0": run_baseline(
            climate_damage_scale=0.0,
        ),
        "scale_1": run_baseline(
            climate_damage_scale=1.0,
        ),
    }


def group_firm_rows_by_period(
    model: Model,
) -> dict[int, list[dict]]:
    """Group the collector's firm rows by period."""

    grouped_rows = defaultdict(list)

    for row in model.collector.firm_rows:
        grouped_rows[int(row["period"])].append(
            row
        )

    assert set(grouped_rows) == set(
        range(N_PERIODS)
    )

    return dict(grouped_rows)


def aggregate_field(
    rows: list[dict],
    field: str,
) -> float:
    """Sum one numeric field over firm rows."""

    return sum(
        float(row[field])
        for row in rows
    )


def aggregate_capital_and_output(
    model: Model,
) -> dict[int, dict[str, float]]:
    """Aggregate capital and output by period."""

    grouped_rows = group_firm_rows_by_period(
        model
    )

    aggregates = {}

    for period, rows in grouped_rows.items():
        aggregates[period] = {
            "closing_total_capital": (
                aggregate_field(
                    rows,
                    "brown_capital",
                )
                + aggregate_field(
                    rows,
                    "green_capital",
                )
            ),
            "potential_output": aggregate_field(
                rows,
                "potential_output",
            ),
            "actual_output": aggregate_field(
                rows,
                "actual_output",
            ),
            "climate_capital_loss": (
                aggregate_field(
                    rows,
                    "climate_capital_loss",
                )
            ),
        }

    return aggregates


def test_no_climate_capital_loss_at_period_zero(
    climate_cases: dict[str, Model],
) -> None:
    """No lagged climate damage must be applied at t=0."""

    for model in climate_cases.values():
        rows_by_period = (
            group_firm_rows_by_period(model)
        )

        loss_at_period_zero = aggregate_field(
            rows_by_period[0],
            "climate_capital_loss",
        )

        assert loss_at_period_zero == pytest.approx(
            0.0,
            abs=TOLERANCE,
        )


def test_positive_losses_after_period_zero(
    climate_cases: dict[str, Model],
) -> None:
    """Capital losses begin at t=1 only when damage is active."""

    model_scale_0 = climate_cases["scale_0"]
    model_scale_1 = climate_cases["scale_1"]

    rows_scale_0 = group_firm_rows_by_period(
        model_scale_0
    )

    rows_scale_1 = group_firm_rows_by_period(
        model_scale_1
    )

    # No capital destruction in the technical counterfactual.
    for period in range(N_PERIODS):
        total_loss_scale_0 = aggregate_field(
            rows_scale_0[period],
            "climate_capital_loss",
        )

        assert total_loss_scale_0 == pytest.approx(
            0.0,
            abs=TOLERANCE,
        )

    climate_damage_by_period = {
        int(row["period"]): float(
            row["climate_damage"]
        )
        for row in model_scale_1.collector.macro_rows
    }

    for period in range(1, N_PERIODS):
        rows = rows_scale_1[period]

        brown_loss = aggregate_field(
            rows,
            "climate_brown_capital_loss",
        )

        green_loss = aggregate_field(
            rows,
            "climate_green_capital_loss",
        )

        total_loss = aggregate_field(
            rows,
            "climate_capital_loss",
        )

        opening_total_capital = (
            aggregate_field(
                rows,
                "opening_brown_capital_before_climate_damage",
            )
            + aggregate_field(
                rows,
                "opening_green_capital_before_climate_damage",
            )
        )

        lagged_damage = (
            climate_damage_by_period[
                period - 1
            ]
        )

        expected_total_loss = (
            CAPITAL_DAMAGE_SHARE
            * lagged_damage
            * opening_total_capital
        )

        assert brown_loss > 0.0
        assert green_loss > 0.0
        assert total_loss > 0.0

        # Also verifies the 30% allocation and one-period lag.
        assert total_loss == pytest.approx(
            expected_total_loss,
            rel=1e-10,
            abs=TOLERANCE,
        )


def test_green_and_brown_capital_identities(
    climate_cases: dict[str, Model],
) -> None:
    """Closing capital must satisfy the accumulation identities."""

    model = climate_cases["scale_1"]

    tested_rows = 0

    for row in model.collector.firm_rows:
        period = int(row["period"])

        if period == 0:
            continue

        if int(row.get("active", 1)) != 1:
            continue

        expected_brown_capital = (
            float(
                row[
                    "opening_brown_capital_before_climate_damage"
                ]
            )
            - float(
                row[
                    "climate_brown_capital_loss"
                ]
            )
            - float(
                row["brown_depreciation"]
            )
            - float(
                row["brown_policy_retirement"]
            )
            + float(
                row["brown_investment"]
            )
        )

        expected_green_capital = (
            float(
                row[
                    "opening_green_capital_before_climate_damage"
                ]
            )
            - float(
                row[
                    "climate_green_capital_loss"
                ]
            )
            - float(
                row["green_depreciation"]
            )
            + float(
                row["green_investment"]
            )
        )

        expected_brown_capital = max(
            0.0,
            expected_brown_capital,
        )

        expected_green_capital = max(
            0.0,
            expected_green_capital,
        )

        assert float(
            row["brown_capital"]
        ) == pytest.approx(
            expected_brown_capital,
            rel=1e-10,
            abs=TOLERANCE,
        )

        assert float(
            row["green_capital"]
        ) == pytest.approx(
            expected_green_capital,
            rel=1e-10,
            abs=TOLERANCE,
        )

        tested_rows += 1

    assert tested_rows > 0


def test_active_damage_reduces_capital_and_capacity(
    climate_cases: dict[str, Model],
) -> None:
    """Active climate feedback must reduce capital and capacity."""

    aggregates_scale_0 = (
        aggregate_capital_and_output(
            climate_cases["scale_0"]
        )
    )

    aggregates_scale_1 = (
        aggregate_capital_and_output(
            climate_cases["scale_1"]
        )
    )

    # Both trajectories must be identical at t=0.
    assert aggregates_scale_1[0][
        "potential_output"
    ] == pytest.approx(
        aggregates_scale_0[0][
            "potential_output"
        ],
        rel=1e-10,
        abs=TOLERANCE,
    )

    assert aggregates_scale_1[0][
        "actual_output"
    ] == pytest.approx(
        aggregates_scale_0[0][
            "actual_output"
        ],
        rel=1e-10,
        abs=TOLERANCE,
    )

    final_period = N_PERIODS - 1

    # Persistent material losses lower the final capital stock.
    assert aggregates_scale_1[final_period][
        "closing_total_capital"
    ] < aggregates_scale_0[final_period][
        "closing_total_capital"
    ]

    # Productivity and capital damage lower productive capacity.
    assert aggregates_scale_1[final_period][
        "potential_output"
    ] < aggregates_scale_0[final_period][
        "potential_output"
    ]

    # Material climate losses must effectively occur after period 0.
    # Actual output need not fall when effective demand is binding and
    # the damaged economy still has sufficient spare productive capacity.
    assert any(
        aggregates_scale_1[period][
            "climate_capital_loss"
        ]
        > 0.0
        for period in range(
            1,
            N_PERIODS,
        )
    )
