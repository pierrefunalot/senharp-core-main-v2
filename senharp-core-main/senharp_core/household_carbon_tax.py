"""Household carbon pricing and Green Deal revenue recycling."""

from .entities import Household, PolicyState, Scenario
from .parameters import Parameters


def household_carbon_tax_is_active(policy: PolicyState) -> bool:
    return (
        policy.active
        and policy.scenario in {Scenario.CARBON_TAX, Scenario.GREEN_DEAL}
    )


def apply_household_carbon_tax(
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
) -> dict[str, float | int]:
    """Charge a carbon-weighted levy on planned household consumption.

    The levy is paid from current disposable income before consumption is
    recomputed. This makes the incidence explicit without compounding the
    legacy base-consumption-cost variable.
    """

    rate = params.household_carbon_tax_rate
    if not 0.0 <= rate <= 1.0:
        raise ValueError("household_carbon_tax_rate must be between 0 and 1.")

    weights = {
        "agriculture_consumption": params.household_carbon_weight_agriculture,
        "energy_consumption": params.household_carbon_weight_energy,
        "housing_consumption": params.household_carbon_weight_housing,
        "transport_consumption": params.household_carbon_weight_transport,
        "industry_consumption": params.household_carbon_weight_industry,
        "technology_consumption": params.household_carbon_weight_technology,
    }
    if any(weight < 0.0 for weight in weights.values()):
        raise ValueError("Household carbon weights cannot be negative.")

    active = household_carbon_tax_is_active(policy)
    for household in households:
        household.household_carbon_tax_base = 0.0
        household.household_carbon_tax_paid = 0.0
        household.carbon_dividend_income = 0.0
        if not active:
            continue
        tax_base = sum(
            max(0.0, float(getattr(household, field))) * weight
            for field, weight in weights.items()
        )
        tax = min(max(0.0, household.economic_disposable_income), rate * tax_base)
        household.household_carbon_tax_base = tax_base
        household.household_carbon_tax_paid = tax
        household.economic_disposable_income = max(
            0.0, household.economic_disposable_income - tax
        )

    total_base = sum(h.household_carbon_tax_base for h in households)
    total_tax = sum(h.household_carbon_tax_paid for h in households)
    return {
        "household_carbon_tax_active": int(active),
        "household_carbon_tax_base": total_base,
        "household_carbon_tax_revenue": total_tax,
        "household_carbon_tax_accounting_gap": total_tax - sum(
            h.household_carbon_tax_paid for h in households
        ),
    }


def distribute_green_deal_carbon_dividend(
    households: list[Household],
    policy: PolicyState,
    params: Parameters,
    total_carbon_revenue: float,
) -> dict[str, float | int]:
    """Return a share of carbon revenue with progressive income weights."""

    share = params.green_deal_carbon_dividend_share
    if not 0.0 <= share <= 1.0:
        raise ValueError("green_deal_carbon_dividend_share must be between 0 and 1.")
    active = policy.active and policy.scenario == Scenario.GREEN_DEAL
    budget = share * max(0.0, total_carbon_revenue) if active else 0.0
    for household in households:
        household.carbon_dividend_income = 0.0
    if budget > 0.0 and households:
        incomes = [max(0.0, h.economic_disposable_income) for h in households]
        mean_income = sum(incomes) / len(incomes)
        weights = [max(0.0, mean_income - income) for income in incomes]
        total_weight = sum(weights)
        if total_weight <= 0.0:
            weights = [1.0] * len(households)
            total_weight = float(len(households))
        for household, weight in zip(households, weights):
            dividend = budget * weight / total_weight
            household.carbon_dividend_income = dividend
            household.economic_disposable_income += dividend
    distributed = sum(h.carbon_dividend_income for h in households)
    return {
        "green_deal_carbon_dividend_active": int(active),
        "planned_carbon_dividend": budget,
        "distributed_carbon_dividend": distributed,
        "carbon_dividend_accounting_gap": budget - distributed,
    }
