import random
from .entities import Household, PolicyState, Scenario
from .parameters import Parameters

def apply_policy_exposure(household: Household, policy: PolicyState, params: Parameters, rng: random.Random) -> None:
    """Bloc 1 — traduit la politique en revenu et coût privé des besoins."""
    income_growth = params.baseline_income_growth
    cost_growth = params.baseline_cost_growth
    transfer_rate = 0.0

    if policy.active:
        
        if policy.scenario == Scenario.CARBON_TAX:
        # The market-oriented package has no direct
        # household transfer.
        #
        # Carbon-price effects on households must pass
        # through explicit economic prices or taxes,
        # rather than through a compounded increase in
        # the household's base consumption cost.
            pass
        elif policy.scenario == Scenario.GREEN_DEAL:
        # Additional Green Deal instruments will be
        # implemented explicitly through government
        # expenditure and household economic accounts.
        #
        # The skeleton initially contains only the same
        # carbon-tax mechanism as the market package.
            pass
        elif policy.scenario == Scenario.POST_GROWTH:
        # Neutral post-growth skeleton.
        # Explicit instruments will be introduced progressively:
        # brown-credit controls, capital retirement,
        # basic income, universal basic services and sufficiency.
            pass

    income_growth += rng.gauss(0.0, params.idiosyncratic_income_sigma)
    cost_growth += rng.gauss(0.0, params.idiosyncratic_cost_sigma)

    household.disposable_income = max(1.0, household.disposable_income * (1.0 + income_growth + transfer_rate))
    household.base_consumption_cost = max(1.0, household.base_consumption_cost * (1.0 + cost_growth))
