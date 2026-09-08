import pytest

from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def build_model(
    scenario,
    policy_mode,
):
    return Model(
        params=Parameters(
            seed=1761,
        ),
        scenario=scenario,
        policy_mode=policy_mode,
        public_service_spending_growth=0.0,
    )


def test_carbon_tax_has_no_reduced_form_household_transfer_or_cost_growth():
    """The market package must not directly alter legacy income or base cost."""

    baseline = build_model(
        scenario=Scenario.BASELINE,
        policy_mode=PolicyMode.OFF,
    )

    carbon_tax_fixed = build_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    baseline.run_period(
        period=0,
    )

    carbon_tax_fixed.run_period(
        period=0,
    )

    assert len(baseline.households) == len(
        carbon_tax_fixed.households
    )

    for baseline_household, tax_household in zip(
        baseline.households,
        carbon_tax_fixed.households,
    ):
        assert (
            tax_household.household_id
            == baseline_household.household_id
        )

        assert (
            tax_household.disposable_income
            == pytest.approx(
                baseline_household.disposable_income,
                rel=1e-12,
                abs=1e-12,
            )
        )

        assert (
            tax_household.base_consumption_cost
            == pytest.approx(
                baseline_household.base_consumption_cost,
                rel=1e-12,
                abs=1e-12,
            )
        )
