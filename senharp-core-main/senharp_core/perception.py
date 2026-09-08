from dataclasses import dataclass
from .entities import Household
from .parameters import Parameters

@dataclass(frozen=True)
class PoliticalPerception:
    change_since_election: float
    relative_position: float
    loss_term: float
    relative_loss_term: float

def compute_political_perception(household: Household, mean_needs_index: float, params: Parameters) -> PoliticalPerception:
    """Bloc 3 — rend les pertes politiquement asymétriques."""
    change = household.needs_index - household.needs_index_at_last_election
    relative_position = household.needs_index - mean_needs_index
    return PoliticalPerception(
        change_since_election=change,
        relative_position=relative_position,
        loss_term=params.loss_aversion * min(0.0, change),
        relative_loss_term=params.loss_aversion * min(0.0, relative_position),
    )
