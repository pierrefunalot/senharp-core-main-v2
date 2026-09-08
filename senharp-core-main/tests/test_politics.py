import unittest
from senharp_core.entities import Household, PolicyState, Scenario
from senharp_core.parameters import Parameters
from senharp_core.perception import compute_political_perception
from senharp_core.politics import update_policy_after_election
from senharp_core.voting import compute_vote_probability

class PoliticsTests(unittest.TestCase):
    def test_loss_is_asymmetric(self):
        p=Parameters(); h=Household(1,"g",100.0,70.0,needs_index=95.0,needs_index_at_last_election=100.0)
        x=compute_political_perception(h,100.0,p)
        self.assertLess(x.loss_term,0.0)
        self.assertLess(x.relative_loss_term,0.0)

    def test_election_can_stop_policy(self):
        p=Parameters(); hs=[Household(i,"g",100.0,70.0,vote=0) for i in range(10)]
        policy=PolicyState(Scenario.CARBON_TAX,True)
        support=update_policy_after_election(hs,policy,p)
        self.assertEqual(support,0.0)
        self.assertFalse(policy.active)

    def test_adverse_results_are_attributed_to_incumbent_regime(self):
        p = Parameters()
        h = Household(
            1,
            "g",
            100.0,
            70.0,
            needs_index=95.0,
            needs_index_at_last_election=100.0,
        )
        perception = compute_political_perception(h, 100.0, p)

        probability_when_policy_active = compute_vote_probability(
            household=h,
            perception=perception,
            peer_support=0.50,
            incumbent_policy_active=True,
            params=p,
        )
        probability_when_policy_inactive = compute_vote_probability(
            household=h,
            perception=perception,
            peer_support=0.50,
            incumbent_policy_active=False,
            params=p,
        )

        self.assertLess(probability_when_policy_active, 0.50)
        self.assertGreater(probability_when_policy_inactive, 0.50)

if __name__ == "__main__": unittest.main()
