import random

import pytest

from senharp_core.entities import (
    EmploymentStatus, Firm, Household, PolicyState, Scenario, Sector,
)
from senharp_core.inequality import gini
from senharp_core.job_guarantee import update_job_guarantee
from senharp_core.model import Model
from senharp_core.parameters import Parameters
from senharp_core.resources import compute_material_use


def household(identifier: int) -> Household:
    return Household(identifier, "rural_low_skill", 100.0, 70.0)


def test_gini_reference_cases():
    assert gini([1.0, 1.0, 1.0]) == pytest.approx(0.0)
    assert gini([0.0, 0.0, 3.0]) == pytest.approx(2.0 / 3.0)
    assert gini([]) == 0.0


def test_green_deal_job_guarantee_enrols_and_pays_minimum_wage():
    households = [household(i) for i in range(10)]
    params = Parameters(green_deal_job_guarantee_entry_rate=1.0)
    result = update_job_guarantee(
        households,
        PolicyState(Scenario.GREEN_DEAL, True),
        params,
        random.Random(1),
    )
    assert result["job_guarantee_enrolled"] == 10
    assert all(h.employment_status == EmploymentStatus.JOB_GUARANTEE for h in households)


def test_job_guarantee_is_inactive_outside_active_green_deal():
    worker = household(0)
    worker.employment_status = EmploymentStatus.JOB_GUARANTEE
    result = update_job_guarantee(
        [worker], PolicyState(Scenario.GREEN_DEAL, False), Parameters(), random.Random(1)
    )
    assert result == {"job_guarantee_released": 1, "job_guarantee_enrolled": 0}
    assert worker.employment_status == EmploymentStatus.UNEMPLOYED


def test_post_growth_reduces_material_intensity_without_carbon_tax():
    firm = Firm(0, Sector.HOUSING, 0, actual_output=100.0)
    params = Parameters()
    baseline = compute_material_use(
        [firm], PolicyState(Scenario.BASELINE, False), params
    )["material_use"]
    post_growth = compute_material_use(
        [firm], PolicyState(Scenario.POST_GROWTH, True), params
    )["material_use"]
    assert baseline == pytest.approx(100.0)
    assert post_growth == pytest.approx(60.0)


def test_green_deal_has_no_extra_indexation_and_post_growth_no_carbon_tax():
    green_deal = Model(
        Parameters(n_households=30, n_firms=12, n_banks=2),
        Scenario.GREEN_DEAL,
    )
    green_deal.run_period(0)
    wage_0 = green_deal.base_wage
    green_deal.run_period(1)
    assert green_deal.base_wage == pytest.approx(
        wage_0 * (1.0 + green_deal.params.nominal_wage_growth_rate)
    )

    post_growth = Model(
        Parameters(n_households=30, n_firms=12, n_banks=2),
        Scenario.POST_GROWTH,
    )
    post_growth.run_period(0)
    assert post_growth.government.carbon_tax_revenue == 0.0


def test_common_productivity_prevents_initial_employment_collapse():
    params = Parameters(seed=1761)
    target = round(params.n_households * params.target_initial_private_employment_rate)
    productivities = []
    for scenario in [Scenario.BASELINE, Scenario.CARBON_TAX, Scenario.GREEN_DEAL, Scenario.POST_GROWTH]:
        model = Model(params, scenario)
        model.run_period(0)
        assert model.current_labour_market_results["filled_jobs"] == target
        model.run_period(1)
        # Effective demand may legitimately raise employment above its
        # period-0 calibration target. The robustness condition is that
        # the transition to endogenous demand does not produce an
        # artificial employment collapse.
        assert model.current_labour_market_results["filled_jobs"] >= target - 3
        assert model.current_labour_market_results["filled_jobs"] <= params.n_households
        productivities.append(model.labor_productivity)
    assert len(set(productivities)) == 1
