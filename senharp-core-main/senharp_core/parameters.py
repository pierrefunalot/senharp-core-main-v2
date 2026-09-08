from dataclasses import dataclass

@dataclass(frozen=True)
class Parameters:
    n_households: int = 600
    n_periods: int = 25
    
    # =========================================================
    # ECONOMIC STRUCTURE
    # =========================================================

    n_firms: int = 120
    n_banks: int = 10

    initial_green_capital_share: float = 0.05

    # Common stock-flow normalization. It raises the opening private
    # capital-to-GDP ratio from about 0.34 to about 4.3, so a 3% gross
    # investment rate represents roughly 13% of GDP, close to the EU
    # business-investment share. Capital productivity and capital-based
    # tax rates are inversely rescaled below to preserve real capacity
    # and the opening policy burden.
    initial_private_capital_scale: float = 12.5

    # Factual EU-27 calibration of opening firm loans.
    initial_green_loans_agriculture: float = 22.8
    initial_green_loans_energy: float = 99.5
    initial_green_loans_housing: float = 89.7
    initial_green_loans_transport: float = 50.5
    initial_green_loans_industry: float = 6.0
    initial_green_loans_technology: float = 1.9
    initial_green_loan_portfolio_share: float = 0.04

    # Independent random streams preserve political
    # reproducibility when economic agents are added.
    firm_seed_offset: int = 10_000
    bank_seed_offset: int = 20_000

    # Independent stream for household-bank assignment.
    household_bank_seed_offset: int = 80_000
    
    # =========================================================
    # PRODUCTION
    # =========================================================

    # Independent stream for period-by-period production shocks
    production_seed_offset: int = 30_000

    # Productivity associated with the productive capital stock
    base_productivity: float = 2.4
    green_productivity_gain: float = 1.6

    # Idiosyncratic production shock
    production_shock_min: float = 0.85
    production_shock_max: float = 1.15

    # Capacity benchmark used in the original model
    full_capacity_ratio: float = 0.80

    # =========================================================
    # DEMAND-BASED PRODUCTION PLANNING
    # =========================================================

    # Fraction of the gap between previous planned output
    # and desired output closed in each period.
    production_adjustment_speed: float = 0.25

    # =========================================================
    # LABOUR-MARKET SCALE
    # =========================================================

    # Initial share of productive capacity used before
    # effective demand is fully endogenised.
    initial_capacity_utilization: float = 0.80

    # =========================================================
    # INITIAL SECTOR CAPACITY UTILISATION
    # =========================================================

    # Provisional sector-specific calibration used only in
    # period 0. Subsequent periods use expected sector demand.
    initial_agriculture_capacity_utilization: float = 1.00
    initial_energy_capacity_utilization: float = 0.33
    initial_housing_capacity_utilization: float = 1.00
    initial_transport_capacity_utilization: float = 0.33
    initial_industry_capacity_utilization: float = 0.05
    initial_technology_capacity_utilization: float = 0.10

    # Target initial share of households employed by firms.
    target_initial_private_employment_rate: float = 0.90

    # Common structural productivity calibrated once on the seed-1761
    # baseline so its first effective-demand plan supports 90% employment.
    # It is expressed for the canonical 600 household-agents.
    calibrated_labor_productivity: float = 325.5
    labor_productivity_reference_households: int = 600

    # Common labour productivity measured in period-0 monetary units per
    # worker. From period 1 onward, sector quantities are first valued at
    # fixed reference prices before labour demand is derived. This avoids
    # adding physically incomparable sector outputs (housing, energy, etc.).
    calibrated_real_labor_productivity: float = 165.0

    # Historical value retained only for replication tests.
    legacy_labor_productivity: float = 60.0

    # =========================================================
    # LABOUR-PRODUCTIVITY REFERENCE CALIBRATION
    # =========================================================

    # Reference sectoral utilisation rates used only to
    # calibrate structural labour productivity.
    #
    # These values do not change when the operational
    # period-0 utilisation rates are modified.
    labor_productivity_reference_agriculture_utilization: float = 1.00
    labor_productivity_reference_energy_utilization: float = 0.33
    labor_productivity_reference_housing_utilization: float = 1.00
    labor_productivity_reference_transport_utilization: float = 0.33
    labor_productivity_reference_industry_utilization: float = 0.05
    labor_productivity_reference_technology_utilization: float = 0.10


    # =========================================================
    # JOB COMPOSITION
    # =========================================================

    # Independent random stream for firms' skill mix.
    skill_mix_seed_offset: int = 40_000

    # Share of high-skilled jobs within each firm.
    min_high_skill_job_share: float = 0.40
    max_high_skill_job_share: float = 0.60

    # autres paramètres
    election_interval: int = 5
    election_threshold: float = 0.50
    seed: int = 42

    alpha_affordability: float = 0.01
    beta_relative_income: float = 0.01
    minimum_needs_index: float = 0.0

    loss_aversion: float = 1.8
    w_needs_change: float = 0.08
    w_relative_position: float = 0.04
    w_loss: float = 0.08
    w_relative_loss: float = 0.04
    w_inertia: float = 1.20
    w_social: float = 0.60
    vote_intercept: float = 0.0

    baseline_income_growth: float = 0.005
    baseline_cost_growth: float = 0.010
    idiosyncratic_income_sigma: float = 0.005
    idiosyncratic_cost_sigma: float = 0.003

    # component of public services in NeedsIndex
    # Switch retained for controlled counterfactuals. The seven-experiment
    # protocol currently disables the whole component temporarily.
    needs_public_service_component_enabled: bool = True
    weight_public_spending_growth: float = 0.10
    weight_transport_burden: float = 0.02
    weight_distance_to_services: float = 0.01

    # =========================================================
    # HOUSEHOLD SKILLS AND LABOUR MATCHING
    # =========================================================

    # Provisional initial share of high-skilled households.
    initial_high_skill_household_share: float = 0.50

    # Independent random streams preserve the political draws.
    household_skill_seed_offset: int = 50_000
    labour_matching_seed_offset: int = 60_000

    # Independent stream for hiring and layoffs after period 0.
    labour_dynamics_seed_offset: int = 70_000

    # Independent Green Deal Job Guarantee draw stream.
    job_guarantee_seed_offset: int = 100_000


    # =========================================================
    # WAGES AND INCOME REPLACEMENT
    # =========================================================

    # When None, the initial base wage will be calibrated
    # from the mean initial disposable income of households.
    initial_base_wage: float | None = None

    # Relative wage structure inherited from the original model.
    minimum_wage_ratio: float = 2.0 / 3.0
    # With a minimum wage equal to two thirds of the base wage,
    # 0.60 provides an unemployment benefit equal to 40% of base wage.
    unemployment_replacement_rate: float = 0.60

    low_skill_green_wage_premium: float = 0.08
    high_skill_wage_premium: float = 0.20
    high_skill_green_wage_premium: float = 0.02

    # Kept at zero until a price/inflation module is introduced.
    nominal_wage_growth_rate: float = 0.0

    # A 2% structural inflation reference is retained for reporting.
    # Wage, benefit and public-purchase indexation is disabled in the
    # reference calibration because it distorted the Green Deal's real path.
    structural_inflation_rate: float = 0.02
    green_deal_indexation_enabled: bool = False
    green_deal_job_guarantee_entry_rate: float = 0.30


    # =========================================================
    # HOUSEHOLD INCOME TAX
    # =========================================================

    # Broad effective direct-tax rate. Together with profit taxation,
    # this moves revenue closer to the European public-revenue scale.
    # Opening net income remains protected by the wage calibration.
    household_income_tax_rate: float = 0.25

    # The historical aggregate formulation taxes total gross
    # household income, including transfers.
    tax_household_transfers: bool = True
    post_growth_progressive_tax_rate: float = 0.15
    post_growth_progressive_tax_threshold_mean: float = 1.50


    # =========================================================
    # HOUSEHOLD CONSUMPTION
    # =========================================================

    # Initial common propensity. The historical model used
    # 0.713 for rural households and 0.717 for urban ones.
    propensity_to_consume_income: float = 0.715

    # Share of accumulated savings entering desired
    # consumption in each period.
    propensity_to_consume_savings: float = 0.01

    # Essential consumption can initially be financed in full
    # through household borrowing.
    allow_essential_consumption_credit: bool = True

    # Initial simplification: no household principal repayment.
    household_debt_repayment_rate: float = 0.0

    # Consumer-loan rate retained for the future debt-service
    # module. It does not yet affect current consumption.
    household_loan_interest_rate: float = 0.03


    # =========================================================
    # SECTORAL CONSUMPTION ALLOCATION
    # =========================================================

    # Independent random stream for household territory.
    household_consumption_preference_seed_offset: int = 90_000

    # Historical rural/urban calibration.
    rural_household_share: float = (
        116_014_000
        / (
            116_014_000
            + 93_567_000
        )
    )

    # Composition of the essential consumption basket.
    # Initial values: agriculture 0.05, energy 0.01,
    # housing 0.07 and transport 0.02.
    essential_agriculture_share: float = 1.0 / 3.0
    essential_energy_share: float = 1.0 / 15.0
    essential_housing_share: float = 7.0 / 15.0
    essential_transport_share: float = 2.0 / 15.0

    # Rural supplementary-consumption preferences.
    rural_agriculture_preference: float = 0.23
    rural_energy_preference: float = 0.08
    rural_housing_preference: float = 0.36
    rural_transport_preference: float = 0.16
    rural_industry_preference: float = 0.12
    rural_technology_preference: float = 0.05

    # Urban supplementary-consumption preferences.
    urban_agriculture_preference: float = 0.28
    urban_energy_preference: float = 0.05
    urban_housing_preference: float = 0.38
    urban_transport_preference: float = 0.13
    urban_industry_preference: float = 0.11
    urban_technology_preference: float = 0.05


    # =========================================================
    # FIRM PRICING
    # =========================================================

    # Initial mark-up over unit labour cost.
    initial_price_markup_rate: float = 0.20

    # Numerical floor preventing zero or negative prices.
    minimum_firm_price: float = 1e-6

    # Dynamic price adjustment will be activated only after
    # the complete demand side has been introduced.
    price_adjustment_speed: float = 0.0


    # =========================================================
    # INVESTMENT-GOODS SUPPLIER SECTORS
    # =========================================================

    # Investment goods include construction, machinery and knowledge
    # assets. Housing proxies construction in the six-sector model.
    brown_investment_housing_share: float = 0.50
    brown_investment_industry_share: float = 0.40
    brown_investment_technology_share: float = 0.10

    green_investment_housing_share: float = 0.40
    green_investment_industry_share: float = 0.20
    green_investment_technology_share: float = 0.40
    
    # =========================================================
    # FIRM INVESTMENT
    # =========================================================

    # No new investment is made in period 0.
    initial_investment_period: int = 1

    # Initial gross private-investment rate. With an opening private
    # Gross opening flow: 3% normal replacement plus approximately 4%
    # desired net accumulation.
    initial_investment_rate: float = 0.07

    # Normal economic depreciation (roughly a 33-period service life).
    # Behavioural desired-capital growth is net of this replacement flow.
    capital_depreciation_rate: float = 0.03

    # Firm-specific desired net capital growth is drawn once inside this
    # narrow common range. Gross investment subsequently adds replacement.
    min_firm_animal_spirits: float = 0.035
    max_firm_animal_spirits: float = 0.045

    # Carbon cost applied to brown capital when the
    # carbon-tax policy is active.
    firm_carbon_tax_rate: float = 0.016

    # Ad-valorem carbon charge on the carbon-weighted value of
    # household consumption. It applies to Carbon Tax and Green Deal.
    household_carbon_tax_rate: float = 0.10
    household_carbon_weight_agriculture: float = 0.60
    household_carbon_weight_energy: float = 1.00
    household_carbon_weight_housing: float = 0.60
    household_carbon_weight_transport: float = 0.80
    household_carbon_weight_industry: float = 0.60
    household_carbon_weight_technology: float = 0.20

    # Sensitivity of brown investment growth to carbon cost.
    brown_investment_carbon_sensitivity: float = 0.0001

    
    # =========================================================
    # FIRM CREDIT AND CAPITAL ACCUMULATION
    # =========================================================

    # Bank credit is not rationed in the canonical model.
    credit_constraint_rate: float = 0.0

    # Standard central-bank refinancing rates.
    standard_green_credit_rate: float = 0.02
    standard_brown_credit_rate: float = 0.02

    # Differentiated rates when the Green Deal is active.
    green_deal_green_credit_rate: float = 0.00
    green_deal_brown_credit_rate: float = 0.05

    # Commercial-bank markup:
    # markup_b = coefficient * market_share_b.
    bank_markup_coefficient: float = 0.02

    # Share of brown credit demand granted when an active
    # post-growth package restricts brown investment.
    post_growth_brown_credit_cap: float = 0.20

    # The brown-credit ceiling tightens while the post-growth package
    # remains active and reaches a full ban after the configured number
    # of consecutive active periods.
    post_growth_brown_credit_cap_decay_rate: float = 0.25
    post_growth_brown_credit_cap_floor: float = 0.02
    post_growth_brown_credit_extinction_after: int = 0

    # Additional retention factor applied to the remaining
    # brown capital under an active post-growth package.
    # Deliberate but gradual stranding of fossil productive capital.
    # This intermediate calibration lies between the former cautious
    # Core value and the factual prototype's very abrupt 0.80 factor.
    post_growth_brown_capital_retention: float = 0.96

    # Universal basic income as a share of the minimum wage.
    # Zero keeps the post-growth package neutral.
    post_growth_basic_income_ratio: float = 0.0
    # Basic income is a universal floor: unemployment insurance pays
    # only the supplement required to reach its normal replacement level.
    post_growth_basic_income_offsets_unemployment_benefit: bool = True

    # Universal basic services planned per household as a share
    # of the current minimum wage.
    #
    # Zero keeps PG-3 neutral.
    post_growth_basic_services_ratio: float = 0.0
    post_growth_basic_services_admin_price_factor: float = 0.50
    # Households re-spend 90% of the private budget released by UBS.
    # The remaining 10% represents saving and rebound neutralisation.
    post_growth_basic_services_no_respend_rate: float = 0.10
    post_growth_basic_services_ramp_periods: int = 3

    # Post-Growth work sharing. A 20% reduction is phased in over three
    # active periods. Monthly wages are deliberately not reduced: firms
    # initially bear the resulting increase in hourly labour cost.
    post_growth_work_time_reduction: float = 0.20
    post_growth_work_time_ramp_periods: int = 3

    # Sector calibration from sen harp factuel.py. Target shares refer
    # to the corresponding essential expenditure; administrative prices
    # and copays determine household and government payments.
    post_growth_ubs_target_agriculture: float = 0.30
    post_growth_ubs_target_energy: float = 0.60
    post_growth_ubs_target_housing: float = 0.60
    post_growth_ubs_target_transport: float = 0.60
    post_growth_ubs_admin_agriculture: float = 0.80
    post_growth_ubs_admin_energy: float = 0.55
    post_growth_ubs_admin_housing: float = 0.60
    post_growth_ubs_admin_transport: float = 0.50
    # Household copays set to 60% in every UBS sector. The public sector
    # finances the remaining 40% at the corresponding administered price.
    post_growth_ubs_copay_agriculture: float = 0.60
    post_growth_ubs_copay_energy: float = 0.60
    post_growth_ubs_copay_housing: float = 0.60
    post_growth_ubs_copay_transport: float = 0.60

    # Provisional allocation of universal basic services
    # across the six productive sectors.
    #
    # These shares must sum to one.
    post_growth_basic_services_agriculture_share: float = 0.246
    post_growth_basic_services_energy_share: float = 0.077
    post_growth_basic_services_housing_share: float = 0.554
    post_growth_basic_services_transport_share: float = 0.123
    post_growth_basic_services_industry_share: float = 0.00
    post_growth_basic_services_technology_share: float = 0.00

    # Contribution of effectively received UBS to NeedsIndex
    # growth. It will be activated in PG-3A-2.
    weight_basic_services_coverage: float = 0.10


    # The canonical equations accumulate loans without
    # principal repayment. This is kept explicit and can
    # subsequently be recalibrated.
    firm_loan_repayment_rate: float = 0.0

    # Distribution of positive firm profits from the preceding period.
    firm_profit_tax_rate: float = 0.25
    firm_dividend_payout_ratio: float = 0.40

    # =========================================================
    # GOVERNMENT SPENDING
    # =========================================================

    # Share of the discretionary public-purchase budget
    # allocated to public capital expenditure.
    government_capital_purchase_share: float = 0.20

    # Initial direct government purchases as a share of the opening
    # C + I + G expenditure aggregate. A 20% order of magnitude keeps
    # the closed economy close to the European expenditure structure.
    initial_government_purchase_gdp_share: float = 0.20

    # Nominal growth of direct government purchases.
    # Kept distinct from the public-service signal used
    # in the NeedsIndex.
    # Keeps ordinary public purchases constant in real terms at
    # the model's 2% structural inflation reference.
    government_purchase_growth_rate: float = 0.02

    # Simple automatic demand stabiliser. Above the reference unemployment
    # rate, ordinary public purchases temporarily rise in proportion to the
    # gap; the supplement vanishes automatically during the recovery.
    government_unemployment_reference_rate: float = 0.08
    government_unemployment_stabilizer: float = 2.0

    # Ordinary purchases are held constant in nominal terms under
    # Post-Growth. UBS remain additional public purchases and automatic
    # transfers/public wages remain free to move countercyclically.
    post_growth_government_purchase_growth_rate: float = 0.0

    # Share of current carbon-tax revenue allocated to
    # additional public green investment when the
    # Green Deal is active.
    green_deal_public_investment_share: float = 0.50

    # Rule transposed from ``sen harp factuel.py``: the Green Deal
    # targets 10% annual growth of the aggregate green-capital base,
    # subject to a ceiling of 10% of lagged nominal GDP.
    green_deal_green_capital_growth_target: float = 0.10
    green_deal_public_investment_gdp_cap: float = 0.10

    # Remaining carbon revenue is returned as a non-taxable,
    # progressively targeted household dividend.
    green_deal_carbon_dividend_share: float = 0.50

    # Fraction of the public green-capital stock converted
    # into productive services available to firms.
    #
    # A value of 1.0 reproduces the one-for-one treatment
    # used in the initial SEN-HARP implementation.
    green_deal_public_capital_service_efficiency: float = 1.0

    # =========================================================
    # SECTORAL ALLOCATION OF GOVERNMENT PURCHASES
    # =========================================================

    # Current purchases: neutral equal allocation.
    government_current_agriculture_share: float = 1.0 / 6.0
    government_current_energy_share: float = 1.0 / 6.0
    government_current_housing_share: float = 1.0 / 6.0
    government_current_transport_share: float = 1.0 / 6.0
    government_current_industry_share: float = 1.0 / 6.0
    government_current_technology_share: float = 1.0 / 6.0

    # Public capital purchases: equal allocation across
    # the five capital-goods and infrastructure sectors (agri_share = 0).
    government_capital_agriculture_share: float = 0.0
    government_capital_energy_share: float = 0.20
    government_capital_housing_share: float = 0.20
    government_capital_transport_share: float = 0.20
    government_capital_industry_share: float = 0.20
    government_capital_technology_share: float = 0.20

    # =========================================================
    # PUBLIC-DEBT HOLDERS
    # =========================================================

    # Share of the closing public-debt stock held directly
    # by the central bank. The remaining share is allocated
    # to commercial banks according to their market shares.
    central_bank_public_debt_share: float = 0.0

    # Gross public spending on the post-growth basic income.
    basic_income_spending: float = 0.0
    
    # =========================================================
    # ENVIRONMENTAL MODULE
    # =========================================================

    # Emissions de référence par ménage et par période
    base_energy_emissions: float = 1.0
    base_transport_emissions: float = 0.8
    base_consumption_emissions: float = 0.6

    # Valeurs de normalisation
    reference_transport_cost: float = 12.5
    reference_disposable_income: float = 120.0

    # Multiplicateurs d'émissions lorsque la politique est active
    carbon_tax_emissions_multiplier: float = 0.90
    green_deal_emissions_multiplier: float = 0.85
    post_growth_emissions_multiplier: float = 0.80

    # Dynamique du stock de pollution
    pollution_decay_rate: float = 0.02

    # Transformation du stock de pollution en dommages
    environmental_damage_scale: float = 0.002

    # Minimal material-use block. Base intensities are normalized;
    # Post-Growth multipliers reproduce sen harp factuel.py.
    material_intensity_agriculture: float = 1.0
    material_intensity_energy: float = 1.0
    material_intensity_housing: float = 1.0
    material_intensity_transport: float = 1.0
    material_intensity_industry: float = 1.0
    material_intensity_technology: float = 1.0
    post_growth_material_multiplier_agriculture: float = 0.80
    post_growth_material_multiplier_energy: float = 0.80
    post_growth_material_multiplier_housing: float = 0.60
    post_growth_material_multiplier_transport: float = 0.60
    post_growth_material_multiplier_industry: float = 0.75
    post_growth_material_multiplier_technology: float = 0.90

    # =========================================================
    # BIOPHYSICAL AND CLIMATE BLOCK
    # =========================================================

    climate_block_enabled: bool = True

    # Energy intensity associated with fully green and fully
    # brown productive capital.
    green_energy_intensity: float = 0.10
    brown_energy_intensity: float = 0.30

    # Conversion of model output into energy use.
    # Provisional value inherited from the initial code.
    energy_per_output: float = 0.0005

   # GtCO2 emitted per model unit of non-renewable energy.
   # Provisional calibration: industrial emissions equal 3.0
   # in period 0 for the seed-1761 baseline.
    emissions_per_non_renewable_energy: float = (
        0.1138112622313912
    )

    # Land-use emissions for the modelled economy.
    initial_land_use_emissions: float = 0.01
    land_use_emissions_decline_rate: float = 0.01

    # Exogenous emissions outside the modelled economy.
    initial_rest_of_world_emissions: float = 37.0
    rest_of_world_emissions_growth: float = 0.01

    # =========================================================
    # CARBON CYCLE, TEMPERATURE AND CLIMATE DAMAGE
    # =========================================================

    # Three-reservoir carbon cycle.
    climate_phi_11: float = 0.9817
    climate_phi_12: float = 0.0183

    climate_phi_21: float = 0.0080
    climate_phi_22: float = 0.9915
    climate_phi_23: float = 0.0005

    climate_phi_32: float = 0.0001
    climate_phi_33: float = 0.9999

    # Initial carbon stocks, in GtCO2.
    initial_atmospheric_carbon: float = 3120.0
    initial_upper_ocean_carbon: float = 5628.8
    initial_lower_ocean_carbon: float = 36706.7

    preindustrial_atmospheric_carbon: float = 2156.2

    # Radiative forcing.
    radiative_forcing_for_co2_doubling: float = 3.8
    initial_exogenous_forcing: float = 0.28
    exogenous_forcing_increment: float = 0.005

    # Temperature dynamics.
    initial_atmospheric_temperature: float = 1.0
    initial_lower_ocean_temperature: float = 0.0068

    climate_sensitivity: float = 3.0

    atmospheric_temperature_adjustment: float = 0.027
    atmosphere_ocean_heat_exchange: float = 0.0018
    lower_ocean_temperature_adjustment: float = 0.005

    # Non-linear climate-damage function.
    climate_damage_eta_1: float = 0.0
    climate_damage_eta_2: float = 0.00284
    climate_damage_eta_3: float = 0.000005

    maximum_damage_temperature: float = 10.0
    climate_damage_exponent: float = 6.754

    # =========================================================
# ALLOCATION OF CLIMATE DAMAGE
# =========================================================

# Overall intensity of climate damage.
# Set to zero for the technical no-damage counterfactual.
    climate_damage_scale: float = 1.0

# Allocation of effective climate damage.
    climate_productivity_damage_share: float = 0.70
    climate_capital_damage_share: float = 0.30
