from collections.abc import Iterable
from .entities import Household, PolicyState
from .parameters import Parameters

def is_election_period(period: int, params: Parameters) -> bool:
    return (period + 1) % params.election_interval == 0

def update_policy_after_election(households: Iterable[Household], policy: PolicyState, params: Parameters) -> float:
    """Bloc 5 — le résultat électoral détermine la politique à partir de t+1."""
    household_list = list(households)
    support_share = sum(h.vote for h in household_list) / len(household_list)
    policy.support_share = support_share
    policy.active = support_share >= params.election_threshold
    for household in household_list:
        household.previous_vote = household.vote
        household.previous_vote_probability = household.vote_probability
        household.needs_index_at_last_election = household.needs_index
    return support_share
