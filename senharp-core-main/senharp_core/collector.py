import csv
from pathlib import Path
from .entities import Household, PolicyState,  EmploymentStatus, Firm, Scenario, Bank, Government, PolicyMode
from .inequality import gini

class Collector:
    def __init__(self) -> None:
        self.household_rows: list[dict] = []
        self.macro_rows: list[dict] = []
        
        self.production_rows: list[dict] = []
        self.firm_rows: list[dict] = []

        self.labour_rows = []

        self.income_rows = []

        self.tax_rows = []

        self.consumption_rows = []

        self.household_banking_rows = []

        self.government_rows: list[
            dict[str, float | int | str]
            ] = []

    def record_production(
        self,
        period: int,
        scenario: Scenario,
        firms: list[Firm],
    ) -> None:
        """Record aggregate and firm-level production results."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        active_firms = [
            firm
            for firm in firms
            if firm.active
        ]

        total_brown_capital = sum(
            firm.brown_capital
            for firm in active_firms
        )

        total_green_capital = sum(
            firm.green_capital
            for firm in active_firms
        )

        total_capital = (
            total_brown_capital
            + total_green_capital
        )
        

        total_potential_output = sum(
            firm.potential_output
            for firm in active_firms
        )

        total_actual_output = sum(
            firm.actual_output
            for firm in active_firms
        )

        total_desired_brown_investment = sum(
            firm.desired_brown_investment
            for firm in active_firms
        )

        total_desired_green_investment = sum(
            firm.desired_green_investment
            for firm in active_firms
        )

        total_brown_investment = sum(
            firm.brown_investment
            for firm in active_firms
        )

        total_green_investment = sum(
            firm.green_investment
            for firm in active_firms
        )

        total_brown_loan_demand = sum(
            firm.brown_loan_demand
            for firm in active_firms
        )

        total_green_loan_demand = sum(
            firm.green_loan_demand
            for firm in active_firms
        )

        total_brown_loans_granted = sum(
            firm.brown_loans_granted
            for firm in active_firms
        )

        total_green_loans_granted = sum(
            firm.green_loans_granted
            for firm in active_firms
        )

        total_brown_loans = sum(
            firm.brown_loans
            for firm in active_firms
        )

        total_green_loans = sum(
            firm.green_loans
            for firm in active_firms
        )

        total_brown_depreciation = sum(
            firm.brown_depreciation
            for firm in active_firms
        )

        total_green_depreciation = sum(
            firm.green_depreciation
            for firm in active_firms
        )

        total_brown_policy_retirement = sum(
            firm.brown_policy_retirement
            for firm in active_firms
        )

        total_firm_carbon_cost = sum(
            firm.firm_carbon_cost
            for firm in active_firms
        )

        number_active_firms = len(
            active_firms
        )

        if number_active_firms > 0:
            mean_productivity = (
                sum(
                    firm.productivity
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_production_shock = (
                sum(
                    firm.production_shock
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_cash_flow_ratio = (
                sum(
                    firm.cash_flow_ratio
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_opening_leverage = (
                sum(
                    firm.investment_leverage
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_closing_leverage = (
                sum(
                    firm.leverage
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_green_credit_rate = (
                sum(
                    firm.green_loan_interest_rate
                    for firm in active_firms
                )
                / number_active_firms
            )

            mean_brown_credit_rate = (
                sum(
                    firm.brown_loan_interest_rate
                    for firm in active_firms
                )
                / number_active_firms
            )
        else:
            mean_productivity = 0.0
            mean_production_shock = 0.0
            mean_cash_flow_ratio = 0.0
            mean_opening_leverage = 0.0
            mean_closing_leverage = 0.0
            mean_green_credit_rate = 0.0
            mean_brown_credit_rate = 0.0

        if total_capital > 0.0:
            aggregate_green_capital_share = (
                total_green_capital
                / total_capital
            )
        else:
            aggregate_green_capital_share = 0.0

        if total_potential_output > 0.0:
            capacity_utilization = (
                total_actual_output
                / total_potential_output
            )
        else:
            capacity_utilization = 0.0

        self.production_rows.append(
            {
                "period": period,
                "scenario": scenario_value,
                "number_active_firms": (
                    number_active_firms
                ),
                "total_brown_capital": (
                    total_brown_capital
                ),
                "total_green_capital": (
                    total_green_capital
                ),
                "total_capital": total_capital,
                "aggregate_green_capital_share": (
                    aggregate_green_capital_share
                ),

                
                "mean_productivity": (
                    mean_productivity
                ),
                "mean_production_shock": (
                    mean_production_shock
                ),
                "total_potential_output": (
                    total_potential_output
                ),
                "total_actual_output": (
                    total_actual_output
                ),
                "capacity_utilization": (
                    capacity_utilization
                ),
                "total_desired_brown_investment": (
                    total_desired_brown_investment
                ),
                "total_desired_green_investment": (
                    total_desired_green_investment
                ),
                "total_brown_investment": (
                    total_brown_investment
                ),
                "total_green_investment": (
                    total_green_investment
                ),
                "total_brown_loan_demand": (
                    total_brown_loan_demand
                ),
                "total_green_loan_demand": (
                    total_green_loan_demand
                ),
                "total_brown_loans_granted": (
                    total_brown_loans_granted
                ),
                "total_green_loans_granted": (
                    total_green_loans_granted
                ),
                "total_brown_loans": (
                    total_brown_loans
                ),
                "total_green_loans": (
                    total_green_loans
                ),
                "total_brown_depreciation": (
                    total_brown_depreciation
                ),
                "total_green_depreciation": (
                    total_green_depreciation
                ),
                "total_brown_policy_retirement": (
                    total_brown_policy_retirement
                ),
                "total_firm_carbon_cost": (
                    total_firm_carbon_cost
                ),
                "mean_cash_flow_ratio": (
                    mean_cash_flow_ratio
                ),
                "mean_opening_leverage": (
                    mean_opening_leverage
                ),
                "mean_closing_leverage": (
                    mean_closing_leverage
                ),
                "mean_green_credit_rate": (
                    mean_green_credit_rate
                ),
                "mean_brown_credit_rate": (
                    mean_brown_credit_rate
                ),
            }
        )

        for firm in firms:
            self.firm_rows.append(
                {
                    "period": period,
                    "scenario": scenario_value,
                    "firm_id": firm.firm_id,
                    "sector": firm.sector.value,
                    "bank_id": firm.bank_id,
                    "active": int(firm.active),
                    "brown_capital": (
                        firm.brown_capital
                    ),
                    "green_capital": (
                        firm.green_capital
                    ),
                    "total_capital": (
                        firm.total_capital
                    ),
                    "opening_brown_capital_before_climate_damage": (
                        firm.opening_brown_capital_before_climate_damage
                    ),

                    "opening_green_capital_before_climate_damage": (
                        firm.opening_green_capital_before_climate_damage
                    ),

                    "climate_capital_damage_rate": (
                        firm.climate_capital_damage_rate
                    ),

                    "climate_brown_capital_loss": (
                        firm.climate_brown_capital_loss
                    ),

                    "climate_green_capital_loss": (
                        firm.climate_green_capital_loss
                    ),

                    "climate_capital_loss": (
                        firm.climate_capital_loss
                    ),
                    
                    "previous_brown_capital": (
                        firm.previous_brown_capital
                    ),

                    "previous_green_capital": (
                        firm.previous_green_capital
                    ),
                    
                    "green_capital_ratio": (
                        firm.green_capital_ratio
                    ),
                    "productivity": (
                        firm.productivity
                    ),
                    "public_green_capital_service": (
                        firm.public_green_capital_service
                    ),
                    "productive_green_capital": (
                        firm.productive_green_capital
                    ),
                    "productive_total_capital": (
                        firm.productive_total_capital
                    ),
                    "productive_green_capital_ratio": (
                        firm.productive_green_capital_ratio
                    ),
                    "planned_brown_investment": (
                        firm.planned_brown_investment
                    ),
                    "planned_green_investment": (
                        firm.planned_green_investment
                    ),
                    "unmet_brown_investment": (
                        firm.unmet_brown_investment
                    ),
                    "unmet_green_investment": (
                        firm.unmet_green_investment
                    ),
                    "planned_brown_loans_granted": (
                        firm.planned_brown_loans_granted
                    ),
                    "planned_green_loans_granted": (
                        firm.planned_green_loans_granted
                    ),             
                    "cancelled_brown_credit": (
                        firm.cancelled_brown_credit
                    ),
                    "cancelled_green_credit": (
                        firm.cancelled_green_credit
                    ),

                    # =========================================================
                    # BIOPHYSICAL PRODUCTION FLOWS
                    # =========================================================

                    "energy_intensity": (
                        firm.energy_intensity
                    ),

                    "energy_needed": (
                        firm.energy_needed
                    ),

                    "renewable_energy_share": (
                        firm.renewable_energy_share
                    ),

                    "renewable_energy": (
                        firm.renewable_energy
                    ),

                    "non_renewable_energy": (
                        firm.non_renewable_energy
                    ),

                    "production_emissions": (
                        firm.production_emissions
                    ),
                    
                    "production_shock": (
                        firm.production_shock
                    ),
                    "potential_output": (
                        firm.potential_output
                    ),
                    "actual_output": (
                        firm.actual_output
                    ),
                    "full_capacity_output": (
                        firm.full_capacity_output
                    ),
                    "previous_profits": (
                        firm.previous_profits
                    ),
                    "revenue": firm.revenue,
                    "wage_bill": firm.wage_bill,
                    "interest_paid": firm.interest_paid,
                    "profits": firm.profits,
                    "firm_carbon_cost": (
                        firm.firm_carbon_cost
                    ),
                    "carbon_tax_paid": (
                        firm.carbon_tax_paid
                    ),
                    "cash_flow_ratio": (
                        firm.cash_flow_ratio
                    ),
                    "opening_leverage": (
                        firm.investment_leverage
                    ),
                    "closing_leverage": (
                        firm.leverage
                    ),
                    "firm_carbon_cost": (
                        firm.firm_carbon_cost
                    ),
                    "desired_brown_capital_growth": (
                        firm.desired_brown_capital_growth
                    ),
                    "desired_green_capital_growth": (
                        firm.desired_green_capital_growth
                    ),
                    "desired_brown_investment": (
                        firm.desired_brown_investment
                    ),
                    "desired_green_investment": (
                        firm.desired_green_investment
                    ),
                    "brown_loan_demand": (
                        firm.brown_loan_demand
                    ),
                    "green_loan_demand": (
                        firm.green_loan_demand
                    ),
                    "brown_loans_granted": (
                        firm.brown_loans_granted
                    ),
                    "green_loans_granted": (
                        firm.green_loans_granted
                    ),
                    "brown_investment": (
                        firm.brown_investment
                    ),
                    "green_investment": (
                        firm.green_investment
                    ),
                    "brown_depreciation": (
                        firm.brown_depreciation
                    ),
                    "green_depreciation": (
                        firm.green_depreciation
                    ),
                    "brown_policy_retirement": (
                        firm.brown_policy_retirement
                    ),
                    "brown_loans": (
                        firm.brown_loans
                    ),
                    "green_loans": (
                        firm.green_loans
                    ),
                    "total_debt": (
                        firm.total_debt
                    ),
                    "green_credit_rate": (
                        firm.green_loan_interest_rate
                    ),
                    "brown_credit_rate": (
                        firm.brown_loan_interest_rate
                    ),
                }
            )

    def record_labour_market(
        self,
        period: int,
        scenario: Scenario,
        households: list[Household],
        firms: list[Firm],
        labour_market_results: dict[str, int] | None,
    ) -> None:
        """Record aggregate labour-market results."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        results = (
            labour_market_results
            if labour_market_results is not None
            else {}
        )

        status_counts = {
            status: sum(
                household.employment_status == status
                for household in households
            )
            for status in EmploymentStatus
        }

        target_jobs = sum(
            firm.target_total_jobs
            for firm in firms
        )

        filled_jobs = sum(
            firm.total_employment
            for firm in firms
        )

        target_green_jobs = sum(
            firm.target_green_jobs
            for firm in firms
        )

        target_brown_jobs = sum(
            firm.target_brown_jobs
            for firm in firms
        )

        green_employment = sum(
            firm.green_employment
            for firm in firms
        )

        brown_employment = sum(
            firm.brown_employment
            for firm in firms
        )

        low_skill_job_demand = sum(
            firm.brown_low_skill_demand
            + firm.green_low_skill_demand
            for firm in firms
        )

        high_skill_job_demand = sum(
            firm.brown_high_skill_demand
            + firm.green_high_skill_demand
            for firm in firms
        )

        low_skill_employment = sum(
            firm.brown_low_skill_employment
            + firm.green_low_skill_employment
            for firm in firms
        )

        high_skill_employment = sum(
            firm.brown_high_skill_employment
            + firm.green_high_skill_employment
            for firm in firms
        )

        low_skill_vacancies = max(
            0,
            low_skill_job_demand
            - low_skill_employment,
        )

        high_skill_vacancies = max(
            0,
            high_skill_job_demand
            - high_skill_employment,
        )

        low_skill_unemployed = sum(
            household.employment_status
            == EmploymentStatus.UNEMPLOYED
            and household.skill_level.value == 0
            for household in households
        )

        high_skill_unemployed = sum(
            household.employment_status
            == EmploymentStatus.UNEMPLOYED
            and household.skill_level.value == 1
            for household in households
        )

        number_households = len(
            households
        )

        private_employment = (
            status_counts[
                EmploymentStatus.LOW_SKILLED_BROWN
            ]
            + status_counts[
                EmploymentStatus.LOW_SKILLED_GREEN
            ]
            + status_counts[
                EmploymentStatus.HIGH_SKILLED_BROWN
            ]
            + status_counts[
                EmploymentStatus.HIGH_SKILLED_GREEN
            ]
        )

        unemployed = status_counts[
            EmploymentStatus.UNEMPLOYED
        ]

        unemployment_rate = (
            unemployed / number_households
            if number_households > 0
            else 0.0
        )

        private_employment_rate = (
            private_employment / number_households
            if number_households > 0
            else 0.0
        )

        vacancy_rate = (
            (
                low_skill_vacancies
                + high_skill_vacancies
            )
            / target_jobs
            if target_jobs > 0
            else 0.0
        )

        self.labour_rows.append(
            {
                "period": period,
                "scenario": scenario_value,

                "number_households": (
                    number_households
                ),

                "target_jobs": target_jobs,
                "filled_jobs": filled_jobs,
                "private_employment": (
                    private_employment
                ),

                "employment_before": (
                    results.get(
                        "employment_before",
                        0,
                    )
                ),

                "layoffs": results.get(
                    "layoffs",
                    0,
                ),

                "hires": results.get(
                    "hires",
                    0,
                ),

                "low_skill_hires": (
                    results.get(
                        "low_skill_hires",
                        0,
                    )
                ),

                "high_skill_hires": (
                    results.get(
                        "high_skill_hires",
                        0,
                    )
                ),

                "vacancies": (
                    low_skill_vacancies
                    + high_skill_vacancies
                ),

                "unemployed": unemployed,

                "private_employment_rate": (
                    private_employment_rate
                ),

                "unemployment_rate": (
                    unemployment_rate
                ),

                "vacancy_rate": vacancy_rate,

                "target_green_jobs": (
                    target_green_jobs
                ),

                "target_brown_jobs": (
                    target_brown_jobs
                ),

                "green_employment": (
                    green_employment
                ),

                "brown_employment": (
                    brown_employment
                ),

                "low_skill_job_demand": (
                    low_skill_job_demand
                ),

                "high_skill_job_demand": (
                    high_skill_job_demand
                ),

                "low_skill_employment": (
                    low_skill_employment
                ),

                "high_skill_employment": (
                    high_skill_employment
                ),

                "low_skill_vacancies": (
                    low_skill_vacancies
                ),

                "high_skill_vacancies": (
                    high_skill_vacancies
                ),

                "low_skill_unemployed": (
                    low_skill_unemployed
                ),

                "high_skill_unemployed": (
                    high_skill_unemployed
                ),

                "status_unemployed": (
                    status_counts[
                        EmploymentStatus.UNEMPLOYED
                    ]
                ),

                "status_low_skilled_brown": (
                    status_counts[
                        EmploymentStatus.LOW_SKILLED_BROWN
                    ]
                ),

                "status_low_skilled_green": (
                    status_counts[
                        EmploymentStatus.LOW_SKILLED_GREEN
                    ]
                ),

                "status_job_guarantee": (
                    status_counts[
                        EmploymentStatus.JOB_GUARANTEE
                    ]
                ),

                "status_high_skilled_brown": (
                    status_counts[
                        EmploymentStatus.HIGH_SKILLED_BROWN
                    ]
                ),

                "status_high_skilled_green": (
                    status_counts[
                        EmploymentStatus.HIGH_SKILLED_GREEN
                    ]
                ),

                "status_reskilling": (
                    status_counts[
                        EmploymentStatus.RESKILLING
                    ]
                ),
            }
        )

    def record_income(
        self,
        period: int,
        scenario: Scenario,
        households: list[Household],
        firms: list[Firm],
        income_results: dict[str, float] | None,
    ) -> None:
        """Record household income flows and wage accounting."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        results = (
            income_results
            if income_results is not None
            else {}
        )

        number_households = len(households)

        total_private_wages = sum(
            household.private_wage_income
            for household in households
        )

        total_public_wages = sum(
            household.public_wage_income
            for household in households
        )

        total_transfers = sum(
            household.transfer_income
            for household in households
        )

        total_gross_income = sum(
            household.gross_income
            for household in households
        )

        total_basic_income = sum(
            household.basic_income_income
            for household in households
        )

        total_firm_wage_bill = sum(
            firm.wage_bill
            for firm in firms
        )

        total_legacy_disposable_income = sum(
            household.disposable_income
            for household in households
        )

        if number_households > 0:
            mean_gross_income = (
                total_gross_income
                / number_households
            )

            mean_legacy_disposable_income = (
                total_legacy_disposable_income
                / number_households
            )
        else:
            mean_gross_income = 0.0
            mean_legacy_disposable_income = 0.0

        if total_gross_income > 0.0:
            private_wage_share = (
                total_private_wages
                / total_gross_income
            )

            public_wage_share = (
                total_public_wages
                / total_gross_income
            )

            transfer_share = (
                total_transfers
                / total_gross_income
            )
        else:
            private_wage_share = 0.0
            public_wage_share = 0.0
            transfer_share = 0.0

        income_identity_gap = (
            total_gross_income
            - total_private_wages
            - total_public_wages
            - total_transfers
        )

        private_wage_accounting_gap = (
            total_private_wages
            - total_firm_wage_bill
        )

        self.income_rows.append(
            {
                "period": period,
                "scenario": scenario_value,
                "number_households": number_households,

                "base_wage": results.get(
                    "base_wage",
                    0.0,
                ),

                "minimum_wage": results.get(
                    "minimum_wage",
                    0.0,
                ),

                "unemployment_benefit": results.get(
                    "unemployment_benefit",
                    0.0,
                ),

                "total_private_wages": (
                    total_private_wages
                ),

                "total_public_wages": (
                    total_public_wages
                ),

                "total_transfers": (
                    total_transfers
                ),

                "total_gross_income": (
                    total_gross_income
                ),

                "mean_gross_income": (
                    mean_gross_income
                ),

                "total_basic_income": (
                    total_basic_income
                ),

                "total_firm_wage_bill": (
                    total_firm_wage_bill
                ),

                "private_wage_share": (
                    private_wage_share
                ),

                "public_wage_share": (
                    public_wage_share
                ),

                "transfer_share": (
                    transfer_share
                ),

                # This is still the income variable used
                # by the former NeedsIndex/political block.
                "mean_legacy_disposable_income": (
                    mean_legacy_disposable_income
                ),

                "income_identity_gap": (
                    income_identity_gap
                ),

                "private_wage_accounting_gap": (
                    private_wage_accounting_gap
                ),
            }
        )
    

    def record_household_taxation(
        self,
        period: int,
        scenario: Scenario,
        households: list[Household],
        government,
        tax_results: dict[str, float] | None,
    ) -> None:
        """Record household income taxation."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        results = (
            tax_results
            if tax_results is not None
            else {}
        )

        number_households = len(households)

        total_gross_income = sum(
            household.gross_income
            for household in households
        )

        total_taxable_income = sum(
            household.taxable_income
            for household in households
        )

        total_income_tax = sum(
            household.income_tax_paid
            for household in households
        )

        total_economic_disposable_income = sum(
            household.economic_disposable_income
            for household in households
        )

        mean_economic_disposable_income = (
            total_economic_disposable_income
            / number_households
            if number_households > 0
            else 0.0
        )

        effective_income_tax_rate = (
            total_income_tax
            / total_gross_income
            if total_gross_income > 0.0
            else 0.0
        )

        household_income_accounting_gap = (
            total_gross_income
            - total_income_tax
            - total_economic_disposable_income
        )

        government_revenue_gap = (
            government.taxes_households
            - total_income_tax
        )

        self.tax_rows.append(
            {
                "period": period,
                "scenario": scenario_value,

                "household_income_tax_rate": (
                    results.get(
                        "household_income_tax_rate",
                        0.0,
                    )
                ),

                "total_gross_income": (
                    total_gross_income
                ),

                "total_taxable_income": (
                    total_taxable_income
                ),

                "total_household_income_tax": (
                    total_income_tax
                ),

                "total_economic_disposable_income": (
                    total_economic_disposable_income
                ),

                "mean_economic_disposable_income": (
                    mean_economic_disposable_income
                ),

                "effective_income_tax_rate": (
                    effective_income_tax_rate
                ),

                "government_taxes_households": (
                    government.taxes_households
                ),

                "household_income_accounting_gap": (
                    household_income_accounting_gap
                ),

                "government_revenue_gap": (
                    government_revenue_gap
                ),
            }
        )
        
    def record_household_consumption(
        self,
        period: int,
        scenario: Scenario,
        households: list[Household],
        consumption_results: (
            dict[str, float] | None
        ),
    ) -> None:
        """Record household consumption and financial stocks."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        results = (
            consumption_results
            if consumption_results is not None
            else {}
        )

        number_households = len(households)

        total_economic_disposable_income = sum(
            household.economic_disposable_income
            for household in households
        )

        total_desired_consumption = sum(
            household.desired_consumption
            for household in households
        )

        total_essential_consumption = sum(
            household.essential_consumption
            for household in households
        )

        total_supplementary_consumption = sum(
            household.supplementary_consumption
            for household in households
        )

        total_consumption = sum(
            household.total_consumption
            for household in households
        )

        total_previous_savings = sum(
            household.previous_savings
            for household in households
        )

        total_savings = sum(
            household.savings
            for household in households
        )

        total_new_household_debt = sum(
            household.new_household_debt
            for household in households
        )

        total_previous_household_debt = sum(
            household.previous_household_debt
            for household in households
        )

        total_household_debt = sum(
            household.household_debt
            for household in households
        )

        total_household_debt_repayment = sum(
            household.household_debt_repayment
            for household in households
        )

        total_household_debt_interest = sum(
            household.household_debt_interest
            for household in households
        )

        household_borrowers = sum(
            household.new_household_debt > 0.0
            for household in households
        )

        indebted_households = sum(
            household.household_debt > 0.0
            for household in households
        )

        unmet_desired_consumption = sum(
            max(
                0.0,
                household.desired_consumption
                - household.total_consumption,
            )
            for household in households
        )

        consumption_accounting_gap = (
            total_previous_savings
            + total_economic_disposable_income
            + total_new_household_debt
            - total_consumption
            - total_household_debt_repayment
            - total_savings
        )

        mean_consumption = (
            total_consumption / number_households
            if number_households > 0
            else 0.0
        )

        mean_savings = (
            total_savings / number_households
            if number_households > 0
            else 0.0
        )

        mean_household_debt = (
            total_household_debt
            / number_households
            if number_households > 0
            else 0.0
        )

        consumption_income_ratio = (
            total_consumption
            / total_economic_disposable_income
            if total_economic_disposable_income > 0.0
            else 0.0
        )

        household_debt_income_ratio = (
            total_household_debt
            / total_economic_disposable_income
            if total_economic_disposable_income > 0.0
            else 0.0
        )

        self.consumption_rows.append(
            {
                "period": period,
                "scenario": scenario_value,
                "number_households": number_households,

                "total_economic_disposable_income": (
                    total_economic_disposable_income
                ),

                "total_desired_consumption": (
                    total_desired_consumption
                ),

                "total_essential_consumption": (
                    total_essential_consumption
                ),

                "total_supplementary_consumption": (
                    total_supplementary_consumption
                ),

                "total_consumption": (
                    total_consumption
                ),

                "mean_consumption": (
                    mean_consumption
                ),

                "consumption_income_ratio": (
                    consumption_income_ratio
                ),

                "total_previous_savings": (
                    total_previous_savings
                ),

                "total_savings": (
                    total_savings
                ),

                "mean_savings": mean_savings,

                "total_new_household_debt": (
                    total_new_household_debt
                ),

                "total_previous_household_debt": (
                    total_previous_household_debt
                ),

                "total_household_debt": (
                    total_household_debt
                ),

                "mean_household_debt": (
                    mean_household_debt
                ),

                "household_debt_income_ratio": (
                    household_debt_income_ratio
                ),

                "total_household_debt_repayment": (
                    total_household_debt_repayment
                ),

                "total_household_debt_interest": (
                    total_household_debt_interest
                ),

                "household_borrowers": (
                    household_borrowers
                ),

                "indebted_households": (
                    indebted_households
                ),

                "unmet_desired_consumption": (
                    unmet_desired_consumption
                ),

                "household_consumption_accounting_gap": (
                    consumption_accounting_gap
                ),

                "reported_accounting_gap": (
                    results.get(
                        "household_consumption_accounting_gap",
                        0.0,
                    )
                ),
            }
        )

    def record_household_banking(
        self,
        period: int,
        scenario: Scenario,
        households: list[Household],
        banks: list[Bank],
        banking_results: dict[str, float] | None,
    ) -> None:
        """Record consumer-credit assets and liabilities."""

        scenario_value = (
            scenario.value
            if hasattr(scenario, "value")
            else str(scenario)
        )

        results = (
            banking_results
            if banking_results is not None
            else {}
        )

        self.household_banking_rows.append(
            {
                "period": period,
                "scenario": scenario_value,

                "total_new_household_debt": sum(
                    household.new_household_debt
                    for household in households
                ),

                "total_new_consumer_loans": sum(
                    bank.new_consumer_loans
                    for bank in banks
                ),

                "total_household_debt": sum(
                    household.household_debt
                    for household in households
                ),

                "total_bank_consumer_loans": sum(
                    bank.consumer_loans
                    for bank in banks
                ),

                "total_household_repayments": sum(
                    household.household_debt_repayment
                    for household in households
                ),

                "total_bank_consumer_loan_repayments": sum(
                    bank.consumer_loan_repayments
                    for bank in banks
                ),

                "total_household_interest": sum(
                    household.household_debt_interest
                    for household in households
                ),

                "total_bank_consumer_interest_income": sum(
                    bank.consumer_loan_interest_income
                    for bank in banks
                ),

                "new_credit_accounting_gap": (
                    results.get(
                        "new_credit_accounting_gap",
                        0.0,
                    )
                ),

                "repayment_accounting_gap": (
                    results.get(
                        "repayment_accounting_gap",
                        0.0,
                    )
                ),

                "consumer_loan_stock_gap": (
                    results.get(
                        "consumer_loan_stock_gap",
                        0.0,
                    )
                ),

                "consumer_interest_accounting_gap": (
                    results.get(
                        "consumer_interest_accounting_gap",
                        0.0,
                    )
                ),
            }
        )
    def record_period(
        self,
        period: int,
        households: list[Household],
        policy: PolicyState,
        policy_mode: str,
        carbon_tax_revenue: float,
        firm_carbon_tax_revenue: float,
        household_carbon_tax_revenue: float,
        carbon_dividend_spending: float,
        nominal_gdp: float,
        real_gdp: float,
        gdp_deflator: float,
        real_gdp_growth: float,
        gdp_revenue_identity_gap: float,
        gdp_results: dict[str, float],
        election: bool,
        policy_active_before: int,
        policy_active_after: int,
        election_type: str,
        policy_transition: str,
        pollution_stock: float,

    # Production emissions
        industrial_emissions: float = 0.0,
        land_use_emissions: float = 0.0,
        modelled_economy_emissions: float = 0.0,
        rest_of_world_emissions: float = 0.0,
        world_emissions: float = 0.0,
        modelled_economy_world_emissions_share: float = 0.0,

    # Carbon cycle
        atmospheric_carbon: float = 0.0,
        upper_ocean_carbon: float = 0.0,
        lower_ocean_carbon: float = 0.0,

    # Forcing, temperature and damage
        exogenous_forcing: float = 0.0,
        radiative_forcing: float = 0.0,
        atmospheric_temperature: float = 0.0,
        lower_ocean_temperature: float = 0.0,
        raw_climate_damage: float = 0.0,
        climate_damage: float = 0.0,
        inflation_rate: float = 0.0,
        material_use: float = 0.0,
        labor_productivity: float = 0.0,
    ) -> None:
        mean_legacy_income = (
            sum(
                household.disposable_income
                for household in households
            )
            / len(households)
        )

        mean_economic_income = (
            sum(
                household.economic_disposable_income
                for household in households
            )
            / len(households)
        )
        
        mean_needs = sum(h.needs_index for h in households) / len(households)
        mean_growth = sum(h.needs_index_growth for h in households) / len(households)
        support = sum(h.vote_probability for h in households) / len(households)
        income_gini = gini(h.economic_disposable_income for h in households)
        needs_index_gini = gini(h.needs_index for h in households)
        job_guarantee_count = sum(
            h.employment_status == EmploymentStatus.JOB_GUARANTEE
            for h in households
        )
        mean_constrained_expenditure_burden = sum(
            (
                h.base_consumption_cost
                if h.constrained_consumption_cost is None
                else h.constrained_consumption_cost
            ) / max(h.economic_disposable_income, 1e-9)
            for h in households
        ) / len(households)


        total_household_emissions = sum(
            household.total_emissions
            for household in households
        )

        mean_household_emissions = (
            total_household_emissions
            / len(households)
        )

        mean_environmental_damage = (
            sum(
                household.environmental_damage
                for household in households
            )
            / len(households)
        )
        
        self.macro_rows.append({
            "period": period,
            "scenario": policy.scenario.value,
            "policy_mode": policy_mode,
            "carbon_tax_revenue": (
                carbon_tax_revenue
            ),
            "firm_carbon_tax_revenue": (
                firm_carbon_tax_revenue
            ),
            "household_carbon_tax_revenue": (
                household_carbon_tax_revenue
            ),
            "carbon_dividend_spending": (
                carbon_dividend_spending
            ),
            "nominal_gdp": nominal_gdp,
            "real_gdp": real_gdp,
            "gdp_deflator": gdp_deflator,
            "real_gdp_growth": real_gdp_growth,
            "inflation_rate": inflation_rate,
            "income_gini": income_gini,
            "needs_index_gini": needs_index_gini,
            "job_guarantee_count": job_guarantee_count,
            "material_use": material_use,
            "labor_productivity": labor_productivity,
            "mean_constrained_expenditure_burden": mean_constrained_expenditure_burden,
            "gdp_revenue_identity_gap": (
                gdp_revenue_identity_gap
            ),
            "nominal_household_consumption": gdp_results[
                "nominal_household_consumption"
            ],
            "nominal_private_investment": gdp_results[
                "nominal_private_investment"
            ],
            "nominal_government_consumption": gdp_results[
                "nominal_government_consumption"
            ],
            "nominal_public_investment": gdp_results[
                "nominal_public_investment"
            ],
            "real_household_consumption": gdp_results[
                "real_household_consumption"
            ],
            "real_private_investment": gdp_results[
                "real_private_investment"
            ],
            "real_government_consumption": gdp_results[
                "real_government_consumption"
            ],
            "real_public_investment": gdp_results[
                "real_public_investment"
            ],
            "nominal_gdp_expenditure_identity_gap": gdp_results[
                "nominal_gdp_expenditure_identity_gap"
            ],
            "real_gdp_expenditure_identity_gap": gdp_results[
                "real_gdp_expenditure_identity_gap"
            ],
           # Ancienne variable conservée
        "policy_active": policy_active_after,

        # Nouvelles variables
        "policy_active_before": (
            policy_active_before
        ),
        "policy_active_after": (
            policy_active_after
        ),
        "election": int(election),
        "election_type": election_type,
        "policy_transition": (
            policy_transition
        ),


            # Ancien nom conservé pour les notebooks existants.
            "total_emissions": (
                total_household_emissions
            ),

# Nom explicite du module environnemental des ménages.
            "total_household_emissions": (
                total_household_emissions
            ),
            "mean_household_emissions": (
                mean_household_emissions
            ),
            "pollution_stock": pollution_stock,
            "mean_environmental_damage": (
                mean_environmental_damage
            ),


                    # =====================================================
        # PRODUCTION EMISSIONS
        # =====================================================

            "industrial_emissions": (
                industrial_emissions
            ),

            "land_use_emissions": (
                land_use_emissions
            ),

            "modelled_economy_emissions": (
                modelled_economy_emissions
            ),

            "rest_of_world_emissions": (
                rest_of_world_emissions
            ),

            "world_emissions": (
                world_emissions
            ),

            "modelled_economy_world_emissions_share": (
                modelled_economy_world_emissions_share
            ),

        # =====================================================
        # CARBON CYCLE
        # =====================================================

            "atmospheric_carbon": (
                atmospheric_carbon
            ),

            "upper_ocean_carbon": (
                upper_ocean_carbon
            ),

            "lower_ocean_carbon": (
                lower_ocean_carbon
            ),

            "total_climate_carbon": (
                atmospheric_carbon
                + upper_ocean_carbon
                + lower_ocean_carbon
            ),

        # =====================================================
        # CLIMATE STATE AND DAMAGE
        # =====================================================

            "exogenous_forcing": (
                exogenous_forcing
            ),

            "radiative_forcing": (
                radiative_forcing
            ),

            "atmospheric_temperature": (
                atmospheric_temperature
            ),

            "lower_ocean_temperature": (
                lower_ocean_temperature
            ),

            "raw_climate_damage": (
                raw_climate_damage
            ),

            "climate_damage": (
                climate_damage
            ),
            
            # Legacy political income.
            "mean_disposable_income": (
                mean_legacy_income
            ),

            "mean_legacy_disposable_income": (
                mean_legacy_income
            ),

# Income generated by the economic block.
            "mean_economic_disposable_income": (
                mean_economic_income
            ),
            "mean_needs_index_growth": mean_growth,
            "mean_needs_index": mean_needs,
            "mean_vote_probability": support,
            "last_election_support": policy.support_share,
        })
        for h in households:
            self.household_rows.append({
                "period": period,
                "scenario": policy.scenario.value,
                "household_id": h.household_id,
                "peer_group": h.peer_group,
                "disposable_income": h.disposable_income,
                "legacy_disposable_income": (
                    h.disposable_income
                ),

                "economic_disposable_income": (
                    h.economic_disposable_income
                ),
                "household_carbon_tax_base": (
                    h.household_carbon_tax_base
                ),
                "household_carbon_tax_paid": (
                    h.household_carbon_tax_paid
                ),
                "carbon_dividend_income": (
                    h.carbon_dividend_income
                ),
                
                "basic_income_income": (
                    h.basic_income_income
                ),

                "employment_status": (
                    h.employment_status.name
                ),
                "base_consumption_cost": h.base_consumption_cost,

                 "transport_cost": h.transport_cost,
                    "transport_cost_burden": (
                    h.transport_cost_burden
                    ),
                "distance_to_public_services": (
                    h.distance_to_public_services
                    ),

                "affordability_component": (
                    h.affordability_component
                    ),
                "relative_income_component": (
                    h.relative_income_component
                    ),
                "public_service_component": (
                  h.public_service_component
                    ),
                "basic_services_received": (
                    h.basic_services_received
                ),

                "basic_services_coverage": (
                    h.basic_services_coverage
                ),

                "basic_services_component": (
                    h.basic_services_component
                ),
                
                "previous_basic_services_coverage": (
                    h.previous_basic_services_coverage
                ),

                "basic_services_coverage_change": (
                    h.basic_services_coverage_change
                ),

                                
                "needs_index_growth": h.needs_index_growth,
                "needs_index": h.needs_index,
                "vote_probability": h.vote_probability,
                "vote": h.vote,

                # =========================================================
                # HOUSEHOLD ENVIRONMENTAL MODULE
                # =========================================================

                # Legacy name retained for compatibility.
                "total_emissions": (
                    total_household_emissions
                ),

                "total_household_emissions": (
                    total_household_emissions
                ),

                "mean_household_emissions": (
                    mean_household_emissions
                ),

                "pollution_stock": (
                    pollution_stock
                ),

                "mean_environmental_damage": (
                    mean_environmental_damage
                ),

# =========================================================
# PRODUCTION EMISSIONS
# =========================================================

                "industrial_emissions": (
                    industrial_emissions
                ),

                "land_use_emissions": (
                    land_use_emissions
                ),

                "modelled_economy_emissions": (
                    modelled_economy_emissions
                ),

                "rest_of_world_emissions": (
                    rest_of_world_emissions
                ),

                "world_emissions": (
                    world_emissions
                ),

                "modelled_economy_world_emissions_share": (
                    modelled_economy_world_emissions_share
                ),

# =========================================================
# CARBON CYCLE
# =========================================================

                "atmospheric_carbon": (
                    atmospheric_carbon
                ),

                "upper_ocean_carbon": (
                    upper_ocean_carbon
                ),

                "lower_ocean_carbon": (
                    lower_ocean_carbon
                ),

                "total_climate_carbon": (
                    atmospheric_carbon
                    + upper_ocean_carbon
                    + lower_ocean_carbon
                ),

# =========================================================
# TEMPERATURE AND CLIMATE DAMAGE
# =========================================================

                 "exogenous_forcing": (
                     exogenous_forcing
                 ),

                 "radiative_forcing": (
                     radiative_forcing
                 ),

                 "atmospheric_temperature": (
                     atmospheric_temperature
                 ),

                 "lower_ocean_temperature": (
                     lower_ocean_temperature
                 ),

                 "raw_climate_damage": (
                     raw_climate_damage
                 ),

                 "climate_damage": (
                     climate_damage
                 ),
            })

    def record_government(
        self,
        period: int,
        scenario: Scenario,
        policy_mode: PolicyMode,
        policy_active_during_period: int,
        government: Government,
        public_green_capital_results: (
            dict[str, float] | None
        ),
        public_green_productivity_results: (
            dict[str, float] | None
        ),
    ) -> None:
        """Record public accounts and Green Deal investment."""

        capital_results = (
            public_green_capital_results
            if public_green_capital_results is not None
            else {}
        )

        productivity_results = (
            public_green_productivity_results
            or {}
        )

        self.government_rows.append(
            {
                "period": period,
                "scenario": scenario.value,
                "policy_mode": policy_mode.value,
                "policy_active_during_period": (
                    policy_active_during_period
                ),

            # Carbon-tax revenue
                "carbon_tax_revenue": (
                    government.carbon_tax_revenue
                ),
                "firm_carbon_tax_revenue": (
                    government.firm_carbon_tax_revenue
                ),
                "household_carbon_tax_revenue": (
                    government.household_carbon_tax_revenue
                ),
                "carbon_dividend_spending": (
                    government.carbon_dividend_spending
                ),

            # Ordinary and total public capital purchases
                "base_capital_purchases": (
                    government.base_capital_purchases
                 ),
                 "planned_capital_purchases": (
                    government.planned_capital_purchases
                ),
                "realised_capital_purchases": (
                    government.realised_capital_purchases
                ),
                "unmet_capital_purchases": (
                    government.unmet_capital_purchases
                ),

            # Green Deal investment flows
                "planned_public_green_investment": (
                    government
                    .planned_public_green_investment
                ),
                "realised_public_green_investment": (
                    government
                    .realised_public_green_investment
                ),
                "unmet_public_green_investment": (
                    government
                    .unmet_public_green_investment
                ),
                
                "basic_income_spending": (
                    government.basic_income_spending
                ),

                "base_current_purchases": (
                    government.base_current_purchases
                ),

                "planned_basic_services_spending": (
                    government.planned_basic_services_spending
                ),

                "realised_basic_services_spending": (
                    government.realised_basic_services_spending
                ),

                "unmet_basic_services_spending": (
                    government.unmet_basic_services_spending
                ),

            # Government-owned green capital
                "opening_public_green_capital": (
                    capital_results.get(
                        "opening_public_green_capital",
                         government.public_green_capital,
                    )
                ),
                "public_green_capital_depreciation": (
                    government
                    .public_green_capital_depreciation
                ),
                "public_green_capital": (
                    government.public_green_capital
                ),

            # Accounting diagnostics
                "public_green_investment_balance_gap": (
                    government
                    .planned_public_green_investment
                    - government
                    .realised_public_green_investment
                    - government
                    .unmet_public_green_investment
                ),
                "public_green_capital_identity_gap": (
                    capital_results.get(
                        "public_green_capital_identity_gap",
                        0.0,
                    )
                ),

            # Public budget
                "capital_spending": (
                    government.capital_spending
                ),
                "primary_deficit": (
                    government.primary_deficit
                ),
                "deficit": government.deficit,
                "public_debt": (
                    government.public_debt
                ),

                "public_green_capital_available_for_services": (
                    productivity_results.get(
                        "public_green_capital_stock",
                        0.0,
                    )
                ),

                "public_green_capital_service_efficiency": (
                    productivity_results.get(
                        "public_green_capital_service_efficiency",
                        0.0,
                    )
                ),
                
                "public_green_capital_service_pool": (
                    productivity_results.get(
                        "public_green_capital_service_pool",
                        0.0,
                    )
                ),
                
                "allocated_public_green_capital_service": (
                    productivity_results.get(
                        "allocated_public_green_capital_service",
                        0.0,
                    )
                ),
                
                "public_green_capital_allocation_gap": (
                    productivity_results.get(
                        "public_green_capital_allocation_gap",
                        0.0,
                    )
                ),
            }
        )

    @staticmethod
    def _write_csv(path: Path, rows: list[dict]) -> None:
        if not rows: return
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
            writer.writeheader(); writer.writerows(rows)

    def export(self, output_dir: str | Path) -> None:
        output_path = Path(output_dir)
        self._write_csv(output_path / "macro_results.csv", self.macro_rows)
        self._write_csv(output_path / "household_results.csv", self.household_rows)
