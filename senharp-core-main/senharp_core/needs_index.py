from .entities import Household
from .parameters import Parameters


def compute_public_service_component(
    household: Household,
    public_service_spending_growth: float,
    params: Parameters,
) -> float:
    """computes the component public services access.

    public_service_spending_growth doit être exprimé sous forme décimale :
    0.03 correspond à une croissance de 3 %.
    """

    if not params.needs_public_service_component_enabled:
        household.transport_cost_burden = 0.0
        household.public_service_component = 0.0
        household.basic_services_component = 0.0
        household.basic_services_coverage_change = 0.0
        return 0.0

    income = max(
        float(household.economic_disposable_income),
        1e-9,
    )

    transport_burden = household.transport_cost / income

    # La distance est supposée normalisée entre 0 et 1.
    distance = min(
        max(household.distance_to_public_services, 0.0),
        1.0,
    )

    basic_services_coverage = min(
        max(
            household.basic_services_coverage,
            0.0,
        ),
        1.0,
    )

    previous_basic_services_coverage = min(
        max(
            household.previous_basic_services_coverage,
            0.0,
        ),
        1.0,
    )

    basic_services_coverage_change = (
        basic_services_coverage
        - previous_basic_services_coverage
    )

    basic_services_component = (
        params.weight_basic_services_coverage
        * basic_services_coverage_change
    )

    public_service_component = (
        params.weight_public_spending_growth
        * public_service_spending_growth
         + basic_services_component
        - params.weight_transport_burden
        * transport_burden
        - params.weight_distance_to_services
        * distance
    )

    household.transport_cost_burden = transport_burden
    household.public_service_component = public_service_component
    household.basic_services_component = (
        basic_services_component
    )
    household.basic_services_coverage_change = (
        basic_services_coverage_change
    )

    household.basic_services_component = (
        basic_services_component
    )

    return public_service_component


def compute_needs_index_growth(
    household: Household,
    mean_economic_disposable_income: float,
    params: Parameters,
    public_service_spending_growth: float = 0.0,
) -> float:
    """Calcule le taux de croissance courant du NeedsIndex.

    Les composantes économiques utilisent le revenu disponible
    issu du bloc économique. L'ancien disposable_income reste
    disponible pour le module politique historique.
    """

    income = max(
        float(
            household.economic_disposable_income
        ),
        1e-9,
    )

    mean_income = max(
        float(
            mean_economic_disposable_income
        ),
        1e-9,
    )

    constrained_cost = (
        household.base_consumption_cost
        if household.constrained_consumption_cost is None
        else max(0.0, household.constrained_consumption_cost)
    )

    affordability_component = (
        params.alpha_affordability
        * (
            1.0
            - constrained_cost
            / income
        )
    )

    relative_income_component = (
        params.beta_relative_income
        * (
            income
            / mean_income
            - 1.0
        )
    )

    public_service_component = (
        compute_public_service_component(
            household=household,
            public_service_spending_growth=(
                public_service_spending_growth
            ),
            params=params,
        )
    )

    household.affordability_component = (
        affordability_component
    )

    household.relative_income_component = (
        relative_income_component
    )

    return (
        affordability_component
        + relative_income_component
        + public_service_component
    )

def update_needs_index(
    household: Household,
    growth_rate: float,
    params: Parameters,
) -> None:
    """Met à jour l'indice cumulé en base 100."""

    household.needs_index_growth = growth_rate

    household.needs_index = max(
        params.minimum_needs_index,
        household.needs_index * (1.0 + growth_rate),
    )
