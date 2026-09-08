from senharp_core.entities import (
    PolicyMode,
    Scenario,
)
from senharp_core.model import Model
from senharp_core.parameters import Parameters


def make_model(
    scenario,
    policy_mode=PolicyMode.ENDOGENOUS,
):
    return Model(
        params=Parameters(
            seed=1761,
        ),
        scenario=scenario,
        public_service_spending_growth=0.0,
        policy_mode=policy_mode,
    )


def test_baseline_is_always_off():
    model = make_model(
        scenario=Scenario.BASELINE,
        policy_mode=PolicyMode.FIXED,
    )

    assert model.policy_mode == PolicyMode.OFF
    assert model.policy.active is False


def test_off_mode_keeps_package_inactive():
    model = make_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.OFF,
    )

    # Try to activate the package manually.
    model.policy.active = True

    model.run_period(
        period=0,
    )

    assert model.policy.active is False

    macro_row = model.collector.macro_rows[-1]

    assert macro_row["policy_active_before"] == 0
    assert macro_row["policy_active_after"] == 0
    assert macro_row["election"] == 0
    assert (
        macro_row["policy_transition"]
        == "policy_fixed_inactive"
    )


def test_fixed_mode_keeps_package_active():
    model = make_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    # Try to deactivate the package manually.
    model.policy.active = False

    for period in range(6):
        model.run_period(
            period=period,
        )

    assert model.policy.active is True

    for macro_row in model.collector.macro_rows:
        assert macro_row[
            "policy_active_before"
        ] == 1

        assert macro_row[
            "policy_active_after"
        ] == 1

        assert macro_row["election"] == 0

        assert (
            macro_row["policy_transition"]
            == "policy_fixed_active"
        )


def test_nonbaseline_default_is_endogenous():
    model = make_model(
        scenario=Scenario.CARBON_TAX,
    )

    assert (
        model.policy_mode
        == PolicyMode.ENDOGENOUS
    )

    assert model.policy.active is True

def test_collector_records_policy_mode():
    baseline = make_model(
        scenario=Scenario.BASELINE,
        policy_mode=PolicyMode.FIXED,
    )

    fixed = make_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.FIXED,
    )

    endogenous = make_model(
        scenario=Scenario.CARBON_TAX,
        policy_mode=PolicyMode.ENDOGENOUS,
    )

    baseline.run_period(
        period=0,
    )

    fixed.run_period(
        period=0,
    )

    endogenous.run_period(
        period=0,
    )

    baseline_row = (
        baseline.collector.macro_rows[-1]
    )

    fixed_row = (
        fixed.collector.macro_rows[-1]
    )

    endogenous_row = (
        endogenous.collector.macro_rows[-1]
    )

    assert (
        baseline_row["policy_mode"]
        == "off"
    )

    assert (
        fixed_row["policy_mode"]
        == "fixed"
    )

    assert (
        endogenous_row["policy_mode"]
        == "endogenous"
    )
