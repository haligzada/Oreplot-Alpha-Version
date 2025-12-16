import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class FinancialEngine:
    """Core financial calculation engine for DCF models, NPV/IRR, and sensitivity analysis"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def calculate_npv(cashflows: List[float], discount_rate: float) -> float:
        """
        Calculate Net Present Value (NPV) of a series of cash flows
        
        Args:
            cashflows: List of annual cash flows (year 0 = initial investment, typically negative)
            discount_rate: Annual discount rate as decimal (e.g., 0.10 for 10%)
        
        Returns:
            NPV in the same currency units as cash flows
        """
        if not cashflows:
            return 0.0
        
        npv = 0.0
        for year, cashflow in enumerate(cashflows):
            npv += cashflow / ((1 + discount_rate) ** year)
        
        return round(npv, 2)
    
    @staticmethod
    def calculate_irr(cashflows: List[float], guess: float = 0.1, max_iterations: int = 100, tolerance: float = 1e-6) -> Optional[float]:
        """
        Calculate Internal Rate of Return (IRR) using Newton-Raphson method
        
        Args:
            cashflows: List of annual cash flows
            guess: Initial guess for IRR (default 10%)
            max_iterations: Maximum number of iterations
            tolerance: Convergence tolerance
        
        Returns:
            IRR as percentage, or None if calculation fails
        """
        if not cashflows or len(cashflows) < 2:
            return None
        
        try:
            rate = guess
            
            for _ in range(max_iterations):
                npv = sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows))
                
                npv_derivative = sum(-t * cf / ((1 + rate) ** (t + 1)) for t, cf in enumerate(cashflows))
                
                if abs(npv_derivative) < tolerance:
                    return None
                
                new_rate = rate - npv / npv_derivative
                
                if abs(new_rate - rate) < tolerance:
                    if -0.99 <= new_rate <= 10.0:
                        return round(new_rate * 100, 2)
                    return None
                
                rate = new_rate
            
            return None
        except:
            return None
    
    @staticmethod
    def calculate_payback_period(cashflows: List[float]) -> Optional[float]:
        """
        Calculate payback period in years
        
        Args:
            cashflows: List of annual cash flows
        
        Returns:
            Number of years to recover initial investment, or None if never recovered
        """
        if not cashflows or len(cashflows) < 2:
            return None
        
        cumulative = 0.0
        for year, cashflow in enumerate(cashflows):
            cumulative += cashflow
            if cumulative >= 0:
                if year == 0:
                    return 0.0
                
                previous_cumulative = cumulative - cashflow
                fraction = abs(previous_cumulative) / abs(cashflow)
                return round(year - 1 + fraction, 2)
        
        return None
    
    @staticmethod
    def generate_production_profile(
        mine_life_years: int,
        annual_production_target: float,
        ramp_up_years: int = 1,
        ramp_down_years: int = 0
    ) -> List[float]:
        """
        Generate production profile with ramp-up and ramp-down
        
        Args:
            mine_life_years: Total mine life
            annual_production_target: Target annual production at full capacity
            ramp_up_years: Years to reach full production
            ramp_down_years: Years of declining production
        
        Returns:
            List of annual production volumes
        """
        profile = []
        
        for year in range(mine_life_years):
            if year < ramp_up_years:
                production = annual_production_target * (year + 1) / ramp_up_years
            elif year >= mine_life_years - ramp_down_years:
                years_from_end = mine_life_years - year
                production = annual_production_target * years_from_end / (ramp_down_years + 1)
            else:
                production = annual_production_target
            
            profile.append(round(production, 2))
        
        return profile
    
    def generate_cashflow_model(
        self,
        mine_life_years: int,
        production_profile: List[float],
        commodity_price: float,
        opex_per_unit: float,
        initial_capex: float,
        sustaining_capex_annual: float = 0,
        royalty_rate: float = 0.03,
        tax_rate: float = 0.30,
        recovery_rate: float = 1.0
    ) -> Dict:
        """
        Generate complete cash flow model
        
        Args:
            mine_life_years: Total mine life
            production_profile: List of annual production volumes
            commodity_price: Price per unit of commodity
            opex_per_unit: Operating cost per unit produced
            initial_capex: Initial capital expenditure (year 0)
            sustaining_capex_annual: Annual sustaining capital
            royalty_rate: Royalty percentage (decimal)
            tax_rate: Corporate tax rate (decimal)
            recovery_rate: Metallurgical recovery rate (decimal)
        
        Returns:
            Dictionary with detailed cash flow breakdown
        """
        years = list(range(mine_life_years + 1))
        revenue = []
        operating_costs = []
        capex = []
        royalties = []
        ebitda = []
        taxes = []
        net_cashflow = []
        
        for year in years:
            if year == 0:
                revenue.append(0)
                operating_costs.append(0)
                capex.append(-initial_capex)
                royalties.append(0)
                ebitda.append(0)
                taxes.append(0)
                net_cashflow.append(-initial_capex)
            else:
                production = production_profile[year - 1]
                recoverable_production = production * recovery_rate
                
                year_revenue = recoverable_production * commodity_price
                year_opex = production * opex_per_unit
                year_royalty = year_revenue * royalty_rate
                year_ebitda = year_revenue - year_opex - year_royalty
                year_tax = max(0, year_ebitda * tax_rate)
                year_net = year_ebitda - year_tax - sustaining_capex_annual
                
                revenue.append(round(year_revenue, 2))
                operating_costs.append(round(-year_opex, 2))
                capex.append(round(-sustaining_capex_annual, 2))
                royalties.append(round(-year_royalty, 2))
                ebitda.append(round(year_ebitda, 2))
                taxes.append(round(-year_tax, 2))
                net_cashflow.append(round(year_net, 2))
        
        return {
            'years': years,
            'production': [0] + production_profile,
            'revenue': revenue,
            'operating_costs': operating_costs,
            'capex': capex,
            'royalties': royalties,
            'ebitda': ebitda,
            'taxes': taxes,
            'net_cashflow': net_cashflow
        }
    
    def calculate_sensitivity_analysis(
        self,
        base_params: Dict,
        variable_name: str,
        variation_range: List[float],
        discount_rate: float
    ) -> List[Dict]:
        """
        Perform sensitivity analysis by varying one parameter
        
        Args:
            base_params: Base case parameters
            variable_name: Name of parameter to vary (e.g., 'commodity_price', 'opex_per_unit')
            variation_range: List of percentage changes (e.g., [-20, -10, 0, 10, 20])
            discount_rate: Discount rate for NPV calculation
        
        Returns:
            List of results for each variation
        """
        results = []
        
        for variation_pct in variation_range:
            params = base_params.copy()
            
            base_value = params.get(variable_name, 0)
            new_value = base_value * (1 + variation_pct / 100)
            params[variable_name] = new_value
            
            cashflow_model = self.generate_cashflow_model(**params)
            npv = self.calculate_npv(cashflow_model['net_cashflow'], discount_rate)
            irr = self.calculate_irr(cashflow_model['net_cashflow'])
            
            results.append({
                'variable': variable_name,
                'variation_pct': variation_pct,
                'value': round(new_value, 2),
                'npv': npv,
                'irr': irr
            })
        
        return results
    
    def calculate_multi_variable_sensitivity(
        self,
        base_params: Dict,
        variables_to_vary: List[str],
        variation_range: List[float],
        discount_rate: float
    ) -> pd.DataFrame:
        """
        Perform sensitivity analysis on multiple variables (tornado chart data)
        
        Args:
            base_params: Base case parameters
            variables_to_vary: List of parameter names to vary
            variation_range: Typically [-20, 20] for -20% to +20%
            discount_rate: Discount rate for NPV
        
        Returns:
            DataFrame with sensitivity results for tornado chart
        """
        results = []
        
        for variable in variables_to_vary:
            for variation_pct in variation_range:
                params = base_params.copy()
                base_value = params.get(variable, 0)
                new_value = base_value * (1 + variation_pct / 100)
                params[variable] = new_value
                
                cashflow_model = self.generate_cashflow_model(**params)
                npv = self.calculate_npv(cashflow_model['net_cashflow'], discount_rate)
                
                results.append({
                    'variable': variable,
                    'variation_pct': variation_pct,
                    'npv': npv
                })
        
        df = pd.DataFrame(results)
        
        pivot_df = df.pivot(index='variable', columns='variation_pct', values='npv')
        
        if len(variation_range) >= 2:
            pivot_df['range'] = abs(pivot_df[variation_range[-1]] - pivot_df[variation_range[0]])
            pivot_df = pivot_df.sort_values('range', ascending=False)
        
        return pivot_df
    
    @staticmethod
    def calculate_project_valuation(
        npv: float,
        resource_tonnes: float,
        annual_production: float,
        comparable_multiples: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate project valuation using multiple methods
        
        Args:
            npv: Net present value
            resource_tonnes: Total resource in tonnes
            annual_production: Annual production in tonnes
            comparable_multiples: Dictionary with industry multiples
        
        Returns:
            Dictionary with valuation estimates
        """
        valuation = {
            'dcf_valuation': npv,
            'resource_value_per_tonne': npv / resource_tonnes if resource_tonnes > 0 else 0,
            'production_multiple': npv / annual_production if annual_production > 0 else 0
        }
        
        if comparable_multiples:
            if 'ev_per_resource' in comparable_multiples:
                valuation['comp_valuation_resource'] = resource_tonnes * comparable_multiples['ev_per_resource']
            
            if 'ev_per_production' in comparable_multiples:
                valuation['comp_valuation_production'] = annual_production * comparable_multiples['ev_per_production']
        
        return {k: round(v, 2) for k, v in valuation.items()}
