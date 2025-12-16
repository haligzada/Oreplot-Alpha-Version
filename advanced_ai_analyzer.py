"""
Advanced AI Valuation Analyzer
Hybrid AI System:
- GPT-5.1: Document extraction and financial data parsing (superior vision & JSON)
- Claude Opus 4.5: Investment narratives and strategic analysis (superior reasoning)
Runs all 5 professional valuation methodologies
"""

import os
import json
from typing import Dict, List, Any
from openai import OpenAI
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception
from format_utils import format_currency

from probability_dcf_engine import generate_probability_dcf_from_extraction
from income_dcf_engine import generate_dcf_from_extraction
from monte_carlo_engine import run_full_monte_carlo_analysis
from kilburn_valuation import generate_kilburn_from_extraction
from decision_tree_emv_engine import generate_emv_from_extraction

AI_INTEGRATIONS_OPENAI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
AI_INTEGRATIONS_OPENAI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

openai_client = None
if AI_INTEGRATIONS_OPENAI_API_KEY:
    openai_client = OpenAI(
        api_key=AI_INTEGRATIONS_OPENAI_API_KEY,
        base_url=AI_INTEGRATIONS_OPENAI_BASE_URL
    )
elif OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

anthropic_client = None
if AI_INTEGRATIONS_ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(
        api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
        base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
    )


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


def normalize_extracted_data(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize extracted data by deriving missing values from related fields.
    This helps when the LLM uses different field names or when values need calculation.
    
    Returns the normalized data with a report of what was derived.
    """
    if "error" in extracted_data:
        return extracted_data
    
    economics = extracted_data.get('economics', {}) or {}
    production = extracted_data.get('production', {}) or {}
    resources = extracted_data.get('resources', {}) or {}
    project_info = extracted_data.get('project_info', {}) or {}
    
    derivations = []
    
    # Try to derive annual_production from various sources
    annual_prod = safe_float(production.get('annual_production'), 0)
    if annual_prod <= 0:
        # Try life_of_mine_production / mine_life
        lom_prod = safe_float(production.get('life_of_mine_production'), 0)
        mine_life = safe_float(economics.get('mine_life'), 0)
        if lom_prod > 0 and mine_life > 0:
            annual_prod = lom_prod / mine_life
            production['annual_production'] = annual_prod
            derivations.append(f"Derived annual_production ({annual_prod:.0f}) from life_of_mine_production / mine_life")
    
    if annual_prod <= 0:
        # Try throughput * recovery * 365 for gold (approximate)
        throughput_tpd = safe_float(production.get('throughput_tpd'), 0)
        recovery = safe_float(production.get('recovery_rate'), 0)
        total_mi_grade = safe_float(resources.get('total_mi_grade'), 0)
        if throughput_tpd > 0 and recovery > 0 and total_mi_grade > 0:
            # For gold: throughput(t/day) * grade(g/t) * recovery * 365 / 31.1035 = oz/year
            annual_prod = throughput_tpd * total_mi_grade * (recovery/100 if recovery > 1 else recovery) * 365 / 31.1035
            production['annual_production'] = annual_prod
            derivations.append(f"Calculated annual_production ({annual_prod:.0f} oz) from throughput * grade * recovery")
    
    # Try to derive commodity_price
    commodity_price = safe_float(economics.get('commodity_price'), 0)
    if commodity_price <= 0:
        # Check commodity_price_assumption
        price_assumption = safe_float(economics.get('commodity_price_assumption'), 0)
        if price_assumption > 0:
            economics['commodity_price'] = price_assumption
            commodity_price = price_assumption
            derivations.append(f"Used commodity_price_assumption (${price_assumption}) as commodity_price")
    
    if commodity_price <= 0:
        # Try to calculate from annual_revenue / annual_production
        annual_revenue = safe_float(economics.get('annual_revenue'), 0)
        if annual_revenue > 0 and annual_prod > 0:
            # Revenue is often in millions, production in oz
            commodity_price = (annual_revenue * 1_000_000) / annual_prod
            economics['commodity_price'] = commodity_price
            derivations.append(f"Calculated commodity_price (${commodity_price:.0f}) from annual_revenue / annual_production")
    
    # Try to derive operating_cost / AISC
    aisc = safe_float(economics.get('all_in_sustaining_cost'), 0)
    op_cost = safe_float(economics.get('operating_cost'), 0)
    
    if aisc <= 0 and op_cost <= 0:
        # Try to calculate from annual_opex / annual_production
        annual_opex = safe_float(economics.get('annual_opex'), 0)
        if annual_opex > 0 and annual_prod > 0:
            # OPEX is often in millions, production in oz
            op_cost = (annual_opex * 1_000_000) / annual_prod
            economics['operating_cost'] = op_cost
            derivations.append(f"Calculated operating_cost (${op_cost:.0f}/oz) from annual_opex / annual_production")
    
    if aisc <= 0 and op_cost > 0:
        # Estimate AISC as operating_cost + 15% for sustaining capex
        aisc = op_cost * 1.15
        economics['all_in_sustaining_cost'] = aisc
        derivations.append(f"Estimated AISC (${aisc:.0f}/oz) as operating_cost + 15%")
    
    # Update the data
    extracted_data['economics'] = economics
    extracted_data['production'] = production
    
    # Add derivation notes
    if 'extraction_notes' not in extracted_data:
        extracted_data['extraction_notes'] = {}
    extracted_data['extraction_notes']['derivations'] = derivations
    
    return extracted_data


def get_missing_inputs_report(extracted_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Generate a detailed report of what's missing for each valuation method.
    Returns a dict with methodology names and their missing inputs.
    """
    economics = extracted_data.get('economics', {}) or {}
    production = extracted_data.get('production', {}) or {}
    exploration = extracted_data.get('exploration', {}) or {}
    project_info = extracted_data.get('project_info', {}) or {}
    
    missing = {}
    
    annual_prod = safe_float(production.get('annual_production'), 0)
    commodity_price = safe_float(economics.get('commodity_price'), 0)
    aisc = safe_float(economics.get('all_in_sustaining_cost') or economics.get('operating_cost'), 0)
    
    # Core valuations need: annual_production, commodity_price, operating_cost/AISC
    core_missing = []
    if annual_prod <= 0:
        core_missing.append("Annual Production (oz/year or tonnes/year)")
    if commodity_price <= 0:
        core_missing.append("Commodity Price Assumption ($/oz or $/tonne)")
    if aisc <= 0:
        core_missing.append("Operating Cost or AISC ($/oz or $/tonne)")
    
    if core_missing:
        missing['Income DCF'] = core_missing.copy()
        missing['Probability-Weighted DCF'] = core_missing.copy()
        missing['Monte Carlo Simulation'] = core_missing.copy()
        missing['Decision Tree EMV'] = core_missing.copy()
    
    # Kilburn needs exploration data
    kilburn_missing = []
    exp_spend = safe_float(exploration.get('historical_exploration_spend'), 0)
    drill_meters = safe_float(exploration.get('drill_meters_completed'), 0)
    if exp_spend <= 0 and drill_meters <= 0:
        kilburn_missing.append("Historical Exploration Expenditure or Drill Meters")
    
    area = safe_float(project_info.get('property_area_km2'), 0)
    if area <= 0:
        kilburn_missing.append("Property Area (km²)")
    
    if kilburn_missing:
        missing['Kilburn/Cost Approach'] = kilburn_missing
    
    return missing


def is_rate_limit_error(exception: BaseException) -> bool:
    error_msg = str(exception)
    return (
        "429" in error_msg
        or "RATELIMIT_EXCEEDED" in error_msg
        or "quota" in error_msg.lower()
        or "rate limit" in error_msg.lower()
        or (hasattr(exception, "status_code") and exception.status_code == 429)
    )


ADVANCED_EXTRACTION_PROMPT = """You are a senior mining finance analyst conducting a comprehensive valuation analysis. Extract all relevant financial, technical, and project data from the following documents for advanced valuation modeling.

CRITICAL INSTRUCTION: The valuation engines REQUIRE three core inputs to work:
1. annual_production - The yearly production rate (oz/year, tonnes/year, lbs/year)
2. commodity_price - The assumed metal price ($/oz, $/lb, $/tonne)  
3. operating_cost OR all_in_sustaining_cost (AISC) - Cash costs or AISC ($/oz, $/lb, $/tonne)

WITHOUT THESE THREE VALUES, the valuation will fail. Search thoroughly for them using these common synonyms:
- annual_production: "average annual production", "steady-state production", "life-of-mine average", "LOM annual average", "production rate", "yearly output"
- commodity_price: "gold price assumption", "metal price", "base case price", "spot price assumed", "price assumption"  
- operating_cost/AISC: "cash cost", "C1 cost", "operating cost", "AISC", "all-in sustaining cost", "total cash cost", "site costs"

SEARCH ALL SECTIONS INCLUDING:
- Executive Summary and Key Metrics (often has annual production and price assumptions)
- Section 14: Mineral Resource Estimates (tonnage, grade, contained metal by category)
- Section 16-17: Mining and Processing Methods (throughput, recovery rates)
- Section 21-22: Capital and Operating Cost Estimates (CAPEX, OPEX, AISC - CRITICAL)
- Section 22: Economic Analysis (NPV, IRR, payback, cash flows, price assumptions - CRITICAL)
- Section 25: Interpretation and Conclusions
- All financial tables, schedules, and appendices (often has production schedules, cost summaries)

DOCUMENTS:
{documents}

Extract the following data in JSON format. For the THREE CRITICAL FIELDS (annual_production, commodity_price, operating_cost/all_in_sustaining_cost), try every possible synonym and calculation method before giving up. For other fields, use 0 or null if truly not found:

{{
    "project_info": {{
        "project_name": "Full project name",
        "primary_commodity": "gold/silver/copper/lithium/etc",
        "secondary_commodities": ["list of by-products"],
        "development_stage": "grassroots/early_exploration/advanced_exploration/pre_feasibility/feasibility/permitted/construction/production",
        "location": "Country/Region",
        "jurisdiction": "Tier 1 (Canada, Australia, USA)/Tier 2 (Chile, Peru, Mexico)/Tier 3 (Emerging)/Tier 4 (High Risk)",
        "property_area_km2": 0,
        "technical_complexity": "simple/moderate/complex/highly_complex",
        "mining_method": "open_pit/underground/both",
        "processing_method": "description"
    }},
    "resources": {{
        "measured_tonnage_mt": 0,
        "measured_grade": 0,
        "measured_contained_metal": 0,
        "indicated_tonnage_mt": 0,
        "indicated_grade": 0,
        "indicated_contained_metal": 0,
        "inferred_tonnage_mt": 0,
        "inferred_grade": 0,
        "inferred_contained_metal": 0,
        "total_mi_tonnage_mt": 0,
        "total_mi_grade": 0,
        "total_mi_contained_metal": 0,
        "resource_category": "Measured & Indicated/Inferred/etc",
        "grade_unit": "g/t, %, ppm, etc",
        "metal_unit": "Moz, Mlb, kt, etc"
    }},
    "reserves": {{
        "proven_tonnage_mt": 0,
        "proven_grade": 0,
        "probable_tonnage_mt": 0,
        "probable_grade": 0,
        "total_pp_tonnage_mt": 0,
        "total_pp_grade": 0,
        "total_pp_contained_metal": 0,
        "strip_ratio": 0
    }},
    "production": {{
        "annual_production": 0,
        "annual_production_unit": "oz/year, lbs/year, tonnes/year",
        "life_of_mine_production": 0,
        "throughput_tpd": 0,
        "recovery_rate": 0
    }},
    "economics": {{
        "initial_capex": 0,
        "sustaining_capex": 0,
        "total_capex": 0,
        "annual_opex": 0,
        "operating_cost": 0,
        "operating_cost_unit": "$/oz, $/lb, $/tonne",
        "all_in_sustaining_cost": 0,
        "aisc_unit": "$/oz, $/lb, $/tonne",
        "commodity_price": 0,
        "commodity_price_assumption": 0,
        "npv": 0,
        "npv_pretax": 0,
        "irr": 0,
        "irr_pretax": 0,
        "payback_years": 0,
        "discount_rate": 8,
        "mine_life": 0,
        "annual_revenue": 0,
        "royalty_rate": 0,
        "tax_rate": 0,
        "closure_cost": 0,
        "working_capital": 0
    }},
    "exploration": {{
        "historical_exploration_spend": 0,
        "drill_meters_completed": 0,
        "number_of_drill_holes": 0,
        "regional_prospectivity": 0,
        "project_maturity_score": 0,
        "local_geology_score": 0,
        "analytical_data_quality": 0,
        "exploration_upside": "description"
    }},
    "risk_factors": {{
        "permitting_status": "Not started/In progress/Approved/Challenged",
        "environmental_studies": "Baseline/EIA submitted/EIA approved",
        "community_relations": "Early engagement/Agreements in place/Disputes",
        "financing_status": "Seeking/Partially funded/Fully funded",
        "infrastructure_status": "description",
        "key_risks": ["list of key risks"]
    }},
    "data_quality": {{
        "report_type": "NI 43-101/JORC/S-K 1300/Other",
        "report_date": "YYYY-MM-DD",
        "qualified_person": "Name and credentials",
        "confidence_level": "High/Moderate/Low"
    }},
    "extraction_notes": {{
        "missing_critical_data": ["list items that could not be found"],
        "data_confidence": "High/Medium/Low",
        "assumptions_made": ["list any assumptions"]
    }}
}}

IMPORTANT: 
- Convert all monetary values to millions USD ($ millions)
- Convert percentages to decimals (e.g., 8% = 8, not 0.08) 
- Ensure grade units match commodity (g/t for gold, % for copper)
- Extract both pre-tax and after-tax economics if available
- Note any values that required calculation or estimation"""


class AdvancedAIAnalyzer:
    """Advanced AI-powered valuation analyzer using GPT-5.1"""
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(7),
        wait=wait_exponential(multiplier=1, min=2, max=128),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def extract_valuation_data(documents_text: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract comprehensive valuation data from documents using GPT-5.1
        
        Args:
            documents_text: List of document dictionaries with 'file_name' and 'text'
        
        Returns:
            Extracted data structure for valuation engines
        """
        if openai_client is None:
            return {
                "error": "OpenAI API not configured. Please ensure AI integration is set up.",
                "extraction_notes": {
                    "missing_critical_data": ["OpenAI API credentials not available"],
                    "data_confidence": "None",
                    "assumptions_made": []
                }
            }
        
        combined_text = "\n\n".join([
            f"=== Document: {doc['file_name']} ===\n{doc['text']}"
            for doc in documents_text if doc.get('success', False)
        ])
        
        if not combined_text.strip():
            return {
                "error": "No valid text extracted from documents.",
                "extraction_notes": {
                    "missing_critical_data": ["All documents failed to extract"],
                    "data_confidence": "None",
                    "assumptions_made": []
                }
            }
        
        # OpenAI message limit is 10.5MB, use 8MB to be safe and leave room for prompt
        MAX_TEXT_LENGTH = 8000000
        if len(combined_text) > MAX_TEXT_LENGTH:
            combined_text = combined_text[:MAX_TEXT_LENGTH] + "\n\n[... document text truncated due to length ...]"
        
        base_prompt = ADVANCED_EXTRACTION_PROMPT.format(documents=combined_text)
        
        training_context = ""
        try:
            from training_rag import build_enhanced_context, get_training_statistics
            stats = get_training_statistics()
            if stats.get('total_chunks', 0) > 0:
                training_context = build_enhanced_context(
                    document_text=combined_text[:10000],
                    category=None,
                    commodity=None
                )
        except Exception:
            pass
        
        if training_context:
            prompt = f"{training_context}\n\n{base_prompt}"
        else:
            prompt = base_prompt
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert mining financial analyst. Extract structured data for valuation modeling. Return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=16384,
                reasoning_effort="high"
            )
            
            response_text = response.choices[0].message.content or "{}"
            try:
                extracted_data = json.loads(response_text)
            except json.JSONDecodeError as je:
                # If JSON parsing fails, try to extract valid JSON portion
                try:
                    # Look for the last complete JSON object
                    last_brace = response_text.rfind('}')
                    if last_brace > 0:
                        partial_json = response_text[:last_brace+1]
                        extracted_data = json.loads(partial_json)
                    else:
                        raise ValueError("No valid JSON object found in response")
                except Exception as fallback_e:
                    return {
                        "error": f"AI extraction failed: JSON parsing error - {str(je)}. Response may be truncated or malformed.",
                        "extraction_notes": {
                            "missing_critical_data": ["Extraction error: Invalid JSON response"],
                            "data_confidence": "None",
                            "assumptions_made": []
                        }
                    }
            
            return extracted_data
            
        except Exception as e:
            return {
                "error": f"AI extraction failed: {str(e)}",
                "extraction_notes": {
                    "missing_critical_data": ["Extraction error occurred"],
                    "data_confidence": "None",
                    "assumptions_made": []
                }
            }
    
    @staticmethod
    def run_all_valuations(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all 5 valuation methodologies on extracted data
        
        IMPORTANT: Income DCF runs first and its result is passed to dependent engines
        (Probability DCF and Decision Tree EMV) to ensure consistent calculated NPV values
        instead of using potentially unreliable document-reported NPVs.
        
        Args:
            extracted_data: Data extracted from documents
        
        Returns:
            Complete valuation results from all methods
        """
        if "error" in extracted_data:
            return {"error": extracted_data["error"]}
        
        # NORMALIZE DATA: Try to derive missing values from related fields
        extracted_data = normalize_extracted_data(extracted_data)
        
        # Generate missing inputs report for user feedback
        missing_inputs_report = get_missing_inputs_report(extracted_data)
        
        valuations = {}
        errors = []
        
        # STEP 1: Run Income DCF FIRST - this provides the base NPV for other engines
        try:
            valuations['income_dcf'] = generate_dcf_from_extraction(extracted_data)
        except Exception as e:
            errors.append(f"Income DCF: {str(e)}")
            valuations['income_dcf'] = {"error": str(e)}
        
        # Get the Income DCF result to pass to dependent engines
        income_dcf_result = valuations.get('income_dcf')
        
        # STEP 2: Run Probability DCF using Income DCF result
        try:
            valuations['probability_dcf'] = generate_probability_dcf_from_extraction(
                extracted_data, 
                income_dcf_result=income_dcf_result
            )
        except Exception as e:
            errors.append(f"Probability DCF: {str(e)}")
            valuations['probability_dcf'] = {"error": str(e)}
        
        # STEP 3: Run Monte Carlo with STRICT validation - ALL THREE inputs required
        try:
            economics = extracted_data.get('economics', {}) or {}
            project_info = extracted_data.get('project_info', {}) or {}
            production = extracted_data.get('production', {}) or {}
            
            commodity = (project_info.get('primary_commodity') or 'gold').lower()
            annual_prod_raw = safe_float(production.get('annual_production'), 0)
            commodity_price_raw = safe_float(economics.get('commodity_price'), 0)
            aisc_raw = safe_float(economics.get('all_in_sustaining_cost') or economics.get('operating_cost'), 0)
            
            # STRICT validation - require ALL THREE inputs, no fabrication
            missing_inputs = []
            if annual_prod_raw <= 0:
                missing_inputs.append('annual_production')
            if commodity_price_raw <= 0:
                missing_inputs.append('commodity_price')
            if aisc_raw <= 0:
                missing_inputs.append('operating_cost/AISC')
            
            if len(missing_inputs) > 0:
                valuations['monte_carlo'] = {
                    "error": "insufficient_data",
                    "message": f"Cannot run Monte Carlo: missing {', '.join(missing_inputs)}",
                    "missing_inputs": missing_inputs
                }
            else:
                # All inputs validated - proceed with actual values
                capex = safe_float(economics.get('initial_capex'), 0)
                mine_life_raw = safe_int(economics.get('mine_life'), 15)
                mine_life = mine_life_raw if mine_life_raw > 0 else 15
                raw_discount = safe_float(economics.get('discount_rate'), 8)
                discount = raw_discount / 100 if raw_discount > 1 else raw_discount if raw_discount > 0 else 0.08
                
                valuations['monte_carlo'] = run_full_monte_carlo_analysis(
                    commodity=commodity,
                    annual_production=annual_prod_raw,
                    unit_cost=aisc_raw,
                    initial_capex=capex * 1_000_000,
                    spot_price=commodity_price_raw,
                    years=mine_life,
                    discount_rate=discount,
                    num_simulations=10000
                )
        except Exception as e:
            errors.append(f"Monte Carlo: {str(e)}")
            valuations['monte_carlo'] = {"error": str(e)}
        
        # STEP 4: Run Kilburn Method
        try:
            valuations['kilburn'] = generate_kilburn_from_extraction(extracted_data)
        except Exception as e:
            errors.append(f"Kilburn Method: {str(e)}")
            valuations['kilburn'] = {"error": str(e)}
        
        # STEP 5: Run Decision Tree EMV using Income DCF result
        try:
            valuations['decision_tree'] = generate_emv_from_extraction(
                extracted_data,
                income_dcf_result=income_dcf_result
            )
        except Exception as e:
            errors.append(f"Decision Tree EMV: {str(e)}")
            valuations['decision_tree'] = {"error": str(e)}
        
        valuation_summary = AdvancedAIAnalyzer._create_valuation_summary(valuations, extracted_data)
        
        return {
            'extracted_data': extracted_data,
            'valuations': valuations,
            'summary': valuation_summary,
            'errors': errors if errors else None,
            'missing_inputs_report': missing_inputs_report if missing_inputs_report else None,
            'derivations': extracted_data.get('extraction_notes', {}).get('derivations', [])
        }
    
    @staticmethod
    def _create_valuation_summary(valuations: Dict[str, Any], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of all valuation results"""
        project_info = extracted_data.get('project_info', {})
        economics = extracted_data.get('economics', {})
        
        values = []
        
        if 'probability_dcf' in valuations and 'error' not in valuations['probability_dcf']:
            risk_adj_npv = valuations['probability_dcf'].get('risk_adjusted_valuation', {}).get('risk_adjusted_npv', 0)
            if risk_adj_npv > 0:
                values.append(('Probability-Weighted DCF', risk_adj_npv))
        
        if 'income_dcf' in valuations and 'error' not in valuations['income_dcf']:
            dcf_npv = valuations['income_dcf'].get('valuation_summary', {}).get('npv', 0)
            if dcf_npv > 0:
                values.append(('Income DCF', dcf_npv))
        
        if 'monte_carlo' in valuations and 'error' not in valuations['monte_carlo']:
            mc_p50 = valuations['monte_carlo'].get('npv_statistics', {}).get('p50', 0)
            if isinstance(mc_p50, (int, float)) and mc_p50 > 0:
                mc_p50_millions = mc_p50 / 1_000_000
                values.append(('Monte Carlo P50', mc_p50_millions))
        
        if 'kilburn' in valuations and 'error' not in valuations['kilburn']:
            kilburn_val = valuations['kilburn'].get('valuation_summary', {}).get('recommended_value', 0)
            if kilburn_val > 0:
                values.append(('Kilburn Method', kilburn_val / 1_000_000))
        
        if 'decision_tree' in valuations and 'error' not in valuations['decision_tree']:
            emv = valuations['decision_tree'].get('valuation_summary', {}).get('emv', 0)
            if emv > 0:
                values.append(('Decision Tree EMV', emv))
        
        if values:
            avg_value = sum(v[1] for v in values) / len(values)
            min_value = min(v[1] for v in values)
            max_value = max(v[1] for v in values)
            median_value = sorted([v[1] for v in values])[len(values) // 2]
        else:
            avg_value = min_value = max_value = median_value = 0
        
        recommendations = []
        rec_colors = []
        
        for method, val_data in valuations.items():
            if 'error' not in val_data:
                rec = val_data.get('recommendation', {})
                if rec.get('text'):
                    recommendations.append(f"{method}: {rec['text']}")
                    rec_colors.append(rec.get('color', 'gray'))
        
        overall_recommendation = "Insufficient data for recommendation"
        overall_color = "gray"
        
        if rec_colors:
            green_count = rec_colors.count('green')
            blue_count = rec_colors.count('blue')
            orange_count = rec_colors.count('orange')
            red_count = rec_colors.count('red')
            
            if green_count >= 2:
                overall_recommendation = "Strong Investment Opportunity - Multiple methods indicate high value"
                overall_color = "green"
            elif green_count + blue_count >= 3:
                overall_recommendation = "Positive Investment Case - Good risk-adjusted returns expected"
                overall_color = "blue"
            elif red_count >= 2:
                overall_recommendation = "High Risk / Low Value - Proceed with caution"
                overall_color = "red"
            else:
                overall_recommendation = "Mixed Signals - Detailed analysis required before investment"
                overall_color = "orange"
        
        return {
            'project_name': project_info.get('project_name', 'Unknown Project'),
            'commodity': project_info.get('primary_commodity', 'Unknown'),
            'stage': project_info.get('development_stage', 'Unknown'),
            'valuation_range': {
                'low': round(min_value, 2),
                'mid': round(median_value, 2),
                'high': round(max_value, 2),
                'average': round(avg_value, 2)
            },
            'valuation_breakdown': {name: round(val, 2) for name, val in values},
            'methods_completed': len(values),
            'methods_failed': len([v for v in valuations.values() if 'error' in v]),
            'overall_recommendation': {
                'text': overall_recommendation,
                'color': overall_color
            },
            'method_recommendations': recommendations,
            'base_case_npv': economics.get('npv', 0),
            'base_case_irr': economics.get('irr', 0)
        }
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception(is_rate_limit_error),
        reraise=True
    )
    def generate_valuation_narrative(valuation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate AI-powered narrative for valuation results using Claude Opus 4.5
        
        Claude Opus 4.5 is used here for superior reasoning and narrative generation,
        while GPT-5.1 handles data extraction (hybrid AI approach).
        
        Args:
            valuation_results: Complete valuation results from run_all_valuations
        
        Returns:
            Narrative summary for report
        """
        summary = valuation_results.get('summary', {})
        extracted = valuation_results.get('extracted_data', {})
        valuations = valuation_results.get('valuations', {})
        
        prompt = f"""Based on the following advanced valuation analysis, write a professional executive summary suitable for an investment committee presentation.

PROJECT: {summary.get('project_name', 'Mining Project')}
COMMODITY: {summary.get('commodity', 'Unknown')}
STAGE: {summary.get('stage', 'Unknown')}

VALUATION RANGE:
- Low estimate: ${summary.get('valuation_range', {}).get('low', 0):.1f}M
- Mid estimate: ${summary.get('valuation_range', {}).get('mid', 0):.1f}M  
- High estimate: ${summary.get('valuation_range', {}).get('high', 0):.1f}M

BASE CASE ECONOMICS:
- NPV: ${extracted.get('economics', {}).get('npv', 0):.1f}M
- IRR: {extracted.get('economics', {}).get('irr', 0):.1f}%
- Mine Life: {extracted.get('economics', {}).get('mine_life', 0)} years

VALUATION METHODS APPLIED:
1. Probability-Weighted DCF: Risk-adjusted for stage-gate probabilities
2. Income Approach DCF: Base case cash flow analysis
3. Monte Carlo Simulation: 10,000 scenarios with price uncertainty
4. Kilburn Method: Exploration asset floor value
5. Decision Tree EMV: Stage-gate expected monetary value

OVERALL RECOMMENDATION: {summary.get('overall_recommendation', {}).get('text', 'N/A')}

Write a 3-4 paragraph executive summary covering:
1. Project overview and current status
2. Key value drivers and risks
3. Valuation methodology summary and conclusions
4. Investment recommendation with key conditions

Keep the tone professional and suitable for institutional investors. Return as JSON with fields:
{{"executive_summary": "...", "key_value_drivers": [...], "key_risks": [...], "investment_thesis": "..."}}"""

        fallback_response = {
            "executive_summary": f"Advanced valuation analysis completed for {summary.get('project_name', 'the mining project')}. The analysis applied five professional methodologies to assess project value. The valuation range spans from ${summary.get('valuation_range', {}).get('low', 0):.1f}M to ${summary.get('valuation_range', {}).get('high', 0):.1f}M based on the available data.",
            "key_value_drivers": ["Resource size and grade", "Cost structure competitiveness", "Jurisdiction quality", "Development stage advancement"],
            "key_risks": ["Commodity price volatility", "Execution risk", "Permitting timeline", "Capital availability"],
            "investment_thesis": summary.get('overall_recommendation', {}).get('text', 'See detailed valuation analysis for investment recommendation'),
        }

        if anthropic_client is not None:
            try:
                message = anthropic_client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=4096,
                    system="You are a senior mining investment analyst writing for institutional investors. Be concise, professional, and data-driven. Always respond with valid JSON only.",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                response_text = "{}"
                if message.content:
                    first_block = message.content[0]
                    if hasattr(first_block, 'text'):
                        response_text = first_block.text
                
                try:
                    narrative = json.loads(response_text)
                    narrative["ai_model"] = "Claude Opus 4.5"
                    return narrative
                except json.JSONDecodeError:
                    import re
                    json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                    if json_match:
                        narrative = json.loads(json_match.group())
                        narrative["ai_model"] = "Claude Opus 4.5"
                        return narrative
                    fallback_response["note"] = "Claude response parsing failed, using fallback"
                    return fallback_response
                    
            except Exception as claude_error:
                fallback_response["claude_error"] = str(claude_error)
        
        claude_failed = "claude_error" in fallback_response
        
        if openai_client is not None:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-5.1",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior mining investment analyst writing for institutional investors. Be concise, professional, and data-driven."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    max_completion_tokens=2048,
                    reasoning_effort="high"
                )
                
                narrative = json.loads(response.choices[0].message.content or "{}")
                narrative["ai_model"] = "GPT-5.1 (fallback)" if claude_failed else "GPT-5.1"
                if claude_failed:
                    narrative["fallback_reason"] = "Claude Opus 4.5 unavailable, used GPT-5.1"
                return narrative
                
            except Exception as e:
                fallback_response["error"] = str(e)
                return fallback_response
        
        fallback_response["note"] = "AI narrative unavailable - no AI integration configured"
        return fallback_response
    
    @staticmethod
    def run_complete_analysis(documents_text: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Run complete advanced valuation analysis pipeline
        
        Args:
            documents_text: List of document dictionaries
        
        Returns:
            Complete analysis with extraction, valuations, and narrative
        """
        extracted_data = AdvancedAIAnalyzer.extract_valuation_data(documents_text)
        
        if "error" in extracted_data and not any(k in extracted_data for k in ['project_info', 'economics']):
            return {"error": extracted_data["error"]}
        
        valuation_results = AdvancedAIAnalyzer.run_all_valuations(extracted_data)
        
        narrative = AdvancedAIAnalyzer.generate_valuation_narrative(valuation_results)
        valuation_results['narrative'] = narrative
        
        return valuation_results
