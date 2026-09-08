"""Minimal productive material-use accounting inherited from the factual model."""

from __future__ import annotations

from .entities import Firm, PolicyState, Scenario, Sector
from .parameters import Parameters


def compute_material_use(
    firms: list[Firm], policy: PolicyState, params: Parameters
) -> dict[str, float]:
    """Compute output-based material use without adding a depletion stock."""
    base = {
        Sector.AGRICULTURE: params.material_intensity_agriculture,
        Sector.ENERGY: params.material_intensity_energy,
        Sector.HOUSING: params.material_intensity_housing,
        Sector.TRANSPORT: params.material_intensity_transport,
        Sector.INDUSTRY: params.material_intensity_industry,
        Sector.TECHNOLOGY: params.material_intensity_technology,
    }
    post_growth = {
        Sector.AGRICULTURE: params.post_growth_material_multiplier_agriculture,
        Sector.ENERGY: params.post_growth_material_multiplier_energy,
        Sector.HOUSING: params.post_growth_material_multiplier_housing,
        Sector.TRANSPORT: params.post_growth_material_multiplier_transport,
        Sector.INDUSTRY: params.post_growth_material_multiplier_industry,
        Sector.TECHNOLOGY: params.post_growth_material_multiplier_technology,
    }
    active_pg = policy.active and policy.scenario == Scenario.POST_GROWTH
    by_sector = {sector: 0.0 for sector in Sector}
    for firm in firms:
        if not firm.active:
            continue
        multiplier = post_growth[firm.sector] if active_pg else 1.0
        by_sector[firm.sector] += max(0.0, firm.actual_output) * base[firm.sector] * multiplier
    result = {f"material_use_{sector.value}": value for sector, value in by_sector.items()}
    result["material_use"] = sum(by_sector.values())
    return result

