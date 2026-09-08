import unittest

from senharp_core.entities import Household
from senharp_core.needs_index import (
    compute_needs_index_growth,
    update_needs_index,
)
from senharp_core.parameters import Parameters


class NeedsIndexTests(unittest.TestCase):

    def setUp(self):
        self.params = Parameters()

    def create_household(
        self,
        household_id,
        economic_income=100.0,
        base_consumption_cost=80.0,
        transport_cost=10.0,
        distance_to_public_services=0.5,
    ):
        """Create a household with consistent legacy and economic income."""

        household = Household(
            household_id=household_id,
            peer_group="g",
            disposable_income=economic_income,
            base_consumption_cost=base_consumption_cost,
            transport_cost=transport_cost,
            distance_to_public_services=(
                distance_to_public_services
            ),
        )

        household.economic_disposable_income = (
            economic_income
        )

        return household

    def test_higher_base_cost_reduces_growth(self):
        low_cost_household = self.create_household(
            household_id=1,
            economic_income=100.0,
            base_consumption_cost=50.0,
        )

        high_cost_household = self.create_household(
            household_id=2,
            economic_income=100.0,
            base_consumption_cost=120.0,
        )

        growth_low_cost = compute_needs_index_growth(
            household=low_cost_household,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.0,
        )

        growth_high_cost = compute_needs_index_growth(
            household=high_cost_household,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.0,
        )

        self.assertGreater(
            growth_low_cost,
            growth_high_cost,
        )

    def test_relative_income_component_is_zero_at_mean_income(self):
        household = self.create_household(
            household_id=1,
            economic_income=100.0,
        )

        compute_needs_index_growth(
            household=household,
            mean_economic_disposable_income=100.0,
            params=self.params,
        )

        self.assertAlmostEqual(
            household.relative_income_component,
            0.0,
        )

    def test_negative_growth_reduces_index(self):
        household = self.create_household(
            household_id=1,
            economic_income=40.0,
            base_consumption_cost=120.0,
        )

        previous_needs_index = household.needs_index

        growth = compute_needs_index_growth(
            household=household,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.0,
        )

        update_needs_index(
            household=household,
            growth_rate=growth,
            params=self.params,
        )

        self.assertLess(
            growth,
            0.0,
        )

        self.assertLess(
            household.needs_index,
            previous_needs_index,
        )

    def test_public_spending_growth_raises_needs_growth(
        self,
    ):
        household = self.create_household(
            household_id=1,
            economic_income=100.0,
            base_consumption_cost=80.0,
            transport_cost=10.0,
            distance_to_public_services=0.5,
        )

        growth_without_spending = (
            compute_needs_index_growth(
                household=household,
                mean_economic_disposable_income=100.0,
                params=self.params,
                public_service_spending_growth=0.0,
            )
        )

        growth_with_spending = (
            compute_needs_index_growth(
                household=household,
                mean_economic_disposable_income=100.0,
                params=self.params,
                public_service_spending_growth=0.03,
            )
        )

        self.assertGreater(
            growth_with_spending,
            growth_without_spending,
        )

    def test_transport_burden_reduces_needs_growth(
        self,
    ):
        low_transport = self.create_household(
            household_id=1,
            economic_income=100.0,
            base_consumption_cost=80.0,
            transport_cost=5.0,
            distance_to_public_services=0.5,
        )

        high_transport = self.create_household(
            household_id=2,
            economic_income=100.0,
            base_consumption_cost=80.0,
            transport_cost=25.0,
            distance_to_public_services=0.5,
        )

        growth_low = compute_needs_index_growth(
            household=low_transport,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.03,
        )

        growth_high = compute_needs_index_growth(
            household=high_transport,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.03,
        )

        self.assertGreater(
            growth_low,
            growth_high,
        )

    def test_distance_reduces_needs_growth(self):
        close_household = self.create_household(
            household_id=1,
            economic_income=100.0,
            base_consumption_cost=80.0,
            transport_cost=10.0,
            distance_to_public_services=0.1,
        )

        remote_household = self.create_household(
            household_id=2,
            economic_income=100.0,
            base_consumption_cost=80.0,
            transport_cost=10.0,
            distance_to_public_services=0.9,
        )

        growth_close = compute_needs_index_growth(
            household=close_household,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.03,
        )

        growth_remote = compute_needs_index_growth(
            household=remote_household,
            mean_economic_disposable_income=100.0,
            params=self.params,
            public_service_spending_growth=0.03,
        )

        self.assertGreater(
            growth_close,
            growth_remote,
        )


if __name__ == "__main__":
    unittest.main()
