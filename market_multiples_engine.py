"""
Market Multiples Valuation Engine
Implements EV/Resource benchmarking based on PwC methodology
"""

import streamlit as st
from database import SessionLocal
from models import ComparableProject
from sqlalchemy import func
import json
from typing import Dict, List, Optional, Tuple
from format_utils import format_currency
from datetime import datetime


# Industry standard EV/Resource multiples (USD per ounce equivalent)
RESOURCE_MULTIPLES = {
    'gold': {
        'inferred': 20.0,
        'indicated': 45.0,
        'measured': 60.0,
        'mi': 30.0,  # Measured + Indicated average
        'pp': 160.0,  # Proven + Probable
    },
    'silver': {
        'inferred': 0.30,
        'indicated': 0.60,
        'mi': 0.45,
        'pp': 2.00,
    },
    'copper': {
        'inferred': 0.015,  # per lb
        'indicated': 0.025,
        'mi': 0.020,
        'pp': 0.08,
    },
    'zinc': {
        'inferred': 0.008,
        'indicated': 0.015,
        'mi': 0.012,
        'pp': 0.04,
    },
    'nickel': {
        'inferred': 0.02,
        'indicated': 0.04,
        'mi': 0.03,
        'pp': 0.10,
    },
    'lithium': {
        'inferred': 150,  # per tonne LCE
        'indicated': 250,
        'mi': 200,
        'pp': 500,
    },
    'uranium': {
        'inferred': 1.50,  # per lb U3O8
        'indicated': 2.50,
        'mi': 2.00,
        'pp': 6.00,
    },
}

# Development stage adjustments
STAGE_MULTIPLIERS = {
    'exploration': 0.6,
    'resource': 0.8,
    'feasibility': 1.0,
    'development': 1.2,
    'production': 1.5,
    'producing': 1.5,
}

# Jurisdiction risk discounts
JURISDICTION_DISCOUNTS = {
    'tier_1': 1.0,  # Canada, Australia, USA, Chile
    'tier_2': 0.85,  # Mexico, Peru, Brazil, South Africa
    'tier_3': 0.70,  # DRC, Guinea, Indonesia
    'tier_4': 0.50,  # High-risk jurisdictions
}

TIER_1_JURISDICTIONS = ['canada', 'australia', 'usa', 'united states', 'chile', 'uk', 'sweden', 'finland', 'norway']
TIER_2_JURISDICTIONS = ['mexico', 'peru', 'brazil', 'south africa', 'argentina', 'colombia', 'spain', 'portugal', 'ireland']
TIER_3_JURISDICTIONS = ['drc', 'democratic republic of congo', 'guinea', 'indonesia', 'philippines', 'tanzania', 'zambia', 'mali', 'burkina faso', 'ghana', 'ivory coast']


def get_jurisdiction_tier(jurisdiction: str) -> str:
    """Determine jurisdiction risk tier"""
    if not jurisdiction:
        return 'tier_2'
    
    jurisdiction_lower = jurisdiction.lower()
    
    if any(t1 in jurisdiction_lower for t1 in TIER_1_JURISDICTIONS):
        return 'tier_1'
    elif any(t2 in jurisdiction_lower for t2 in TIER_2_JURISDICTIONS):
        return 'tier_2'
    elif any(t3 in jurisdiction_lower for t3 in TIER_3_JURISDICTIONS):
        return 'tier_3'
    else:
        return 'tier_2'  # Default to tier 2


def get_base_multiple(commodity: str, resource_category: str) -> float:
    """Get base EV/Resource multiple for a commodity and category"""
    commodity_lower = commodity.lower() if commodity else 'gold'
    
    # Normalize commodity names
    if 'gold' in commodity_lower or 'au' == commodity_lower:
        commodity_key = 'gold'
    elif 'silver' in commodity_lower or 'ag' == commodity_lower:
        commodity_key = 'silver'
    elif 'copper' in commodity_lower or 'cu' == commodity_lower:
        commodity_key = 'copper'
    elif 'zinc' in commodity_lower or 'zn' == commodity_lower:
        commodity_key = 'zinc'
    elif 'nickel' in commodity_lower or 'ni' == commodity_lower:
        commodity_key = 'nickel'
    elif 'lithium' in commodity_lower or 'li' == commodity_lower:
        commodity_key = 'lithium'
    elif 'uranium' in commodity_lower or 'u3o8' in commodity_lower:
        commodity_key = 'uranium'
    else:
        commodity_key = 'gold'  # Default
    
    multiples = RESOURCE_MULTIPLES.get(commodity_key, RESOURCE_MULTIPLES['gold'])
    
    # Normalize category - check combined categories first (more specific matches)
    category_lower = resource_category.lower() if resource_category else 'inferred'
    
    # Check for P&P / Reserves first
    if any(x in category_lower for x in ['probable', 'proven', 'p+p', 'p&p', 'pp', 'reserve']):
        return multiples['pp']
    # Check for M&I / M+I combined category
    elif any(x in category_lower for x in ['m+i', 'm&i', 'measured & indicated', 'measured and indicated', 'measured+indicated']):
        return multiples['mi']
    # Check for individual categories (after combined to avoid false matches)
    elif 'measured' in category_lower and 'indicated' not in category_lower:
        return multiples['measured']
    elif 'indicated' in category_lower and 'measured' not in category_lower:
        return multiples['indicated']
    elif 'inferred' in category_lower:
        return multiples['inferred']
    else:
        return multiples['inferred']


def calculate_ev_resource_valuation(
    commodity: str,
    resource_estimate: float,
    resource_category: str,
    stage: str,
    jurisdiction: str,
    grade: Optional[float] = None
) -> Dict:
    """
    Calculate project valuation using EV/Resource multiples
    
    Args:
        commodity: Primary commodity (gold, silver, copper, etc.)
        resource_estimate: Resource estimate in appropriate units (oz for gold, lbs for base metals)
        resource_category: Inferred, Indicated, Measured, M&I, or P&P
        stage: Development stage
        jurisdiction: Project location
        grade: Optional grade for premium adjustment
    
    Returns:
        Dictionary with valuation details
    """
    # Get base multiple
    base_multiple = get_base_multiple(commodity, resource_category)
    
    # Get stage multiplier
    stage_lower = stage.lower() if stage else 'exploration'
    stage_mult = 0.6  # Default for exploration
    for key, value in STAGE_MULTIPLIERS.items():
        if key in stage_lower:
            stage_mult = value
            break
    
    # Get jurisdiction discount
    jurisdiction_tier = get_jurisdiction_tier(jurisdiction)
    jurisdiction_discount = JURISDICTION_DISCOUNTS[jurisdiction_tier]
    
    # Calculate adjusted multiple
    adjusted_multiple = base_multiple * stage_mult * jurisdiction_discount
    
    # Grade premium/discount (10% premium for top quartile grades)
    grade_adjustment = 1.0
    if grade:
        # This would require historical grade data for comparison
        # For now, apply a simple heuristic
        if commodity.lower() == 'gold' and grade > 3.0:  # High-grade gold > 3 g/t
            grade_adjustment = 1.15
        elif commodity.lower() == 'gold' and grade < 0.8:  # Low-grade gold < 0.8 g/t
            grade_adjustment = 0.85
    
    final_multiple = adjusted_multiple * grade_adjustment
    
    # Calculate implied value
    implied_value = resource_estimate * final_multiple
    
    # Calculate range (±20%)
    low_value = implied_value * 0.80
    high_value = implied_value * 1.20
    
    return {
        'base_multiple': base_multiple,
        'stage_multiplier': stage_mult,
        'jurisdiction_tier': jurisdiction_tier,
        'jurisdiction_discount': jurisdiction_discount,
        'grade_adjustment': grade_adjustment,
        'final_multiple': final_multiple,
        'implied_value': implied_value,
        'value_range': {
            'low': low_value,
            'mid': implied_value,
            'high': high_value
        },
        'commodity': commodity,
        'resource_estimate': resource_estimate,
        'resource_category': resource_category,
        'stage': stage,
        'jurisdiction': jurisdiction,
        'calculation_date': datetime.now().isoformat()
    }


def get_comparable_peers(commodity: str, stage: Optional[str] = None, jurisdiction: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Fetch comparable projects from database for peer benchmarking
    """
    db = SessionLocal()
    try:
        query = db.query(ComparableProject).filter(
            ComparableProject.approved_for_display == True,
            ComparableProject.status == 'active'
        )
        
        # Filter by commodity (primary filter)
        if commodity:
            query = query.filter(
                func.lower(ComparableProject.commodity).contains(commodity.lower())
            )
        
        # Optional stage filter
        if stage:
            query = query.filter(
                func.lower(ComparableProject.development_stage).contains(stage.lower())
            )
        
        projects = query.order_by(ComparableProject.created_at.desc()).limit(limit).all()
        
        result = []
        for project in projects:
            result.append({
                'id': project.id,
                'project_name': project.project_name,
                'company': project.company,
                'commodity': project.commodity,
                'deposit_type': project.deposit_type,
                'development_stage': project.development_stage,
                'jurisdiction': project.jurisdiction,
                'resource_moz': project.resource_moz,
                'grade_gpt': project.grade_gpt,
                'investment_score': project.investment_score,
                'sustainability_score': project.sustainability_score,
            })
        
        return result
    finally:
        db.close()


def calculate_peer_statistics(peers: List[Dict], commodity: str) -> Dict:
    """
    Calculate statistics from peer group for benchmarking
    """
    if not peers:
        return {
            'count': 0,
            'avg_ev_per_oz': None,
            'median_ev_per_oz': None,
            'percentile_25': None,
            'percentile_75': None,
        }
    
    # For now, use industry benchmarks
    # In production, this would calculate from actual transaction data
    base_multiple = get_base_multiple(commodity, 'indicated')
    
    return {
        'count': len(peers),
        'avg_ev_per_oz': base_multiple,
        'median_ev_per_oz': base_multiple * 0.95,
        'percentile_25': base_multiple * 0.75,
        'percentile_75': base_multiple * 1.25,
        'min': base_multiple * 0.50,
        'max': base_multiple * 1.50,
    }


def render_market_multiples_analysis():
    """Render the Market Multiples analysis UI in Streamlit"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e3a5f, #2d5a87); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: white; margin: 0;'>📊 Market Multiples Valuation</h3>
        <p style='color: #e0e0e0; margin: 5px 0 0 0;'>EV/Resource benchmarking based on industry transactions</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Project Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        commodity = st.selectbox(
            "Primary Commodity",
            ["Gold", "Silver", "Copper", "Zinc", "Nickel", "Lithium", "Uranium"],
            help="Select the primary commodity for valuation"
        )
        
        resource_estimate = st.number_input(
            "Resource Estimate (oz/lbs/tonnes)",
            min_value=0.0,
            value=1000000.0,
            step=100000.0,
            format="%.0f",
            help="Enter total resource in appropriate units (oz for precious metals, lbs for base metals)"
        )
        
        grade = st.number_input(
            "Average Grade (g/t or %)",
            min_value=0.0,
            value=1.5,
            step=0.1,
            format="%.2f",
            help="Enter average grade for premium adjustment"
        )
    
    with col2:
        resource_category = st.selectbox(
            "Resource Category",
            ["Inferred", "Indicated", "Measured", "M&I (Measured + Indicated)", "P&P (Proven + Probable)"],
            help="Higher confidence categories command higher multiples"
        )
        
        stage = st.selectbox(
            "Development Stage",
            ["Exploration", "Resource", "Feasibility", "Development", "Production"],
            help="Later stage projects command premium multiples"
        )
        
        jurisdiction = st.selectbox(
            "Jurisdiction",
            ["Canada", "Australia", "USA", "Chile", "Mexico", "Peru", "Brazil", "South Africa", 
             "DRC", "Guinea", "Indonesia", "Other"],
            help="Tier 1 jurisdictions have lower risk discount"
        )
    
    st.markdown("---")
    
    if st.button("🔍 Calculate Valuation", type="primary", use_container_width=True):
        with st.spinner("Calculating market multiples valuation..."):
            # Perform valuation
            result = calculate_ev_resource_valuation(
                commodity=commodity,
                resource_estimate=resource_estimate,
                resource_category=resource_category,
                stage=stage,
                jurisdiction=jurisdiction,
                grade=grade
            )
            
            # Store in session state
            st.session_state['market_multiples_result'] = result
            
            # Display results
            st.markdown("### 📈 Valuation Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Base Multiple",
                    f"${result['base_multiple']:.2f}/oz",
                    help="Industry standard multiple for commodity and category"
                )
            
            with col2:
                st.metric(
                    "Adjusted Multiple",
                    f"${result['final_multiple']:.2f}/oz",
                    delta=f"{((result['final_multiple']/result['base_multiple'])-1)*100:.1f}%",
                    help="Multiple after stage, jurisdiction, and grade adjustments"
                )
            
            with col3:
                st.metric(
                    "Implied Value",
                    format_currency(result['implied_value']/1e6, decimals=1),
                    help="Calculated enterprise value"
                )
            
            # Value range
            st.markdown("#### Valuation Range")
            
            range_data = result['value_range']
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style='background: #fff3e0; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>Low Case (-20%)</div>
                    <div style='font-size: 24px; font-weight: bold; color: #e65100;'>{format_currency(range_data['low']/1e6, decimals=1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style='background: #e8f5e9; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>Base Case</div>
                    <div style='font-size: 24px; font-weight: bold; color: #2e7d32;'>{format_currency(range_data['mid']/1e6, decimals=1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style='background: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center;'>
                    <div style='font-size: 14px; color: #666;'>High Case (+20%)</div>
                    <div style='font-size: 24px; font-weight: bold; color: #1565c0;'>{format_currency(range_data['high']/1e6, decimals=1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Adjustment breakdown
            st.markdown("#### Adjustment Factors")
            
            st.markdown(f"""
            | Factor | Value | Impact |
            |--------|-------|--------|
            | Stage Multiplier | {result['stage_multiplier']:.2f}x | {stage} stage adjustment |
            | Jurisdiction Discount | {result['jurisdiction_discount']:.0%} | {result['jurisdiction_tier'].replace('_', ' ').title()} ({jurisdiction}) |
            | Grade Adjustment | {result['grade_adjustment']:.0%} | {"Premium" if result['grade_adjustment'] > 1 else "Discount" if result['grade_adjustment'] < 1 else "Neutral"} |
            """)
            
            # Peer comparison
            st.markdown("#### 🔄 Peer Comparison")
            
            peers = get_comparable_peers(commodity, stage.lower())
            
            if peers:
                st.markdown(f"Found **{len(peers)}** comparable {commodity} projects in database:")
                
                for peer in peers[:5]:
                    with st.expander(f"📍 {peer['project_name']} ({peer['company']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Commodity:** {peer['commodity']}")
                            st.markdown(f"**Stage:** {peer['development_stage']}")
                            st.markdown(f"**Jurisdiction:** {peer['jurisdiction']}")
                        with col2:
                            if peer.get('resource_moz'):
                                st.markdown(f"**Resource:** {peer['resource_moz']:.2f} Moz")
                            if peer.get('grade_gpt'):
                                st.markdown(f"**Grade:** {peer['grade_gpt']:.2f} g/t")
                            if peer.get('investment_score'):
                                st.markdown(f"**Investment Score:** {peer['investment_score']}/100")
            else:
                st.info(f"No comparable {commodity} projects found in database. Using industry benchmark multiples.")
            
            st.success("Market multiples valuation complete!")


def get_valuation_for_report(project_data: Dict) -> Optional[Dict]:
    """
    Generate valuation for PDF report generation
    """
    if not project_data:
        return None
    
    commodity = project_data.get('commodity', 'Gold')
    resource_estimate = project_data.get('resource_estimate', 0)
    resource_category = project_data.get('resource_category', 'Inferred')
    stage = project_data.get('stage', 'Exploration')
    jurisdiction = project_data.get('jurisdiction', 'Unknown')
    grade = project_data.get('grade')
    
    if resource_estimate <= 0:
        return None
    
    return calculate_ev_resource_valuation(
        commodity=commodity,
        resource_estimate=resource_estimate,
        resource_category=resource_category,
        stage=stage,
        jurisdiction=jurisdiction,
        grade=grade
    )
