"""
Probability-Weighted DCF Engine (Risk-Adjusted NPV)
A valuation method where the DCF result is multiplied by explicit probabilities 
of success at each project stage (exploration, permitting, financing, construction).
"""

import numpy as np
from typing import Dict, Any, Optional, List

STAGE_SUCCESS_PROBABILITIES = {
    'grassroots': {
        'exploration_success': 0.10,
        'resource_definition': 0.30,
        'permitting_approval': 0.60,
        'financing_secured': 0.50,
        'construction_complete': 0.85,
        'production_ramp': 0.90
    },
    'early_exploration': {
        'exploration_success': 0.25,
        'resource_definition': 0.45,
        'permitting_approval': 0.65,
        'financing_secured': 0.55,
        'construction_complete': 0.85,
        'production_ramp': 0.90
    },
    'advanced_exploration': {
        'exploration_success': 0.50,
        'resource_definition': 0.65,
        'permitting_approval': 0.70,
        'financing_secured': 0.60,
        'construction_complete': 0.85,
        'production_ramp': 0.92
    },
    'pre_feasibility': {
        'exploration_success': 0.80,
        'resource_definition': 0.85,
        'permitting_approval': 0.75,
        'financing_secured': 0.65,
        'construction_complete': 0.88,
        'production_ramp': 0.93
    },
    'feasibility': {
        'exploration_success': 0.90,
        'resource_definition': 0.92,
        'permitting_approval': 0.80,
        'financing_secured': 0.70,
        'construction_complete': 0.90,
        'production_ramp': 0.95
    },
    'permitted': {
        'exploration_success': 1.00,
        'resource_definition': 1.00,
        'permitting_approval': 0.95,
        'financing_secured': 0.75,
        'construction_complete': 0.92,
        'production_ramp': 0.95
    },
    'construction': {
        'exploration_success': 1.00,
        'resource_definition': 1.00,
        'permitting_approval': 1.00,
        'financing_secured': 0.90,
        'construction_complete': 0.93,
        'production_ramp': 0.96
    },
    'production': {
        'exploration_success': 1.00,
        'resource_definition': 1.00,
        'permitting_approval': 1.00,
        'financing_secured': 1.00,
        'construction_complete': 1.00,
        'production_ramp': 0.97
    }
}

RISK_FACTOR_ADJUSTMENTS = {
    'jurisdiction': {
        'tier_1': 1.0,
        'tier_2': 0.90,
        'tier_3': 0.75,
        'tier_4': 0.55
    },
    'commodity_risk': {
        'gold': 1.0,
        'silver': 0.95,
        'copper': 0.95,
        'lithium': 0.85,
        'nickel': 0.90,
        'zinc': 0.92,
        'uranium': 0.80,
        'rare_earth': 0.75
    },
    'technical_complexity': {
        'simple': 1.0,
        'moderate': 0.92,
        'complex': 0.80,
        'highly_complex': 0.65
    }
}


def calculate_stage_probability(
    current_stage: str,
    jurisdiction_tier: str = 'tier_2',
    commodity: str = 'gold',
    technical_complexity: str = 'moderate'
) -> Dict[str, Any]:
    """
    Calculate cumulative probability of reaching production
    
    Args:
        current_stage: Current project development stage
        jurisdiction_tier: Jurisdiction risk tier
        commodity: Primary commodity
        technical_complexity: Technical complexity level
    
    Returns:
        Dictionary with stage probabilities and cumulative probability
    """
    stage_key = current_stage.lower().replace(' ', '_').replace('-', '_')
    if stage_key not in STAGE_SUCCESS_PROBABILITIES:
        stage_key = 'early_exploration'
    
    base_probs = STAGE_SUCCESS_PROBABILITIES[stage_key].copy()
    
    jur_adj = RISK_FACTOR_ADJUSTMENTS['jurisdiction'].get(jurisdiction_tier, 0.85)
    comm_adj = RISK_FACTOR_ADJUSTMENTS['commodity_risk'].get(commodity.lower(), 0.90)
    tech_adj = RISK_FACTOR_ADJUSTMENTS['technical_complexity'].get(technical_complexity, 0.90)
    
    adjusted_probs = {}
    cumulative_prob = 1.0
    
    for stage, prob in base_probs.items():
        adjusted_prob = prob * jur_adj * comm_adj * tech_adj
        adjusted_prob = min(adjusted_prob, 0.99)
        adjusted_probs[stage] = round(adjusted_prob, 3)
        cumulative_prob *= adjusted_prob
    
    return {
        'stage_probabilities': adjusted_probs,
        'cumulative_probability': round(cumulative_prob, 4),
        'risk_adjustments': {
            'jurisdiction': jur_adj,
            'commodity': comm_adj,
            'technical': tech_adj,
            'combined': round(jur_adj * comm_adj * tech_adj, 3)
        }
    }


def calculate_probability_weighted_dcf(
    base_npv: float,
    base_irr: float,
    current_stage: str,
    project_life_years: int = 15,
    discount_rate: float = 0.08,
    annual_cash_flows: List[float] = None,
    initial_capex: float = None,
    annual_revenue: float = None,
    annual_opex: float = None,
    jurisdiction_tier: str = 'tier_2',
    commodity: str = 'gold',
    technical_complexity: str = 'moderate'
) -> Dict[str, Any]:
    """
    Calculate probability-weighted DCF valuation
    
    Args:
        base_npv: Base case NPV ($ millions)
        base_irr: Base case IRR (decimal)
        current_stage: Current project stage
        project_life_years: Project life in years
        discount_rate: Discount rate (decimal)
        annual_cash_flows: Optional list of annual cash flows
        initial_capex: Initial capital expenditure ($ millions)
        annual_revenue: Annual revenue ($ millions)
        annual_opex: Annual operating costs ($ millions)
        jurisdiction_tier: Jurisdiction risk tier
        commodity: Primary commodity
        technical_complexity: Technical complexity level
    
    Returns:
        Comprehensive probability-weighted DCF analysis
    """
    prob_analysis = calculate_stage_probability(
        current_stage, 
        jurisdiction_tier, 
        commodity, 
        technical_complexity
    )
    
    cumulative_prob = prob_analysis['cumulative_probability']
    
    risk_adjusted_npv = base_npv * cumulative_prob
    
    if annual_cash_flows is None and all([initial_capex, annual_revenue, annual_opex]):
        annual_cash_flow = annual_revenue - annual_opex
        annual_cash_flows = [-initial_capex] + [annual_cash_flow] * project_life_years
    
    npv_sensitivity = {}
    if base_npv != 0:
        for adj in [-0.20, -0.10, 0.10, 0.20]:
            adjusted_npv = base_npv * (1 + adj)
            risk_adj_npv = adjusted_npv * cumulative_prob
            npv_sensitivity[f"{adj*100:+.0f}%"] = {
                'base_npv': round(adjusted_npv, 2),
                'risk_adjusted_npv': round(risk_adj_npv, 2)
            }
    
    if risk_adjusted_npv > base_npv * 0.5:
        recommendation = "Strong Buy - High probability of value realization"
        color = "green"
    elif risk_adjusted_npv > base_npv * 0.25:
        recommendation = "Buy - Moderate probability-adjusted upside"
        color = "blue"
    elif risk_adjusted_npv > base_npv * 0.10:
        recommendation = "Hold - Significant execution risk embedded"
        color = "orange"
    else:
        recommendation = "High Risk - Consider only with portfolio diversification"
        color = "red"
    
    return {
        'base_case': {
            'npv': round(base_npv, 2),
            'irr': round(base_irr * 100, 2),
            'project_life': project_life_years,
            'discount_rate': round(discount_rate * 100, 2)
        },
        'probability_analysis': {
            'current_stage': current_stage,
            'stage_probabilities': prob_analysis['stage_probabilities'],
            'cumulative_probability': cumulative_prob,
            'probability_percent': round(cumulative_prob * 100, 2),
            'risk_adjustments': prob_analysis['risk_adjustments']
        },
        'risk_adjusted_valuation': {
            'risk_adjusted_npv': round(risk_adjusted_npv, 2),
            'npv_discount_from_base': round((1 - cumulative_prob) * 100, 2),
            'risk_adjusted_irr': round(base_irr * cumulative_prob * 100, 2)
        },
        'sensitivity_analysis': npv_sensitivity,
        'recommendation': {
            'text': recommendation,
            'color': color
        },
        'methodology_notes': [
            "Probability-weighted DCF applies stage-gate success probabilities to base case NPV",
            f"Current stage '{current_stage}' implies {cumulative_prob*100:.1f}% probability of full value realization",
            f"Jurisdiction ({jurisdiction_tier}), commodity ({commodity}), and technical factors adjust base probabilities",
            "Risk-adjusted NPV represents expected value considering all development risks"
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


def generate_probability_dcf_from_extraction(extracted_data: Dict[str, Any], income_dcf_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate Probability-Weighted DCF analysis from AI-extracted document data
    
    IMPORTANT: Uses calculated NPV from Income DCF engine, NOT document-reported NPV
    
    Args:
        extracted_data: Data extracted from documents by GPT-5.1
        income_dcf_result: Pre-calculated Income DCF result (used for base NPV/IRR)
    
    Returns:
        Complete probability-weighted DCF valuation
    """
    if not extracted_data:
        return {
            'error': 'insufficient_data',
            'message': 'No data available for probability-weighted DCF calculation'
        }
    
    economics = extracted_data.get('economics', {}) or {}
    project_info = extracted_data.get('project_info', {}) or {}
    production = extracted_data.get('production', {}) or {}
    
    # CRITICAL: Use calculated NPV from Income DCF, NOT document-reported NPV
    # Document-reported NPVs can be unrealistic or from different assumptions
    
    # If Income DCF returned an error, propagate it - don't fabricate values
    if income_dcf_result and 'error' in income_dcf_result:
        return {
            'error': 'insufficient_data',
            'message': f"Cannot calculate probability-weighted DCF: Income DCF failed - {income_dcf_result.get('message', 'insufficient data')}",
            'upstream_error': income_dcf_result.get('error'),
            'missing_inputs': income_dcf_result.get('missing_inputs', [])
        }
    
    if income_dcf_result and 'valuation_summary' in income_dcf_result:
        base_npv = income_dcf_result['valuation_summary'].get('npv', 0)
        base_irr = income_dcf_result['valuation_summary'].get('irr_percent', 0) / 100
    else:
        # No Income DCF result - try to calculate from first principles with STRICT validation
        annual_prod = safe_float(production.get('annual_production') or economics.get('annual_production'), 0)
        commodity_price = safe_float(economics.get('commodity_price'), 0)
        aisc = safe_float(economics.get('aisc') or economics.get('all_in_sustaining_cost') or economics.get('operating_cost'), 0)
        
        # STRICT: Require ALL THREE inputs - no fabrication
        missing_inputs = []
        if annual_prod <= 0:
            missing_inputs.append('annual_production')
        if commodity_price <= 0:
            missing_inputs.append('commodity_price')
        if aisc <= 0:
            missing_inputs.append('operating_cost')
        
        if len(missing_inputs) > 0:
            return {
                'error': 'insufficient_data',
                'message': f'Cannot calculate probability-weighted DCF: missing {", ".join(missing_inputs)}',
                'missing_inputs': missing_inputs
            }
        
        # Only calculate if we have all inputs
        mine_life = safe_int(economics.get('mine_life'), 15) or 15
        capex = safe_float(economics.get('initial_capex'), 0)
        annual_margin = annual_prod * (commodity_price - aisc)
        annual_margin_millions = annual_margin / 1_000_000
        base_npv = annual_margin_millions * mine_life * 0.6 - capex
        base_irr = 0.15 if base_npv > 0 else 0.05
    
    if base_npv <= 0:
        return {
            'error': 'insufficient_data',
            'message': 'Cannot calculate probability-weighted DCF: calculated NPV is zero or negative',
            'base_npv_calculated': base_npv
        }
    
    current_stage = project_info.get('development_stage') or 'early_exploration'
    project_life_raw = safe_int(economics.get('mine_life'), 15)
    project_life = project_life_raw if project_life_raw > 0 else 15
    raw_discount = safe_float(economics.get('discount_rate'), 8)
    discount_rate = raw_discount / 100 if raw_discount > 1 else raw_discount if raw_discount > 0 else 0.08
    
    jurisdiction = project_info.get('jurisdiction', 'tier_2')
    if isinstance(jurisdiction, str):
        jur_lower = jurisdiction.lower()
        if any(t in jur_lower for t in ['canada', 'australia', 'usa', 'tier 1', 'tier1']):
            jurisdiction_tier = 'tier_1'
        elif any(t in jur_lower for t in ['chile', 'peru', 'mexico', 'tier 2', 'tier2']):
            jurisdiction_tier = 'tier_2'
        elif any(t in jur_lower for t in ['tier 3', 'tier3', 'africa', 'asia']):
            jurisdiction_tier = 'tier_3'
        else:
            jurisdiction_tier = 'tier_2'
    else:
        jurisdiction_tier = 'tier_2'
    
    commodity = project_info.get('primary_commodity', 'gold').lower()
    
    technical = project_info.get('technical_complexity') or 'moderate'
    if isinstance(technical, str):
        tech_lower = technical.lower()
        if 'simple' in tech_lower or 'straightforward' in tech_lower:
            technical_complexity = 'simple'
        elif 'complex' in tech_lower or 'difficult' in tech_lower:
            technical_complexity = 'complex'
        elif 'highly' in tech_lower:
            technical_complexity = 'highly_complex'
        else:
            technical_complexity = 'moderate'
    else:
        technical_complexity = 'moderate'
    
    capex = safe_float(economics.get('initial_capex'), 200)
    revenue = safe_float(economics.get('annual_revenue'), 100)
    opex = safe_float(economics.get('annual_opex'), 50)
    
    return calculate_probability_weighted_dcf(
        base_npv=base_npv,
        base_irr=base_irr,
        current_stage=current_stage,
        project_life_years=project_life,
        discount_rate=discount_rate,
        initial_capex=capex,
        annual_revenue=revenue,
        annual_opex=opex,
        jurisdiction_tier=jurisdiction_tier,
        commodity=commodity,
        technical_complexity=technical_complexity
    )
