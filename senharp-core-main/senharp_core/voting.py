import math, random
from .entities import Household
from .parameters import Parameters
from .perception import PoliticalPerception

def logistic(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)

def compute_vote_probability(
    household: Household,
    perception: PoliticalPerception,
    peer_support: float,
    incumbent_policy_active: bool,
    params: Parameters,
) -> float:
    """Bloc 4a — combine trajectoire, pertes, inertie et influence sociale."""
    inertia = household.previous_vote_probability - 0.50
    social = peer_support - 0.50
    material_assessment = (
        params.w_needs_change * perception.change_since_election
        + params.w_relative_position * perception.relative_position
        + params.w_loss * perception.loss_term
        + params.w_relative_loss * perception.relative_loss_term
    )
    attributed_material_assessment = (
        material_assessment
        if incumbent_policy_active
        else -material_assessment
    )
    latent = (
        params.vote_intercept
        + attributed_material_assessment
        + params.w_inertia * inertia
        + params.w_social * social
    )
    return logistic(latent)

def draw_vote(household: Household, probability: float, rng: random.Random) -> None:
    household.vote_probability = probability
    household.vote = int(rng.random() < probability)
