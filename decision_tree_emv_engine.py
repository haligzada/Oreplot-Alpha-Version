"""
Decision Tree / Stage-Gate Analysis (EMV) Engine
A sequential decision model that maps out key project stages with costs, 
success probabilities, and outcomes to calculate Expected Monetary Value.
"""

import numpy as np
from typing import Dict, Any, List, Optional

STAGE_GATE_DEFINITIONS = {
    'grassroots': {
        'stages': [
            {'name': 'Initial Exploration', 'cost': 2.0, 'duration': 2, 'success_prob': 0.15, 'next_stage': 'Target Generation'},
            {'name': 'Target Generation', 'cost': 5.0, 'duration': 2, 'success_prob': 0.25, 'next_stage': 'Drilling Program'},
            {'name': 'Drilling Program', 'cost': 15.0, 'duration': 2, 'success_prob': 0.30, 'next_stage': 'Resource Definition'},
            {'name': 'Resource Definition', 'cost': 25.0, 'duration': 2, 'success_prob': 0.50, 'next_stage': 'Preliminary Economic Assessment'},
            {'name': 'Preliminary Economic Assessment', 'cost': 3.0, 'duration': 1, 'success_prob': 0.60, 'next_stage': 'Pre-Feasibility Study'},
            {'name': 'Pre-Feasibility Study', 'cost': 10.0, 'duration': 1, 'success_prob': 0.70, 'next_stage': 'Feasibility Study'},
            {'name': 'Feasibility Study', 'cost': 25.0, 'duration': 1.5, 'success_prob': 0.80, 'next_stage': 'Permitting'},
            {'name': 'Permitting', 'cost': 15.0, 'duration': 2, 'success_prob': 0.75, 'next_stage': 'Financing'},
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.70, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.90, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 3.0
    },
    'early_exploration': {
        'stages': [
            {'name': 'Target Generation', 'cost': 5.0, 'duration': 1.5, 'success_prob': 0.30, 'next_stage': 'Drilling Program'},
            {'name': 'Drilling Program', 'cost': 15.0, 'duration': 2, 'success_prob': 0.35, 'next_stage': 'Resource Definition'},
            {'name': 'Resource Definition', 'cost': 20.0, 'duration': 1.5, 'success_prob': 0.55, 'next_stage': 'Preliminary Economic Assessment'},
            {'name': 'Preliminary Economic Assessment', 'cost': 3.0, 'duration': 1, 'success_prob': 0.65, 'next_stage': 'Pre-Feasibility Study'},
            {'name': 'Pre-Feasibility Study', 'cost': 10.0, 'duration': 1, 'success_prob': 0.72, 'next_stage': 'Feasibility Study'},
            {'name': 'Feasibility Study', 'cost': 25.0, 'duration': 1.5, 'success_prob': 0.82, 'next_stage': 'Permitting'},
            {'name': 'Permitting', 'cost': 15.0, 'duration': 2, 'success_prob': 0.78, 'next_stage': 'Financing'},
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.72, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.92, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 2.5
    },
    'advanced_exploration': {
        'stages': [
            {'name': 'Infill Drilling', 'cost': 20.0, 'duration': 1.5, 'success_prob': 0.60, 'next_stage': 'Resource Update'},
            {'name': 'Resource Update', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.75, 'next_stage': 'Preliminary Economic Assessment'},
            {'name': 'Preliminary Economic Assessment', 'cost': 3.0, 'duration': 0.75, 'success_prob': 0.70, 'next_stage': 'Pre-Feasibility Study'},
            {'name': 'Pre-Feasibility Study', 'cost': 10.0, 'duration': 1, 'success_prob': 0.75, 'next_stage': 'Feasibility Study'},
            {'name': 'Feasibility Study', 'cost': 25.0, 'duration': 1.5, 'success_prob': 0.85, 'next_stage': 'Permitting'},
            {'name': 'Permitting', 'cost': 15.0, 'duration': 2, 'success_prob': 0.80, 'next_stage': 'Financing'},
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.75, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.93, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 2.0
    },
    'pre_feasibility': {
        'stages': [
            {'name': 'Complete Pre-Feasibility', 'cost': 8.0, 'duration': 0.75, 'success_prob': 0.80, 'next_stage': 'Feasibility Study'},
            {'name': 'Feasibility Study', 'cost': 25.0, 'duration': 1.5, 'success_prob': 0.88, 'next_stage': 'Permitting'},
            {'name': 'Permitting', 'cost': 15.0, 'duration': 2, 'success_prob': 0.82, 'next_stage': 'Financing'},
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.78, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.94, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 1.8
    },
    'feasibility': {
        'stages': [
            {'name': 'Complete Feasibility', 'cost': 15.0, 'duration': 1, 'success_prob': 0.90, 'next_stage': 'Permitting'},
            {'name': 'Permitting', 'cost': 15.0, 'duration': 2, 'success_prob': 0.85, 'next_stage': 'Financing'},
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.80, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.95, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 1.5
    },
    'permitted': {
        'stages': [
            {'name': 'Financing', 'cost': 5.0, 'duration': 0.5, 'success_prob': 0.82, 'next_stage': 'Construction'},
            {'name': 'Construction', 'cost': 250.0, 'duration': 2, 'success_prob': 0.96, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 1.3
    },
    'construction': {
        'stages': [
            {'name': 'Complete Construction', 'cost': 150.0, 'duration': 1.5, 'success_prob': 0.97, 'next_stage': 'Production'}
        ],
        'terminal_value_multiple': 1.15
    },
    'production': {
        'stages': [],
        'terminal_value_multiple': 1.0
    }
}


def calculate_emv_valuation(
    current_stage: str,
    terminal_value: float,
    discount_rate: float = 0.10,
    custom_stages: List[Dict] = None,
    scale_factor: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate Expected Monetary Value using decision tree analysis
    
    Args:
        current_stage: Current project development stage
        terminal_value: Expected project value at production ($ millions)
        discount_rate: Discount rate for time value (decimal)
        custom_stages: Optional custom stage definitions
        scale_factor: Scale factor for costs (larger projects may need higher costs)
    
    Returns:
        Comprehensive EMV analysis with decision tree breakdown
    """
    stage_key = current_stage.lower().replace(' ', '_').replace('-', '_')
    if stage_key not in STAGE_GATE_DEFINITIONS:
        stage_key = 'early_exploration'
    
    stage_config = STAGE_GATE_DEFINITIONS[stage_key]
    stages = custom_stages if custom_stages else stage_config['stages']
    terminal_multiple = stage_config['terminal_value_multiple']
    
    total_stages = len(stages)
    if total_stages == 0:
        return {
            'emv': terminal_value,
            'probability_to_production': 1.0,
            'recommendation': {
                'text': 'Already in Production - Value equals operating project NPV',
                'color': 'green'
            }
        }
    
    stage_analysis = []
    cumulative_cost = 0
    cumulative_time = 0
    cumulative_probability = 1.0
    
    for i, stage in enumerate(stages):
        stage_cost = stage['cost'] * scale_factor
        stage_prob = stage['success_prob']
        stage_duration = stage['duration']
        
        cumulative_cost += stage_cost
        cumulative_time += stage_duration
        cumulative_probability *= stage_prob
        
        time_discount = (1 + discount_rate) ** cumulative_time
        
        success_value_this_stage = 0
        if i == total_stages - 1:
            success_value_this_stage = terminal_value / time_discount
        else:
            remaining_prob = 1.0
            for j in range(i + 1, total_stages):
                remaining_prob *= stages[j]['success_prob']
            remaining_time = sum(s['duration'] for s in stages[i+1:])
            total_discount = (1 + discount_rate) ** (cumulative_time + remaining_time)
            success_value_this_stage = (terminal_value * remaining_prob) / total_discount
        
        stage_emv = (success_value_this_stage * stage_prob) - stage_cost
        
        should_proceed = stage_emv > 0
        
        stage_analysis.append({
            'stage_name': stage['name'],
            'stage_number': i + 1,
            'cost': round(stage_cost, 2),
            'duration_years': stage_duration,
            'success_probability': round(stage_prob * 100, 1),
            'cumulative_probability': round(cumulative_probability * 100, 2),
            'cumulative_cost': round(cumulative_cost, 2),
            'cumulative_time': round(cumulative_time, 1),
            'expected_value_if_success': round(success_value_this_stage, 2),
            'stage_emv': round(stage_emv, 2),
            'decision': 'PROCEED' if should_proceed else 'STOP/RECONSIDER',
            'next_stage': stage.get('next_stage', 'Complete')
        })
    
    overall_emv = 0
    running_prob = 1.0
    running_time = 0
    
    for stage in stages:
        running_time += stage['duration']
        time_discount = (1 + discount_rate) ** running_time
        
        failure_prob = 1 - stage['success_prob']
        failure_cost = (stage['cost'] * scale_factor) * running_prob
        failure_loss = -failure_cost / time_discount
        
        overall_emv += failure_loss * failure_prob
        running_prob *= stage['success_prob']
    
    success_pv = (terminal_value * running_prob) / ((1 + discount_rate) ** running_time)
    overall_emv += success_pv
    
    total_investment_if_proceed = sum(s['cost'] * scale_factor for s in stages)
    
    if overall_emv > total_investment_if_proceed * 0.5:
        recommendation = "High Value Opportunity - EMV significantly exceeds required investment"
        color = "green"
    elif overall_emv > total_investment_if_proceed * 0.2:
        recommendation = "Positive EMV - Expected value exceeds risk-adjusted costs"
        color = "blue"
    elif overall_emv > 0:
        recommendation = "Marginal Opportunity - Positive but low EMV relative to investment"
        color = "orange"
    else:
        recommendation = "Negative EMV - Expected losses exceed potential gains"
        color = "red"
    
    optimal_exit_stages = []
    for i, stage in enumerate(stage_analysis):
        if stage['decision'] == 'STOP/RECONSIDER':
            optimal_exit_stages.append(stage['stage_name'])
    
    return {
        'valuation_summary': {
            'emv': round(overall_emv, 2),
            'terminal_value': round(terminal_value, 2),
            'probability_to_production': round(cumulative_probability * 100, 2),
            'total_investment_required': round(total_investment_if_proceed, 2),
            'total_time_to_production': round(cumulative_time, 1),
            'risk_adjusted_multiple': round(overall_emv / total_investment_if_proceed, 2) if total_investment_if_proceed > 0 else 0
        },
        'stage_gate_analysis': stage_analysis,
        'decision_analysis': {
            'optimal_path': 'Proceed through all stages' if not optimal_exit_stages else f'Consider exit at: {", ".join(optimal_exit_stages)}',
            'value_creation_milestones': [
                f"Stage {s['stage_number']}: {s['stage_name']} adds ${s['stage_emv']:.1f}M EMV"
                for s in stage_analysis if s['stage_emv'] > 0
            ],
            'highest_risk_stages': [
                f"{s['stage_name']} ({s['success_probability']:.0f}% success)"
                for s in stage_analysis if s['success_probability'] < 70
            ]
        },
        'real_options_value': {
            'option_to_abandon': round(sum(s['cost'] for s in stage_analysis if s['stage_emv'] < 0) * 0.5, 2),
            'option_to_expand': round(overall_emv * 0.15, 2),
            'option_to_defer': round(overall_emv * 0.10, 2),
            'total_options_value': round(overall_emv * 0.25, 2)
        },
        'recommendation': {
            'text': recommendation,
            'color': color
        },
        'methodology_notes': [
            f"Decision tree with {total_stages} stages from {current_stage} to production",
            f"Terminal value of ${terminal_value:.1f}M discounted at {discount_rate*100:.0f}% over {cumulative_time:.1f} years",
            f"Cumulative probability of reaching production: {cumulative_probability*100:.2f}%",
            "Real options value reflects flexibility to abandon, expand, or defer"
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


def generate_emv_from_extraction(extracted_data: Dict[str, Any], income_dcf_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Generate Decision Tree EMV analysis from AI-extracted document data
    
    IMPORTANT: Uses calculated NPV from Income DCF engine, NOT document-reported NPV
    
    Args:
        extracted_data: Data extracted from documents by GPT-5.1
        income_dcf_result: Pre-calculated Income DCF result (used for terminal value)
    
    Returns:
        Complete EMV valuation
    """
    if not extracted_data:
        return {
            'error': 'insufficient_data',
            'message': 'No data available for EMV calculation'
        }
    
    economics = extracted_data.get('economics', {}) or {}
    project_info = extracted_data.get('project_info', {}) or {}
    production = extracted_data.get('production', {}) or {}
    
    current_stage = project_info.get('development_stage') or 'early_exploration'
    
    # CRITICAL: Use calculated NPV from Income DCF as terminal value, NOT document-reported NPV
    
    # If Income DCF returned an error, propagate it - don't fabricate values
    if income_dcf_result and 'error' in income_dcf_result:
        return {
            'error': 'insufficient_data',
            'message': f"Cannot calculate EMV: Income DCF failed - {income_dcf_result.get('message', 'insufficient data')}",
            'upstream_error': income_dcf_result.get('error'),
            'missing_inputs': income_dcf_result.get('missing_inputs', [])
        }
    
    terminal_value = 0
    if income_dcf_result and 'valuation_summary' in income_dcf_result:
        terminal_value = income_dcf_result['valuation_summary'].get('npv', 0)
    
    # If no Income DCF result, calculate terminal value with STRICT validation
    if terminal_value <= 0:
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
                'message': f'Cannot calculate EMV: missing {", ".join(missing_inputs)}',
                'missing_inputs': missing_inputs
            }
        
        # Only calculate if we have all inputs
        mine_life = safe_int(economics.get('mine_life'), 15) or 15
        capex = safe_float(economics.get('initial_capex'), 0)
        annual_margin = annual_prod * (commodity_price - aisc)
        annual_margin_millions = annual_margin / 1_000_000
        terminal_value = max(0, annual_margin_millions * mine_life * 0.6 - capex)
    
    if terminal_value <= 0:
        return {
            'error': 'insufficient_data',
            'message': 'Cannot calculate EMV: calculated terminal value is zero or negative',
            'terminal_value_calculated': terminal_value
        }
    
    raw_discount = safe_float(economics.get('discount_rate'), 10)
    discount_rate = raw_discount / 100 if raw_discount > 1 else raw_discount if raw_discount > 0 else 0.10
    
    capex = safe_float(economics.get('initial_capex'), 200)
    if capex > 500:
        scale_factor = capex / 250
    elif capex < 100:
        scale_factor = 0.5
    else:
        scale_factor = 1.0
    
    return calculate_emv_valuation(
        current_stage=current_stage,
        terminal_value=terminal_value,
        discount_rate=discount_rate,
        scale_factor=scale_factor
    )
