import random
from collections import defaultdict

from .collector import Collector
from .economy_initialization import initialize_economy
from .production import (
    update_actual_output_from_employment,
    update_productive_capacity,
)
from .income import (
    distribute_firm_dividends,
    calibrate_initial_base_wage,
    update_household_gross_incomes,
)
from .taxation import (
    update_household_income_tax,
)
from .consumption import (
    update_household_consumption,
)

from .household_banking import (
    assign_households_to_banks,
    update_household_bank_credit,
)
from .consumption_allocation import (
    allocate_household_consumption_by_sector,
    initialize_household_consumption_preferences,
)

from .pricing import (
    initialize_cost_based_prices,
)

from .sector_market import (
    compute_sector_market_diagnostics,
)

from .investment_demand import (
    compute_sector_investment_demand,
)

from .government_spending import (
    update_government_spending,
)

from .government_demand import (
    compute_sector_government_demand,
)

from .sales import (
    update_firm_sales_and_profits,
)

from .market_settlement import (
    compute_market_settlement,
)

from .household_settlement import (
    apply_household_market_settlement,
)

from .government_settlement import (
    apply_government_market_settlement,
)

from .private_investment_settlement import (
    apply_private_investment_market_settlement,
)

from .firm_banking import (
    update_bank_firm_loan_accounts,
)

from .firm_interest import (
    update_firm_interest_payments,
)

from .government_debt import (
    prepare_government_debt_service,
    close_government_debt_account,
)

from .public_debt_holders import (
    update_public_debt_holdings,
)

from .household_deposits import (
    update_bank_household_deposit_accounts,
)

from .entities import Household, PolicyMode, PolicyState, Scenario
from .exposure import apply_policy_exposure
from .needs_index import compute_needs_index_growth, update_needs_index
from .parameters import Parameters
from .perception import compute_political_perception
from .politics import is_election_period, update_policy_after_election
from .voting import compute_vote_probability, draw_vote
from .job_guarantee import enrol_job_guarantee, release_job_guarantee
from .resources import compute_material_use

from .banking import update_credit_conditions
from .capital_accumulation import (
    accumulate_capital_and_debt,
    apply_lagged_climate_capital_damage,
)
from .investment import compute_investment_decisions

from .labour_demand import (
    calibrate_labor_productivity,
    calibrate_real_labor_productivity,
    align_initial_job_targets,
    update_job_composition,
    update_planned_output_and_job_targets,
)

from .labour_matching import (
    initialize_labour_market,
    update_labour_market,
)

from .environment import update_environment

from .climate import (
    update_climate_emissions,
    update_climate_state,
)

from .public_green_investment import (
    plan_public_green_investment,
)

from .public_green_capital import (
    accumulate_public_green_capital,
)

from .public_green_productivity import (
    allocate_public_green_capital_services,
)

from .public_green_productivity import (
    allocate_public_green_capital_services,
)

from .basic_income import (
    apply_post_growth_basic_income,
)

from .basic_services import (
    prepare_household_basic_services_substitution,
    plan_post_growth_basic_services,
    settle_post_growth_basic_services,
)
from .household_carbon_tax import (
    apply_household_carbon_tax,
    distribute_green_deal_carbon_dividend,
)
from .gdp import compute_market_gdp

class Model:
    """One simulation SEN-HARP Core Political."""

    def __init__(
        self,
        params: Parameters,
        scenario: Scenario,
        public_service_spending_growth: float = 0.0,
        policy_mode: PolicyMode = PolicyMode.ENDOGENOUS,
    ) -> None:
        self.params = params
        # Economic and political random streams are separated
        # so that voting does not modify future economic shocks.
        self.rng_economy = random.Random(
            params.seed
        )
        self.rng_politics = random.Random(
            params.seed + 1_000_003
        )

       # Temporary compatibility alias:
       # all existing economic mechanisms continue to use
       # the exact same random sequence as in v0.3.
        self.rng = self.rng_economy
        
        self.period = 0

        self.public_service_spending_growth = (
            public_service_spending_growth
        )

        requested_policy_mode = PolicyMode(
            policy_mode
        )

        # The baseline never contains a transition package.
        if scenario == Scenario.BASELINE:
            self.policy_mode = PolicyMode.OFF
        else:
            self.policy_mode = requested_policy_mode

        initially_active = (
            scenario != Scenario.BASELINE
            and self.policy_mode
            in {
                PolicyMode.FIXED,
                PolicyMode.ENDOGENOUS,
            }
        )

        self.policy = PolicyState(
            scenario=scenario,
            active=initially_active,
        )

        # There is no electoral support measure when the
        # package is fixed or switched off exogenously.
        if self.policy_mode != PolicyMode.ENDOGENOUS:
            self.policy.support_share = float("nan")

        
        self.households = self._create_households()

        self.household_territory_distribution = (
            initialize_household_consumption_preferences(
                households=self.households,
                params=self.params,
            )
        )

        self.current_sector_consumption_results: (
            dict[str, float] | None
        ) = None
        
        self.reference_mean_income = (
            sum(
                household.disposable_income
                for household in self.households
            )
            / len(self.households)
        )

        self.base_wage: float | None = None

        self.current_income_results: (
            dict[str, float] | None
        ) = None

        (
            self.firms,
            self.banks,
            self.central_bank,
            self.government,
        ) = initialize_economy(
            params=self.params,
        )

        self.household_bank_distribution = (
            assign_households_to_banks(
                households=self.households,
                banks=self.banks,
                params=self.params,
            )
        )

        self.current_household_banking_results: (
            dict[str, float] | None
        ) = None
        
        self.current_tax_results: (
            dict[str, float] | None
        ) = None
        
        self.current_consumption_results: (
            dict[str, float] | None
        ) = None

        self.current_pricing_results: (
            dict[str, float] | None
        ) = None

        self.current_sector_market_results: (
            list[dict[str, float | str]] | None
        ) = None

        self.production_rng = random.Random(
            self.params.seed
            + self.params.production_seed_offset
        )

        self.labor_productivity = (
            calibrate_labor_productivity(
                firms=self.firms,
                params=self.params,
            )
        )
        self.real_labor_productivity = (
            calibrate_real_labor_productivity(
                params=self.params,
            )
        )

        self.labour_dynamics_rng = random.Random(
            self.params.seed
            + self.params.labour_dynamics_seed_offset
        )
        self.job_guarantee_rng = random.Random(
            self.params.seed + self.params.job_guarantee_seed_offset
        )
        
        self.current_labour_market_results = None
        self.labour_market_initialized = False
        self.initial_labour_matching_results = None

        self.current_sector_investment_demand_results: (
            dict[str, float] | None
        ) = None

        self.current_government_spending_results: (
            dict[str, float] | None
        ) = None

        self.current_sector_government_demand_results: (
            dict[str, float] | None
        ) = None

        self.current_sales_results: (
            list[dict[str, float | str]] | None
        ) = None

        self.current_market_settlement_results: (
            list[dict[str, float | str]] | None
        ) = None

        self.current_household_settlement_results: (
            dict[str, float] | None
        ) = None

        self.current_government_settlement_results: (
            dict[str, float] | None
        ) = None

        self.current_private_investment_settlement_results: (
            dict[str, float] | None
        ) = None

        self.current_firm_banking_results: (
            dict[str, float] | None
        ) = None

        self.current_firm_interest_results: (
            dict[str, float] | None
        ) = None

        self.current_government_debt_service_results: (
            dict[str, float] | None
        ) = None
            
        self.current_government_debt_results: (
            dict[str, float] | None
        ) = None

        self.current_public_debt_holder_results: (
            dict[str, float] | None
        ) = None

        self.current_household_deposit_results: (
            dict[str, float] | None
        ) = None

        self.current_public_green_investment_results: (
            dict[str, float] | None
        ) = None

        self.current_public_green_capital_results: (
            dict[str, float] | None
        ) = None

        self.current_public_green_productivity_results: (
            dict[str, float] | None
        ) = None

        self.current_basic_income_results: (
            dict[str, float | int] | None
        ) = None

        self.current_basic_services_planning_results: (
            dict[str, float | int] | None
        ) = None

        self.current_basic_services_settlement_results: (
            dict[str, float] | None
        ) = None
        self.current_job_guarantee_results = {
            "job_guarantee_released": 0,
            "job_guarantee_enrolled": 0,
        }
        self.current_material_results = {"material_use": 0.0}
        self.inflation_rate = self.params.structural_inflation_rate

        self.current_household_carbon_tax_results = None
        self.current_carbon_dividend_results = None
        self.current_gdp_results: dict[str, float] | None = None
        self.gdp_reference_prices: dict[int, float] = {}
        self.previous_real_gdp: float | None = None
        
        self.collector = Collector()

        self.total_emissions = 0.0
        self.pollution_stock = 0.0
        self.mean_environmental_damage = 0.0

        # =====================================================
        # BIOPHYSICAL AND CLIMATE STATE
        # =====================================================

        self.industrial_emissions = 0.0

        self.land_use_emissions = (
            self.params.initial_land_use_emissions
        )

        self.modelled_economy_emissions = 0.0
        self.rest_of_world_emissions = 0.0
        self.world_emissions = 0.0
        self.modelled_economy_world_emissions_share = 0.0

        # =====================================================
        # CARBON CYCLE AND CLIMATE STATE
        # =====================================================

        self.atmospheric_carbon = (
            self.params.initial_atmospheric_carbon
        )

        self.upper_ocean_carbon = (
            self.params.initial_upper_ocean_carbon
        )

        self.lower_ocean_carbon = (
            self.params.initial_lower_ocean_carbon
        )

        self.exogenous_forcing = (
            self.params.initial_exogenous_forcing
        )

        self.radiative_forcing = 0.0

        self.atmospheric_temperature = (
            self.params.initial_atmospheric_temperature
        )

        self.lower_ocean_temperature = (
            self.params.initial_lower_ocean_temperature
        )

        self.raw_climate_damage = 0.0
        self.climate_damage = 0.0


    def _create_households(
        self,
    ) -> list[Household]:
        households: list[Household] = []

        for household_id in range(self.params.n_households):

            skill = (
                "high_skill"
                if self.rng.random() < 0.40
                else "low_skill"
            )

            territory = (
                "urban"
                if self.rng.random() < 0.70
                else "rural"
            )

            peer_group = f"{territory}_{skill}"

            income = self.rng.uniform(80.0, 160.0)
            base_cost = self.rng.uniform(55.0, 95.0)

            households.append(
                Household(
                    household_id=household_id,
                    peer_group=peer_group,
                    disposable_income=income,
                    base_consumption_cost=base_cost,

                    energy_exposure=self.rng.uniform(0.20, 1.00),
                    brown_job_exposure=self.rng.uniform(0.00, 1.00),
                    green_job_access=self.rng.uniform(0.00, 1.00),
                    transfer_weight=self.rng.uniform(0.00, 1.00),
                    socialized_service_access=self.rng.uniform(0.00, 1.00),

                    transport_cost=self.rng.uniform(5.0, 20.0),
                    distance_to_public_services=self.rng.uniform(0.0, 1.0),
                )
            )

        return households

    def _peer_support_by_group(self) -> dict[str, float]:
        probabilities: dict[str, list[float]] = defaultdict(list)

        for household in self.households:
            probabilities[household.peer_group].append(
                household.previous_vote_probability
            )

        return {
            group: sum(values) / len(values)
            for group, values in probabilities.items()
        }

    def run_period(
        self,
        period: int,
    ) -> None:
               
        """RUN ONE PERIOD OF THE MODEL."""
        # =====================================================
        # POLICY REGIME APPLICABLE DURING THE CURRENT PERIOD
        # =====================================================

        if self.policy_mode == PolicyMode.OFF:
            self.policy.active = False

        elif self.policy_mode == PolicyMode.FIXED:
            self.policy.active = True

        # Under ENDOGENOUS mode, the state inherited from the
        # preceding election is retained.
        if (
            self.policy.active
            and self.policy.scenario == Scenario.POST_GROWTH
        ):
            self.policy.consecutive_active_periods += 1
        else:
            self.policy.consecutive_active_periods = 0
        # =====================================================
        # FIRM INVESTSMENT
        # =====================================================

        compute_investment_decisions(
            firms=self.firms,
            period=period,
            policy=self.policy,
            params=self.params,
        )

        # =====================================================
        # FIRM CARBON-TAX PAYMENTS
        # =====================================================

        self.government.firm_carbon_tax_revenue = sum(
            firm.carbon_tax_paid
            for firm in self.firms
        )
        self.government.taxes_firms = sum(
            firm.profit_tax_paid for firm in self.firms
        )
        self.government.household_carbon_tax_revenue = 0.0
        self.government.carbon_tax_revenue = (
            self.government.firm_carbon_tax_revenue
        )

        # =====================================================
        # CREDIT TO FIRMS
        # =====================================================

        update_credit_conditions(
            firms=self.firms,
            banks=self.banks,
            central_bank=self.central_bank,
            policy=self.policy,
            params=self.params,
        )

        # =====================================================
        # INTEREST ON COMPANIES’ OPENING DEBT
        # =====================================================

        self.current_firm_interest_results = (
            update_firm_interest_payments(
                firms=self.firms,
                period=period,
            )
        )

        # =========================================================
        # OPENING CLIMATE DAMAGE
        # =========================================================

        apply_lagged_climate_capital_damage(
            firms=self.firms,
            lagged_climate_damage=(
                self.climate_damage
            ),
            params=self.params,
        )

        # =====================================================
        # PRODUCTIVE SERVICES OF GREEN PUBLIC CAPITAL
        # =====================================================

        self.current_public_green_productivity_results = (
            allocate_public_green_capital_services(
                firms=self.firms,
                government=self.government,
                params=self.params,
            )
        )
        # =====================================================
        # PRODUCTIVE CAPACITY
        # =====================================================
        # Capital accumulation is performed at the end of
        # the period, after investment goods are delivered.
        update_productive_capacity(
            firms=self.firms,
            params=self.params,
            rng=self.production_rng,
            lagged_climate_damage=(
                self.climate_damage
            ),
        )

        # =====================================================
        # PLANNED PRODUCTION AND TOTAL LABOUR DEMAND
        
        # =====================================================

        work_time_reduction = 0.0
        if (
            self.policy.active
            and self.policy.scenario == Scenario.POST_GROWTH
        ):
            reduction = self.params.post_growth_work_time_reduction
            ramp_periods = self.params.post_growth_work_time_ramp_periods
            if not 0.0 <= reduction < 1.0:
                raise ValueError(
                    "post_growth_work_time_reduction must be in [0, 1)."
                )
            if ramp_periods <= 0:
                raise ValueError(
                    "post_growth_work_time_ramp_periods must be positive."
                )
            ramp = min(
                1.0,
                self.policy.consecutive_active_periods / ramp_periods,
            )
            work_time_reduction = reduction * ramp

        self.current_work_time_factor = 1.0 - work_time_reduction

        update_planned_output_and_job_targets(
            firms=self.firms,
            labor_productivity=(
                self.labor_productivity
            ),
            params=self.params,
            period=period,
            previous_sector_market_results=(
                self.current_sector_market_results
            ),
            reference_prices=self.gdp_reference_prices,
            real_labor_productivity=(
                self.real_labor_productivity
            ),
            work_time_factor=self.current_work_time_factor,
        )

        if period == 0:
            align_initial_job_targets(
                firms=self.firms,
                params=self.params,
            )

        # =====================================================
        # COMPOSITION OF JOBS
        # =====================================================

        update_job_composition(
            firms=self.firms,
        )

        # =====================================================
        # INITIALISATION OF THE LABOUR MARKET AT PERIOD 0
        # =====================================================

        released_from_job_guarantee = release_job_guarantee(self.households)

        if (
            period == 0
            and not self.labour_market_initialized
        ):
            self.initial_labour_matching_results = (
                initialize_labour_market(
                    households=self.households,
                    firms=self.firms,
                    params=self.params,
                )
            )

            self.current_labour_market_results = (
                self.initial_labour_matching_results
            )

            self.labour_market_initialized = True

        elif period > 0:
            self.current_labour_market_results = (
                update_labour_market(
                    households=self.households,
                    firms=self.firms,
                    rng=self.labour_dynamics_rng,
                )
            )

        self.current_job_guarantee_results = enrol_job_guarantee(
            households=self.households,
            policy=self.policy,
            params=self.params,
            rng=self.job_guarantee_rng,
        )
        self.current_job_guarantee_results["job_guarantee_released"] = (
            released_from_job_guarantee
        )

        # =====================================================
        # ACTUAL OUTPUT
        # =====================================================

        update_actual_output_from_employment(
            firms=self.firms,
            labor_productivity=(
                self.labor_productivity
            ),
            reference_prices=self.gdp_reference_prices,
            real_labor_productivity=(
                self.real_labor_productivity
            ),
            work_time_factor=self.current_work_time_factor,
        )
        self.current_material_results = compute_material_use(
            firms=self.firms,
            policy=self.policy,
            params=self.params,
        )
        
        # =====================================================
        # WAGES AND GROSS INCOME
        # =====================================================

        if self.base_wage is None:
            self.base_wage = (
                calibrate_initial_base_wage(
                    households=self.households,
                    params=self.params,
                    reference_mean_income=(
                        self.reference_mean_income
                    ),
                )
            )

        elif period > 0:
            wage_growth = self.params.nominal_wage_growth_rate
            if (
                self.params.green_deal_indexation_enabled
                and self.policy.active
                and self.policy.scenario == Scenario.GREEN_DEAL
            ):
                wage_growth += self.inflation_rate
            self.base_wage *= 1.0 + wage_growth

        self.current_income_results = (
            update_household_gross_incomes(
                households=self.households,
                firms=self.firms,
                base_wage=self.base_wage,
                params=self.params,
            )
        )
        total_dividends = distribute_firm_dividends(
            households=self.households,
            firms=self.firms,
        )
        self.current_income_results["total_dividend_income"] = total_dividends
        self.current_income_results["total_gross_income"] += total_dividends
        # =====================================================
        # UNIVERSAL BASIC INCOME
        # =====================================================

        self.current_basic_income_results = (
            apply_post_growth_basic_income(
                households=self.households,
                policy=self.policy,
                params=self.params,
                minimum_wage=(
                    self.current_income_results[
                        "minimum_wage"
                    ]
                ),
            )
        )

        basic_income_total = (
            self.current_basic_income_results[
                "total_basic_income"
            ]
        )

        self.current_income_results[
            "total_basic_income"
        ] = basic_income_total

        self.current_income_results[
            "total_transfers"
        ] = sum(
            household.transfer_income
            for household in self.households
        )

        self.current_income_results[
            "total_gross_income"
        ] = sum(
            household.gross_income
            for household in self.households
        )

        self.current_basic_services_substitution_results = (
            prepare_household_basic_services_substitution(
                households=self.households,
                policy=self.policy,
                params=self.params,
                minimum_wage=(
                    self.current_income_results["minimum_wage"]
                ),
            )
        )
        
        # =====================================================
        # COST-BASED PRICES
        # =====================================================

        self.current_pricing_results = (
            initialize_cost_based_prices(
                firms=self.firms,
                params=self.params,
            )
        )

        # =====================================================
        # INCOME TAX
        # =====================================================

        self.current_tax_results = (
            update_household_income_tax(
                households=self.households,
                params=self.params,
                policy=self.policy,
            )
        )

        self.government.taxes_households = (
            self.current_tax_results[
                "total_household_income_tax"
            ]
        )

        # =====================================================
        # PRE-TAX CONSUMPTION BASKET AND HOUSEHOLD CARBON TAX
        # =====================================================

        self.current_consumption_results = update_household_consumption(
            households=self.households,
            params=self.params,
        )
        self.current_sector_consumption_results = (
            allocate_household_consumption_by_sector(
                households=self.households,
                params=self.params,
            )
        )
        self.current_household_carbon_tax_results = (
            apply_household_carbon_tax(
                households=self.households,
                policy=self.policy,
                params=self.params,
            )
        )
        self.government.household_carbon_tax_revenue = float(
            self.current_household_carbon_tax_results[
                "household_carbon_tax_revenue"
            ]
        )
        self.government.carbon_tax_revenue = (
            self.government.firm_carbon_tax_revenue
            + self.government.household_carbon_tax_revenue
        )
        self.current_carbon_dividend_results = (
            distribute_green_deal_carbon_dividend(
                households=self.households,
                policy=self.policy,
                params=self.params,
                total_carbon_revenue=self.government.carbon_tax_revenue,
            )
        )
        self.government.carbon_dividend_spending = float(
            self.current_carbon_dividend_results[
                "distributed_carbon_dividend"
            ]
        )

        # Recompute final household demand after the tax and dividend.
        self.current_consumption_results = update_household_consumption(
            households=self.households,
            params=self.params,
            snapshot_opening_stocks=False,
        )
        self.current_sector_consumption_results = (
            allocate_household_consumption_by_sector(
                households=self.households,
                params=self.params,
            )
        )

        # =====================================================
        # PUBLIC EXPENDITURE AND PUBLIC PROCUREMENT BUDGET
        # =====================================================

        self.current_government_spending_results = (
            update_government_spending(
                government=self.government,
                households=self.households,
                params=self.params,
                period=period,
                firms=self.firms,
                purchase_growth_rate_override=(
                    self.params.post_growth_government_purchase_growth_rate
                    if (
                        self.policy.active
                        and self.policy.scenario == Scenario.POST_GROWTH
                    )
                    else self.params.government_purchase_growth_rate
                    + self.inflation_rate
                    if (
                        self.params.green_deal_indexation_enabled
                        and self.policy.active
                        and self.policy.scenario == Scenario.GREEN_DEAL
                    )
                    else None
                ),
            )
        )

        # =====================================================
        # UNIVERSAL BASIC SERVICES: PLANNING
        # =====================================================

        self.current_basic_services_planning_results = (
            plan_post_growth_basic_services(
                government=self.government,
                households=self.households,
                policy=self.policy,
                params=self.params,
                minimum_wage=(
                    self.current_income_results[
                        "minimum_wage"
                    ]
                ),
            )
        )

        # =====================================================
        # GREEN DEAL — ADDITIONAL PUBLIC GREEN INVESTMENT
        # =====================================================

        self.current_public_green_investment_results = (
            plan_public_green_investment(
                government=self.government,
                policy=self.policy,
                params=self.params,
                firms=self.firms,
                lagged_nominal_gdp=(
                    self.current_gdp_results["nominal_gdp"]
                    if self.current_gdp_results is not None
                    else None
                ),
            )
        )

        

        # =====================================================
        # INTEREST ON THE INITIAL PUBLIC DEBT
        # =====================================================

        self.current_government_debt_service_results = (
            prepare_government_debt_service(
                government=self.government,
                period=period,
            )
        )
        
        # =====================================================
        # HOUSEHOLD CONSUMPTION, SAVINGS AND DEBT
        # =====================================================

        # Household consumption was computed above so carbon pricing
        # and Green Deal recycling enter the current-period budget.
        
        
        # =====================================================
        # SECTORAL ALLOCATION OF CONSUMPTION
        # =====================================================

        # Sectoral household demand was recomputed after carbon pricing.
        
        # =====================================================
        # NOMINAL INVESTMENT DEMAND BY SECTOR
        # =====================================================

        self.current_sector_investment_demand_results = (
            compute_sector_investment_demand(
                firms=self.firms,
                params=self.params,
            )
        )

        # =====================================================
        # NOMINAL PUBLIC DEMAND BY SECTOR
        # =====================================================

        self.current_sector_government_demand_results = (
            compute_sector_government_demand(
                government=self.government,
                params=self.params,
            )
        )
        
        # =====================================================
        # CURRENT HOUSEHOLD DEMAND BY SECTOR
        # =====================================================

        self.current_sector_market_results = (
            compute_sector_market_diagnostics(
                firms=self.firms,
                sector_consumption_results=(
                    self.current_sector_consumption_results
                ),
                sector_investment_demand_results=(
                    self.current_sector_investment_demand_results
                ),
                sector_government_demand_results=(
                    self.current_sector_government_demand_results
                ),
            )
        )

        # =====================================================
        # PRIORITY SETTLEMENT OF THE MARKET
        # =====================================================

        self.current_market_settlement_results = (
            compute_market_settlement(
                sector_market_results=(
                    self.current_sector_market_results
                ),
                sector_consumption_results=(
                    self.current_sector_consumption_results
                ),
                sector_investment_demand_results=(
                    self.current_sector_investment_demand_results
                ),
                sector_government_demand_results=(
                    self.current_sector_government_demand_results
                ),
            )
        )

        # =====================================================
        # PRIVATE INVESTMENT ACTUALLY DELIVERED
        # =====================================================

        self.current_private_investment_settlement_results = (
            apply_private_investment_market_settlement(
                firms=self.firms,
                market_settlement_results=(
                    self.current_market_settlement_results
                ),
                params=self.params,
            )
        )

        # =====================================================
        # PUBLIC PROCUREMENT ACTUALLY DELIVERED
        # =====================================================

        self.current_government_settlement_results = (
            apply_government_market_settlement(
                government=self.government,
                market_settlement_results=(
                    self.current_market_settlement_results
                ),
            )
        )

        # =====================================================
        # UNIVERSAL BASIC SERVICES: SETTLEMENT
        # =====================================================

        self.current_basic_services_settlement_results = (
            settle_post_growth_basic_services(
                government=self.government,
                households=self.households,
                sector_government_demand_results=(
                    self.current_sector_government_demand_results
                ),
                market_settlement_results=(
                    self.current_market_settlement_results
                ),
            )
        )

        # =====================================================
        # ACCUMULATION OF GREEN PUBLIC CAPITAL
        # =====================================================

        self.current_public_green_capital_results = (
            accumulate_public_green_capital(
                government=self.government,
                period=period,
                params=self.params,
            )
        )

        # =====================================================
        # CLOSING PUBLIC DEBT STOCK
        # =====================================================

        self.current_government_debt_results = (
            close_government_debt_account(
                government=self.government,
            )
        )

        # =====================================================
        # HOLDERS OF PUBLIC DEBT SECURITIES
        # =====================================================

        self.current_public_debt_holder_results = (
            update_public_debt_holdings(
                government=self.government,
                banks=self.banks,
                central_bank=self.central_bank,
                params=self.params,
            )
        )

        # =====================================================
        # COLLECT PUBLIC ACCOUNTS AND GREEN CAPITAL
        # =====================================================

        self.collector.record_government(
            period=period,
            scenario=self.policy.scenario,
            policy_mode=self.policy_mode,
            policy_active_during_period=int(
                self.policy.active
            ),
            government=self.government,
            public_green_capital_results=(
                self.current_public_green_capital_results
            ),
            public_green_productivity_results=(
                self.current_public_green_productivity_results
            ),
        )

        # =====================================================
        # ACTUAL CONSUMPTION, SAVINGS AND HOUSEHOLD DEBT
        # =====================================================

        self.current_household_settlement_results = (
            apply_household_market_settlement(
                households=self.households,
                market_settlement_results=(
                    self.current_market_settlement_results
                ),
            )
        )

        # =====================================================
        # BANK RECORDS OF ACTUAL CREDIT USED
        # =====================================================

        self.current_household_banking_results = (
            update_household_bank_credit(
                households=self.households,
                banks=self.banks,
            )
        )

        # =====================================================
        # BANK DEPOSITS REPRESENTING HOUSEHOLD SAVINGS
        # =====================================================

        self.current_household_deposit_results = (
            update_bank_household_deposit_accounts(
                households=self.households,
                banks=self.banks,
                period=period,
            )
        )

        # =====================================================
        # SALES, REVENUE AND PROFITS
        # =====================================================

        self.current_sales_results = (
            update_firm_sales_and_profits(
                firms=self.firms,
                sector_market_results=(
                    self.current_sector_market_results
                ),
            )
        )

        # =====================================================
        # MARKET GDP AT CURRENT AND PERIOD-0 PRICES
        # =====================================================

        self.current_gdp_results = compute_market_gdp(
            firms=self.firms,
            market_settlement_results=(
                self.current_market_settlement_results
            ),
            reference_prices=self.gdp_reference_prices,
            previous_real_gdp=self.previous_real_gdp,
        )
        self.previous_real_gdp = self.current_gdp_results[
            "real_gdp"
        ]

        # =====================================================
        # END-OF-PERIOD ACCUMULATION
        # =====================================================
        #
        # Current production uses opening capital.
        # Investment delivered during the current period enters
        # closing capital and becomes productive next period.
        # =====================================================

        accumulate_capital_and_debt(
            firms=self.firms,
            period=period,
            policy=self.policy,
            params=self.params,
        )
         # =====================================================
        # BANK ASSETS CORRESPONDING TO CORPORATE DEBT
        # =====================================================

        self.current_firm_banking_results = (
            update_bank_firm_loan_accounts(
                firms=self.firms,
                banks=self.banks,
            )
        )
        # COLLECTOR
        self.collector.record_household_banking(
            period=period,
            scenario=self.policy.scenario,
            households=self.households,
            banks=self.banks,
            banking_results=(
                self.current_household_banking_results
            ),
        )
        
        self.collector.record_household_consumption(
            period=period,
            scenario=self.policy.scenario,
            households=self.households,
            consumption_results=(
                self.current_consumption_results
            ),
        )
        
        self.collector.record_household_taxation(
            period=period,
            scenario=self.policy.scenario,
            households=self.households,
            government=self.government,
            tax_results=self.current_tax_results,
        )
        
        self.collector.record_income(
            period=period,
            scenario=self.policy.scenario,
            households=self.households,
            firms=self.firms,
            income_results=(
                self.current_income_results
            ),
        )

        self.collector.record_labour_market(
            period=period,
            scenario=self.policy.scenario,
            households=self.households,
            firms=self.firms,
            labour_market_results=(
                self.current_labour_market_results
            ),
        )
        
        

                      
        # Policy changes economic conditions.
        for household in self.households:
            apply_policy_exposure(
                household=household,
                policy=self.policy,
                params=self.params,
                rng=self.rng,
            )
            
        # =====================================================
        # BIOPHYSICAL PRODUCTION EMISSIONS
        # =====================================================

        (
            self.industrial_emissions,
            self.land_use_emissions,
            self.modelled_economy_emissions,
            self.rest_of_world_emissions,
            self.world_emissions,
        ) = update_climate_emissions(
            firms=self.firms,
            period=period,
            previous_land_use_emissions=(
                self.land_use_emissions
            ),
            params=self.params,
        )

        (
            self.atmospheric_carbon,
            self.upper_ocean_carbon,
            self.lower_ocean_carbon,
            self.exogenous_forcing,
            self.radiative_forcing,
            self.atmospheric_temperature,
            self.lower_ocean_temperature,
            self.raw_climate_damage,
            self.climate_damage,
        ) = update_climate_state(
            period=period,

            world_emissions=(
                self.world_emissions
            ),

            previous_atmospheric_carbon=(
                self.atmospheric_carbon
            ),

            previous_upper_ocean_carbon=(
                self.upper_ocean_carbon
            ),

            previous_lower_ocean_carbon=(
                self.lower_ocean_carbon
            ),

            previous_exogenous_forcing=(
                self.exogenous_forcing
            ),

            previous_atmospheric_temperature=(
                self.atmospheric_temperature
            ),

            previous_lower_ocean_temperature=(
                self.lower_ocean_temperature
            ),

            params=self.params,
        )

        if self.world_emissions > 0.0:
            self.modelled_economy_world_emissions_share = (
                self.modelled_economy_emissions
                / self.world_emissions
            )
        else:
            self.modelled_economy_world_emissions_share = 0.0


         # Emissions, pollution and damages.
        (
            self.total_emissions,
            self.pollution_stock,
            self.mean_environmental_damage,
        ) = update_environment(
            households=self.households,
            policy=self.policy,
            previous_pollution_stock=(
                self.pollution_stock
            ),
            params=self.params,
        )

                
        # Calculation of NeedsIndex.
        mean_economic_income = (
            sum(
                household.economic_disposable_income
                for household in self.households
            )
            / len(self.households)
        )

        for household in self.households:
            growth = compute_needs_index_growth(
                household=household,
                mean_economic_disposable_income=(
                    mean_economic_income
                ),
                params=self.params,
                public_service_spending_growth=(
                    self.public_service_spending_growth
                ),
            )

            update_needs_index(
                household=household,
                growth_rate=growth,
                params=self.params,
            )
        # =====================================================
        # COLLECT FIRM PRODUCTION AND BIOPHYSICAL FLOWS
        # =====================================================

        self.collector.record_production(
            period=period,
            scenario=self.policy.scenario,
            firms=self.firms,
        )

        # =====================================================
        # PERCEPTION, VOTE AND POLITICAL DYNAMICS
        # =====================================================

        if self.policy_mode != PolicyMode.ENDOGENOUS:
         
    # No individual vote is drawn when the policy package
    # is fixed or exogenously switched off.
            for household in self.households:
                household.vote_probability = float("nan")
                household.vote = -1
                
            election = False
            
            policy_active_before = int(
                self.policy.active
            )
            policy_active_after = (
                policy_active_before
            )
            
            election_type = "not_applicable"

            if self.policy_mode == PolicyMode.FIXED:
                policy_transition = "policy_fixed_active"
            else:
                policy_transition = "policy_fixed_inactive"

        else:

            # Perception of loss and gains.
            mean_needs_index = (
                sum(
                    household.needs_index
                    for household in self.households
                )
                / len(self.households)
            )

            peer_support = self._peer_support_by_group()

            # BLOC 4 — Vote individuel.
            for household in self.households:
                perception = compute_political_perception(
                    household=household,
                    mean_needs_index=mean_needs_index,
                    params=self.params,
                )

                probability = compute_vote_probability(
                    household=household,
                    perception=perception,
                    peer_support=(
                        peer_support[
                            household.peer_group
                        ]
                    ),
                    incumbent_policy_active=(
                        self.policy.active
                    ),
                    params=self.params,
                )

                draw_vote(
                    household,
                    probability,
                    self.rng_politics,
                )

            # Election and political dynamics.
            election = is_election_period(
                period=period,
                params=self.params,
            )

            policy_active_before = int(
                self.policy.active
            )

            election_type = "no_election"
            policy_transition = "no_election"
            policy_active_after = (
                policy_active_before
            )

            if election:
                election_type = (
                    "continuation_vote"
                    if policy_active_before == 1
                    else "reactivation_vote"
                )

                update_policy_after_election(
                    households=self.households,
                    policy=self.policy,
                    params=self.params,
                )

                policy_active_after = int(
                    self.policy.active
                )

                transition_labels = {
                    (1, 1): "policy_maintained",
                    (1, 0): "policy_rejected",
                    (0, 1): "policy_reactivated",
                    (0, 0): (
                        "policy_remains_inactive"
                    ),
                }

                policy_transition = (
                    transition_labels[
                        (
                            policy_active_before,
                            policy_active_after,
                        )
                    ]
                )
            
        # Recording of results.
        self.collector.record_period(
            period=period,
            households=self.households,
            policy=self.policy,
            policy_mode=self.policy_mode.value,
            carbon_tax_revenue=(
                self.government.carbon_tax_revenue
            ),
            firm_carbon_tax_revenue=(
                self.government.firm_carbon_tax_revenue
            ),
            household_carbon_tax_revenue=(
                self.government.household_carbon_tax_revenue
            ),
            carbon_dividend_spending=(
                self.government.carbon_dividend_spending
            ),
            nominal_gdp=self.current_gdp_results["nominal_gdp"],
            real_gdp=self.current_gdp_results["real_gdp"],
            gdp_deflator=self.current_gdp_results["gdp_deflator"],
            real_gdp_growth=self.current_gdp_results["real_gdp_growth"],
            gdp_revenue_identity_gap=(
                self.current_gdp_results["gdp_revenue_identity_gap"]
            ),
            gdp_results=self.current_gdp_results,
            election=election,
            policy_active_before=policy_active_before,
            policy_active_after=policy_active_after,
            election_type=election_type,
            policy_transition=policy_transition,
            pollution_stock=self.pollution_stock,
            industrial_emissions=(
                self.industrial_emissions
            ),

            land_use_emissions=(
                self.land_use_emissions
            ),

            modelled_economy_emissions=(
                self.modelled_economy_emissions
            ),

            rest_of_world_emissions=(
                self.rest_of_world_emissions
            ),

            world_emissions=(
                self.world_emissions
            ),

            modelled_economy_world_emissions_share=(
                self.modelled_economy_world_emissions_share
            ),

            atmospheric_carbon=(
                self.atmospheric_carbon
            ),

            upper_ocean_carbon=(
                self.upper_ocean_carbon
            ),

            lower_ocean_carbon=(
                self.lower_ocean_carbon
            ),

            exogenous_forcing=(
                self.exogenous_forcing
            ),

            radiative_forcing=(
                self.radiative_forcing
            ),

            atmospheric_temperature=(
                self.atmospheric_temperature
            ),

            lower_ocean_temperature=(
                self.lower_ocean_temperature
            ),

            raw_climate_damage=(
                self.raw_climate_damage
            ),

            climate_damage=(
                self.climate_damage
            ),
            inflation_rate=self.inflation_rate,
            material_use=self.current_material_results["material_use"],
            labor_productivity=self.labor_productivity,
        )

    def run(self) -> Collector:
        """Runs all periods."""

        for period in range(
            self.params.n_periods
        ):
            self.period = period
            self.run_period(period)

        return self.collector
