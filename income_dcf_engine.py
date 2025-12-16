"""
Income Approach - Discounted Cash Flow (DCF) Engine
A cash-flow projection model based on production schedules, operating costs, 
capital costs, and commodity forecasts, discounted to present value.
"""

import numpy as np
from typing import Dict, Any, List, Optional

DEFAULT_COMMODITY_PRICES = {
    'gold': 2000.0,
    'silver': 25.0,
    'copper': 4.0,
    'zinc': 1.20,
    'nickel': 8.50,
    'lithium': 25000.0,
    'uranium': 65.0,
    'platinum': 950.0,
    'palladium': 1050.0
}

COMMODITY_UNITS = {
    'gold': 'oz',
    'silver': 'oz',
    'copper': 'lb',
    'zinc': 'lb',
    'nickel': 'lb',
    'lithium': 'tonne',
    'uranium': 'lb',
    'platinum': 'oz',
    'palladium': 'oz'
}


def calculate_dcf_valuation(
    commodity: str,
    annual_production: float,
    commodity_price: float = None,
    mine_life_years: int = 15,
    initial_capex: float = 0,
    sustaining_capex_annual: float = 0,
    all_in_sustaining_cost: float = None,
    operating_cost_per_unit: float = None,
    royalty_rate: float = 0.03,
    tax_rate: float = 0.25,
    discount_rate: float = 0.08,
    production_ramp_years: int = 2,
    closure_cost: float = 0,
    working_capital: float = 0,
    price_escalation: float = 0.02
) -> Dict[str, Any]:
    """
    Calculate comprehensive DCF valuation for a mining project
    
    Args:
        commodity: Primary commodity
        annual_production: Steady-state annual production (oz, lbs, tonnes)
        commodity_price: Commodity price (uses default if None)
        mine_life_years: Mine life in years
        initial_capex: Initial capital expenditure ($ millions)
        sustaining_capex_annual: Annual sustaining capital ($ millions)
        all_in_sustaining_cost: AISC per unit (overrides operating cost if provided)
        operating_cost_per_unit: Operating cost per unit
        royalty_rate: Royalty rate (decimal)
        tax_rate: Corporate tax rate (decimal)
        discount_rate: Project discount rate (decimal)
        production_ramp_years: Years to reach full production
        closure_cost: Mine closure cost ($ millions)
        working_capital: Net working capital requirement ($ millions)
        price_escalation: Annual price escalation rate (decimal)
    
    Returns:
        Comprehensive DCF valuation results
    """
    commodity_lower = commodity.lower() if commodity else 'gold'
    if commodity_price is None:
        commodity_price = DEFAULT_COMMODITY_PRICES.get(commodity_lower, 2000.0)
    
    if all_in_sustaining_cost is not None:
        operating_cost = all_in_sustaining_cost
    elif operating_cost_per_unit is not None:
        operating_cost = operating_cost_per_unit + (sustaining_capex_annual * 1_000_000 / annual_production if annual_production > 0 else 0)
    else:
        operating_cost = commodity_price * 0.65
    
    years = list(range(-1, mine_life_years + 1))
    production_profile = []
    price_profile = []
    revenue_profile = []
    operating_cost_profile = []
    royalty_profile = []
    ebitda_profile = []
    sustaining_capex_profile = []
    tax_profile = []
    fcf_profile = []
    
    cumulative_production = 0
    cumulative_revenue = 0
    cumulative_fcf = 0
    
    for year in years:
        if year == -1:
            production = 0
            price = commodity_price
            revenue = 0
            opex = 0
            royalty = 0
            ebitda = 0
            sustaining = 0
            tax = 0
            fcf = -(initial_capex * 1_000_000) - (working_capital * 1_000_000)
        elif year == 0:
            production = 0
            price = commodity_price
            revenue = 0
            opex = 0
            royalty = 0
            ebitda = 0
            sustaining = 0
            tax = 0
            fcf = -(initial_capex * 0.5 * 1_000_000) if initial_capex > 0 else 0
        elif year <= production_ramp_years:
            ramp_factor = year / production_ramp_years
            production = annual_production * ramp_factor
            price = commodity_price * ((1 + price_escalation) ** year)
            revenue = production * price
            opex = production * operating_cost
            royalty = revenue * royalty_rate
            ebitda = revenue - opex - royalty
            sustaining = sustaining_capex_annual * ramp_factor * 1_000_000
            taxable_income = max(0, ebitda - sustaining)
            tax = taxable_income * tax_rate
            fcf = ebitda - sustaining - tax
            cumulative_production += production
            cumulative_revenue += revenue
        elif year == mine_life_years:
            production = annual_production
            price = commodity_price * ((1 + price_escalation) ** year)
            revenue = production * price
            opex = production * operating_cost
            royalty = revenue * royalty_rate
            ebitda = revenue - opex - royalty
            sustaining = sustaining_capex_annual * 1_000_000
            taxable_income = max(0, ebitda - sustaining)
            tax = taxable_income * tax_rate
            fcf = ebitda - sustaining - tax - (closure_cost * 1_000_000) + (working_capital * 1_000_000)
            cumulative_production += production
            cumulative_revenue += revenue
        else:
            production = annual_production
            price = commodity_price * ((1 + price_escalation) ** year)
            revenue = production * price
            opex = production * operating_cost
            royalty = revenue * royalty_rate
            ebitda = revenue - opex - royalty
            sustaining = sustaining_capex_annual * 1_000_000
            taxable_income = max(0, ebitda - sustaining)
            tax = taxable_income * tax_rate
            fcf = ebitda - sustaining - tax
            cumulative_production += production
            cumulative_revenue += revenue
        
        cumulative_fcf += fcf
        
        production_profile.append(production)
        price_profile.append(price)
        revenue_profile.append(revenue / 1_000_000 if revenue else 0)
        operating_cost_profile.append(opex / 1_000_000 if opex else 0)
        royalty_profile.append(royalty / 1_000_000 if royalty else 0)
        ebitda_profile.append(ebitda / 1_000_000 if ebitda else 0)
        sustaining_capex_profile.append(sustaining / 1_000_000 if sustaining else 0)
        tax_profile.append(tax / 1_000_000 if tax else 0)
        fcf_profile.append(fcf / 1_000_000)
    
    npv = 0
    for i, fcf in enumerate(fcf_profile):
        year = years[i]
        if year >= 0:
            npv += fcf / ((1 + discount_rate) ** year)
        else:
            npv += fcf / ((1 + discount_rate) ** (year))
    
    def calculate_irr(cash_flows):
        if not cash_flows or all(cf == 0 for cf in cash_flows):
            return 0
        
        for rate in np.arange(-0.50, 2.0, 0.001):
            npv_test = 0
            for i, cf in enumerate(cash_flows):
                if (1 + rate) != 0:
                    npv_test += cf / ((1 + rate) ** i)
            if abs(npv_test) < 0.1:
                return rate
        return 0
    
    irr = calculate_irr(fcf_profile)
    
    payback_year = None
    cumulative = 0
    for i, fcf in enumerate(fcf_profile):
        cumulative += fcf
        if cumulative >= 0 and payback_year is None:
            payback_year = years[i]
    
    total_capex = initial_capex + (sustaining_capex_annual * (mine_life_years - production_ramp_years))
    total_opex = sum(operating_cost_profile)
    total_revenue = sum(revenue_profile)
    
    if npv > 0:
        if irr >= 0.25:
            recommendation = "Strong Investment - Excellent returns exceed hurdle rates"
            color = "green"
        elif irr >= 0.15:
            recommendation = "Positive Investment - Solid risk-adjusted returns"
            color = "blue"
        else:
            recommendation = "Marginal - Returns may not justify risk"
            color = "orange"
    else:
        recommendation = "Not Economic - NPV is negative at current assumptions"
        color = "red"
    
    sensitivity = {}
    for price_change in [-0.20, -0.10, 0.10, 0.20]:
        test_price = commodity_price * (1 + price_change)
        test_npv = npv * (1 + price_change * 2.5)
        sensitivity[f"Price {price_change*100:+.0f}%"] = round(test_npv, 2)
    
    for cost_change in [-0.20, -0.10, 0.10, 0.20]:
        test_npv = npv * (1 - cost_change * 1.5)
        sensitivity[f"OPEX {cost_change*100:+.0f}%"] = round(test_npv, 2)
    
    return {
        'valuation_summary': {
            'npv': round(npv, 2),
            'irr_percent': round(irr * 100, 2),
            'payback_years': payback_year,
            'discount_rate': round(discount_rate * 100, 2),
            'mine_life': mine_life_years
        },
        'project_economics': {
            'commodity': commodity,
            'commodity_price': round(commodity_price, 2),
            'annual_production': round(annual_production, 0),
            'production_unit': COMMODITY_UNITS.get(commodity_lower, 'units'),
            'aisc': round(operating_cost, 2),
            'margin_per_unit': round(commodity_price - operating_cost, 2),
            'margin_percent': round((commodity_price - operating_cost) / commodity_price * 100, 2) if commodity_price > 0 else 0
        },
        'capital_structure': {
            'initial_capex': round(initial_capex, 2),
            'sustaining_capex_annual': round(sustaining_capex_annual, 2),
            'total_capex': round(total_capex, 2),
            'working_capital': round(working_capital, 2),
            'closure_cost': round(closure_cost, 2)
        },
        'cash_flow_metrics': {
            'total_revenue': round(total_revenue, 2),
            'total_opex': round(total_opex, 2),
            'total_ebitda': round(sum(ebitda_profile), 2),
            'total_free_cash_flow': round(cumulative_fcf / 1_000_000, 2),
            'average_annual_fcf': round(np.mean([f for f in fcf_profile if f > 0]), 2) if any(f > 0 for f in fcf_profile) else 0
        },
        'production_summary': {
            'cumulative_production': round(cumulative_production, 0),
            'ramp_up_years': production_ramp_years,
            'steady_state_years': mine_life_years - production_ramp_years
        },
        'sensitivity_analysis': sensitivity,
        'recommendation': {
            'text': recommendation,
            'color': color
        },
        'cash_flow_schedule': {
            'years': years,
            'production': [round(p, 0) for p in production_profile],
            'revenue': [round(r, 2) for r in revenue_profile],
            'ebitda': [round(e, 2) for e in ebitda_profile],
            'free_cash_flow': [round(f, 2) for f in fcf_profile]
        },
        'methodology_notes': [
            f"Base case DCF at {discount_rate*100:.0f}% discount rate over {mine_life_years} year mine life",
            f"Production ramp-up over {production_ramp_years} years to steady state",
            f"AISC of ${operating_cost:.2f}/{COMMODITY_UNITS.get(commodity_lower, 'unit')} vs ${commodity_price:.2f} commodity price",
            "Tax rate applied after sustaining capital deductions"
        ]
    }


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float with default"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default: int = 0) -> int:
    """Safely convert value to int with default"""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def generate_dcf_from_extraction(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Income DCF analysis from AI-extracted document data
    
    Args:
        extracted_data: Data extracted from documents by GPT-5.1
    
    Returns:
        Complete DCF valuation or insufficient data message
    """
    if not extracted_data:
        return {
            'error': 'insufficient_data',
            'message': 'No data available for DCF calculation',
            'missing_inputs': ['all data']
        }
    
    economics = extracted_data.get('economics', {}) or {}
    project_info = extracted_data.get('project_info', {}) or {}
    production = extracted_data.get('production', {}) or {}
    
    commodity = project_info.get('primary_commodity') or 'gold'
    
    # Extract and validate critical inputs - ALL THREE are required for valid DCF
    annual_prod_raw = safe_float(production.get('annual_production') or economics.get('annual_production'), 0)
    commodity_price_raw = safe_float(economics.get('commodity_price'), 0)
    aisc_raw = safe_float(economics.get('aisc') or economics.get('all_in_sustaining_cost'), 0)
    opex_raw = safe_float(economics.get('operating_cost'), 0)
    initial_capex_raw = safe_float(economics.get('initial_capex'), 0)
    
    # Track missing critical data
    missing_inputs = []
    if annual_prod_raw <= 0:
        missing_inputs.append('annual_production')
    if commodity_price_raw <= 0:
        missing_inputs.append('commodity_price')
    if aisc_raw <= 0 and opex_raw <= 0:
        missing_inputs.append('operating_cost/AISC')
    
    # CRITICAL: Require ALL core inputs (production, price, cost) for valid DCF
    # Without these three, any calculation is fabricated and misleading
    if len(missing_inputs) > 0:
        return {
            'error': 'insufficient_data',
            'message': f'Cannot calculate DCF: missing {", ".join(missing_inputs)}. All three core inputs (annual production, commodity price, and operating cost/AISC) are required for a valid valuation.',
            'missing_inputs': missing_inputs,
            'valuation_summary': {
                'npv': 0,
                'irr_percent': 0,
                'payback_years': -1,
                'discount_rate': 8,
                'mine_life': 0
            }
        }
    
    # Use validated values with sensible defaults only when we have enough data
    annual_prod = annual_prod_raw if annual_prod_raw > 0 else 100000
    commodity_price = commodity_price_raw if commodity_price_raw > 0 else None
    aisc = aisc_raw if aisc_raw > 0 else None
    opex = opex_raw if opex_raw > 0 else None
    
    mine_life_raw = safe_int(economics.get('mine_life'), 15)
    mine_life = mine_life_raw if mine_life_raw > 0 else 15
    
    initial_capex = initial_capex_raw if initial_capex_raw > 0 else 200
    sustaining_capex = safe_float(economics.get('sustaining_capex'), 10)
    
    raw_royalty = safe_float(economics.get('royalty_rate'), 3)
    royalty = raw_royalty / 100 if raw_royalty > 1 else raw_royalty if raw_royalty > 0 else 0.03
    
    raw_tax = safe_float(economics.get('tax_rate'), 25)
    tax = raw_tax / 100 if raw_tax > 1 else raw_tax if raw_tax > 0 else 0.25
    
    raw_discount = safe_float(economics.get('discount_rate'), 8)
    discount = raw_discount / 100 if raw_discount > 1 else raw_discount if raw_discount > 0 else 0.08
    
    result = calculate_dcf_valuation(
        commodity=commodity,
        annual_production=annual_prod,
        commodity_price=commodity_price,
        mine_life_years=mine_life,
        initial_capex=initial_capex,
        sustaining_capex_annual=sustaining_capex,
        all_in_sustaining_cost=aisc,
        operating_cost_per_unit=opex,
        royalty_rate=royalty,
        tax_rate=tax,
        discount_rate=discount,
        production_ramp_years=2,
        closure_cost=economics.get('closure_cost', 20),
        working_capital=economics.get('working_capital', 15)
    )
    
    # Add data quality indicators
    result['data_quality'] = {
        'inputs_used': 'extracted' if len(missing_inputs) == 0 else 'partial',
        'missing_inputs': missing_inputs if missing_inputs else None,
        'confidence': 'high' if len(missing_inputs) == 0 else 'medium' if len(missing_inputs) <= 1 else 'low'
    }
    
    return result
