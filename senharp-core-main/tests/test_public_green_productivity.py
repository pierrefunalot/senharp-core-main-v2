import random

import pytest

from senharp_core.entities import Firm
from senharp_core.parameters import Parameters
from senharp_core.production import (
    update_firm_productive_capacity,
)
from types import SimpleNamespace

from senharp_core.public_green_productivity import (
    allocate_public_green_capital_services,
)
from senharp_core.labour_demand import (
    decompose_jobs_by_technology,
)
def test_public_green_capital_service_increases_capacity():
    params = Parameters(
        production_shock_min=1.0,
        production_shock_max=1.0,
    )

    firm_without_public_service = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    firm_with_public_service = Firm(
        firm_id=1,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    firm_without_public_service.public_green_capital_service = 0.0
    firm_with_public_service.public_green_capital_service = 50.0

    update_firm_productive_capacity(
        firm=firm_without_public_service,
        params=params,
        rng=random.Random(1),
        lagged_climate_damage=0.0,
    )

    update_firm_productive_capacity(
        firm=firm_with_public_service,
        params=params,
        rng=random.Random(1),
        lagged_climate_damage=0.0,
    )

    assert (
        firm_with_public_service.productive_total_capital
        == pytest.approx(150.0)
    )

    assert (
        firm_with_public_service.productive_green_capital_ratio
        == pytest.approx(50.0 / 150.0)
    )

    assert (
        firm_with_public_service.productivity
        > firm_without_public_service.productivity
    )

    assert (
        firm_with_public_service.potential_output
        > firm_without_public_service.potential_output
    )

    assert (
        firm_with_public_service.full_capacity_output
        > firm_without_public_service.full_capacity_output
    )

    # Public infrastructure must not alter private ownership.
    assert (
        firm_with_public_service.total_capital
        == pytest.approx(100.0)
    )

def test_public_green_capital_services_are_fully_allocated():
    params = Parameters(
        green_deal_public_capital_service_efficiency=0.50,
    )

    firm_1 = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    firm_2 = Firm(
        firm_id=1,
        bank_id=0,
        sector="technology",
        brown_capital=300.0,
        green_capital=0.0,
    )

    government = SimpleNamespace(
        public_green_capital=200.0,
    )

    results = allocate_public_green_capital_services(
        firms=[firm_1, firm_2],
        government=government,
        params=params,
    )

    # The service pool is 50% of the public stock.
    assert results[
        "public_green_capital_service_pool"
    ] == pytest.approx(100.0)

    # Allocation follows private-capital weights: 25% and 75%.
    assert (
        firm_1.public_green_capital_service
        == pytest.approx(25.0)
    )

    assert (
        firm_2.public_green_capital_service
        == pytest.approx(75.0)
    )

    assert results[
        "allocated_public_green_capital_service"
    ] == pytest.approx(100.0)

    assert results[
        "public_green_capital_allocation_gap"
    ] == pytest.approx(0.0)


def test_inactive_firm_receives_no_public_green_service():
    params = Parameters(
        green_deal_public_capital_service_efficiency=1.0,
    )

    active_firm = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    inactive_firm = Firm(
        firm_id=1,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    inactive_firm.active = False

    government = SimpleNamespace(
        public_green_capital=100.0,
    )

    allocate_public_green_capital_services(
        firms=[
            active_firm,
            inactive_firm,
        ],
        government=government,
        params=params,
    )

    assert (
        active_firm.public_green_capital_service
        == pytest.approx(100.0)
    )

    assert (
        inactive_firm.public_green_capital_service
        == pytest.approx(0.0)
    )


def test_zero_efficiency_resets_public_green_services():
    params = Parameters(
        green_deal_public_capital_service_efficiency=0.0,
    )

    firm = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    # Simulates a service inherited in the object from the
    # preceding model period.
    firm.public_green_capital_service = 50.0

    government = SimpleNamespace(
        public_green_capital=200.0,
    )

    results = allocate_public_green_capital_services(
        firms=[firm],
        government=government,
        params=params,
    )

    assert (
        firm.public_green_capital_service
        == pytest.approx(0.0)
    )

    assert results[
        "public_green_capital_service_pool"
    ] == pytest.approx(0.0)

    assert results[
        "public_green_capital_allocation_gap"
    ] == pytest.approx(0.0)

def test_public_green_capital_service_changes_job_composition():
    firm_without_service = Firm(
        firm_id=0,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    firm_with_service = Firm(
        firm_id=1,
        bank_id=0,
        sector="technology",
        brown_capital=100.0,
        green_capital=0.0,
    )

    firm_without_service.target_total_jobs = 10
    firm_with_service.target_total_jobs = 10

    firm_without_service.public_green_capital_service = 0.0
    firm_with_service.public_green_capital_service = 100.0

    decompose_jobs_by_technology(
        firms=[
            firm_without_service,
            firm_with_service,
        ]
    )

    # Without green capital or public service,
    # all jobs remain brown.
    assert (
        firm_without_service.target_green_jobs
        == 0
    )

    assert (
        firm_without_service.target_brown_jobs
        == 10
    )

    # The second firm has an effective green ratio of:
    # 100 / (100 + 100) = 0.5.
    assert (
        firm_with_service.target_green_jobs
        == 5
    )

    assert (
        firm_with_service.target_brown_jobs
        == 5
    )

    # Public green capital changes composition,
    # not the total number of jobs.
    for firm in [
        firm_without_service,
        firm_with_service,
    ]:
        assert (
            firm.target_green_jobs
            + firm.target_brown_jobs
            == firm.target_total_jobs
        )
import numpy as np
import pandas as pd

from senharp_core.model import Model

from senharp_core.entities import (
    PolicyMode,
    Scenario,
)

def test_collected_public_green_services_balance():
    params = Parameters(
        seed=1761,
        green_deal_public_capital_service_efficiency=1.0,
    )

    model = Model(
        params=params,
        scenario=Scenario.GREEN_DEAL,
        policy_mode=PolicyMode.FIXED,
        public_service_spending_growth=0.0,
    )

    for period in range(6):
        model.run_period(
            period=period
        )

    firms = pd.DataFrame(
        model.collector.firm_rows
    )

    government = pd.DataFrame(
        model.collector.government_rows
    )

    required_firm_columns = {
        "public_green_capital_service",
        "productive_green_capital",
        "productive_total_capital",
        "productive_green_capital_ratio",
    }

    assert required_firm_columns.issubset(
        firms.columns
    )

    required_government_columns = {
        "public_green_capital_available_for_services",
        "public_green_capital_service_pool",
        "allocated_public_green_capital_service",
        "public_green_capital_allocation_gap",
    }

    assert required_government_columns.issubset(
        government.columns
    )

    services_by_period = (
        firms
        .groupby(
            "period",
            as_index=False,
        )[
            "public_green_capital_service"
        ]
        .sum()
        .rename(
            columns={
                "public_green_capital_service": (
                    "firm_service_sum"
                )
            }
        )
    )

    comparison = government.merge(
        services_by_period,
        on="period",
        how="left",
        validate="one_to_one",
    )

    assert np.allclose(
        comparison["firm_service_sum"],
        comparison[
            "allocated_public_green_capital_service"
        ],
        atol=1e-9,
    )

    assert np.allclose(
        comparison[
            "public_green_capital_allocation_gap"
        ],
        0.0,
        atol=1e-9,
    )

    assert np.allclose(
        comparison[
            "public_green_capital_service_pool"
        ],
        (
            comparison[
                "public_green_capital_available_for_services"
            ]
            * params
            .green_deal_public_capital_service_efficiency
        ),
        atol=1e-9,
    )

    # No inherited stock is available at the beginning
    # of the first period.
    assert comparison.loc[
        comparison["period"] == 0,
        "firm_service_sum",
    ].iloc[0] == pytest.approx(0.0)

    # Public investment delivered in earlier periods
    # eventually provides productive services.
    assert (
        comparison.loc[
            comparison["period"] >= 2,
            "firm_service_sum",
        ]
        > 0.0
    ).any()