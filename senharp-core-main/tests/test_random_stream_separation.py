import pytest

from senharp_core.entities import Scenario
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def economic_snapshot(model):
    """Return a compact snapshot of the economic state."""

    return (
        sum(
            firm.actual_output
            for firm in model.firms
        ),
        sum(
            firm.brown_capital
            for firm in model.firms
        ),
        sum(
            firm.green_capital
            for firm in model.firms
        ),
        sum(
            household.economic_disposable_income
            for household in model.households
        ),
        sum(
            household.needs_index
            for household in model.households
        ),
        model.industrial_emissions,
        model.climate_damage,
    )


def run_inactive_policy_trajectory(
    scenario,
    number_of_periods=6,
):
    """Run a scenario while forcing its policy inactive."""

    params = Parameters(
        seed=1761,
    )

    model = Model(
        params=params,
        scenario=scenario,
        public_service_spending_growth=0.0,
    )

    trajectory = []

    for period in range(number_of_periods):

        # No policy instrument is active during this period.
        model.policy.active = False

        model.run_period(
            period=period,
        )

        trajectory.append(
            economic_snapshot(model)
        )

    return trajectory


def test_inactive_policy_does_not_change_economic_trajectory():
    """Political draws must not alter economic random shocks."""

    baseline = run_inactive_policy_trajectory(
        Scenario.BASELINE
    )

    inactive_carbon_tax = (
        run_inactive_policy_trajectory(
            Scenario.CARBON_TAX
        )
    )

    assert len(baseline) == len(
        inactive_carbon_tax
    )

    for period, (
        baseline_snapshot,
        policy_snapshot,
    ) in enumerate(
        zip(
            baseline,
            inactive_carbon_tax,
        )
    ):
        assert policy_snapshot == pytest.approx(
            baseline_snapshot,
            rel=1e-12,
            abs=1e-12,
        ), (
            "Divergence économique alors que le package "
            f"est inactif à la période {period}."
        )
