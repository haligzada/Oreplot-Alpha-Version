"""
Kilburn Method / PwC Cost Approach Valuation Engine
Implements geoscientific rating system for early-stage exploration valuation
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


# Kilburn Geoscientific Rating Factors (1-4 scale)
RATING_FACTORS = {
    'regional_prospectivity': {
        'name': 'Regional Prospectivity',
        'description': 'Geological setting and regional mineral potential',
        'levels': {
            1: {'name': 'Low', 'desc': 'Limited geological potential, unfavorable setting'},
            2: {'name': 'Moderate', 'desc': 'Some favorable indicators, limited past success'},
            3: {'name': 'High', 'desc': 'Favorable geological setting, nearby deposits'},
            4: {'name': 'Very High', 'desc': 'Proven mineral district, multiple nearby deposits'}
        }
    },
    'project_maturity': {
        'name': 'Project Maturity',
        'description': 'Stage of exploration and technical advancement',
        'levels': {
            1: {'name': 'Grassroots', 'desc': 'Early reconnaissance, no drilling'},
            2: {'name': 'Early Stage', 'desc': 'Initial drilling, target definition'},
            3: {'name': 'Advanced', 'desc': 'Systematic drilling, resource estimation'},
            4: {'name': 'Pre-Development', 'desc': 'Defined resource, economic studies'}
        }
    },
    'local_geology': {
        'name': 'Local Geology',
        'description': 'On-property geological indicators and mineralization',
        'levels': {
            1: {'name': 'Poor', 'desc': 'No significant surface indicators'},
            2: {'name': 'Fair', 'desc': 'Some favorable indicators, limited sampling'},
            3: {'name': 'Good', 'desc': 'Consistent mineralization, positive results'},
            4: {'name': 'Excellent', 'desc': 'High-grade intercepts, well-defined zones'}
        }
    },
    'analytical_data': {
        'name': 'Analytical Data Quality',
        'description': 'Quality and reliability of technical data',
        'levels': {
            1: {'name': 'Poor', 'desc': 'Limited assays, no QAQC'},
            2: {'name': 'Fair', 'desc': 'Basic sampling, limited verification'},
            3: {'name': 'Good', 'desc': 'Systematic sampling, QAQC protocols'},
            4: {'name': 'Excellent', 'desc': 'Comprehensive data, third-party verification'}
        }
    }
}

# Prospectivity Enhancement Multiplier (PEM) ranges
PEM_RANGES = {
    'very_low': {'min': 0.5, 'max': 1.0, 'desc': 'Low confidence, high-risk'},
    'low': {'min': 1.0, 'max': 1.5, 'desc': 'Below average prospectivity'},
    'moderate': {'min': 1.5, 'max': 2.0, 'desc': 'Average exploration potential'},
    'high': {'min': 2.0, 'max': 3.0, 'desc': 'Above average prospectivity'},
    'very_high': {'min': 3.0, 'max': 5.0, 'desc': 'Exceptional potential, defined targets'}
}

# Base acquisition cost (BAC) per hectare by region (USD)
BAC_PER_HECTARE = {
    'north_america': 25.0,
    'south_america': 15.0,
    'australia': 20.0,
    'africa': 10.0,
    'europe': 30.0,
    'asia': 12.0,
    'other': 15.0,
}


def calculate_kilburn_rating(
    regional_prospectivity: int,
    project_maturity: int,
    local_geology: int,
    analytical_data: int
) -> Tuple[float, str]:
    """
    Calculate Kilburn geoscientific rating
    
    Args:
        regional_prospectivity: Rating 1-4
        project_maturity: Rating 1-4
        local_geology: Rating 1-4
        analytical_data: Rating 1-4
    
    Returns:
        Tuple of (composite rating, rating category)
    """
    # Validate inputs
    ratings = [regional_prospectivity, project_maturity, local_geology, analytical_data]
    for r in ratings:
        if r < 1 or r > 4:
            raise ValueError(f"Rating must be between 1 and 4, got {r}")
    
    # Calculate average rating
    avg_rating = sum(ratings) / len(ratings)
    
    # Determine category
    if avg_rating <= 1.5:
        category = 'very_low'
    elif avg_rating <= 2.0:
        category = 'low'
    elif avg_rating <= 2.5:
        category = 'moderate'
    elif avg_rating <= 3.0:
        category = 'high'
    else:
        category = 'very_high'
    
    return avg_rating, category


def calculate_pem(rating: float, category: str) -> float:
    """
    Calculate Prospectivity Enhancement Multiplier based on rating
    """
    pem_range = PEM_RANGES[category]
    
    # Linear interpolation within category range
    if category == 'very_low':
        normalized = (rating - 1.0) / 0.5
    elif category == 'low':
        normalized = (rating - 1.5) / 0.5
    elif category == 'moderate':
        normalized = (rating - 2.0) / 0.5
    elif category == 'high':
        normalized = (rating - 2.5) / 0.5
    else:
        normalized = (rating - 3.0) / 1.0
    
    normalized = max(0, min(1, normalized))
    
    pem = pem_range['min'] + (pem_range['max'] - pem_range['min']) * normalized
    
    return round(pem, 2)


def calculate_mee_valuation(
    exploration_expenditure: float,
    pem: float,
    years_since_expenditure: int = 0,
    inflation_rate: float = 0.03
) -> Dict:
    """
    Calculate Multiple of Exploration Expenditure (MEE) valuation
    
    Args:
        exploration_expenditure: Total exploration expenditure (USD)
        pem: Prospectivity Enhancement Multiplier
        years_since_expenditure: Years since expenditure for inflation adjustment
        inflation_rate: Annual inflation rate for adjustment
    
    Returns:
        Dictionary with MEE valuation details
    """
    # Adjust for inflation
    inflation_factor = (1 + inflation_rate) ** years_since_expenditure
    adjusted_expenditure = exploration_expenditure * inflation_factor
    
    # Calculate appraised value
    appraised_value = adjusted_expenditure * pem
    
    # Calculate range (±15%)
    low_value = appraised_value * 0.85
    high_value = appraised_value * 1.15
    
    return {
        'exploration_expenditure': exploration_expenditure,
        'adjusted_expenditure': adjusted_expenditure,
        'inflation_adjustment': inflation_factor,
        'pem': pem,
        'appraised_value': appraised_value,
        'value_range': {
            'low': low_value,
            'mid': appraised_value,
            'high': high_value
        },
        'methodology': 'Multiple of Exploration Expenditure (MEE)',
        'calculation_date': datetime.now().isoformat()
    }


def calculate_bac_valuation(
    area_hectares: float,
    region: str,
    pem: float
) -> Dict:
    """
    Calculate Base Acquisition Cost valuation
    
    Args:
        area_hectares: Property area in hectares
        region: Geographic region
        pem: Prospectivity Enhancement Multiplier
    
    Returns:
        Dictionary with BAC valuation details
    """
    # Get BAC per hectare
    region_lower = region.lower().replace(' ', '_')
    if 'north america' in region_lower or 'canada' in region_lower or 'usa' in region_lower:
        bac = BAC_PER_HECTARE['north_america']
        region_key = 'north_america'
    elif 'south america' in region_lower or 'peru' in region_lower or 'chile' in region_lower or 'brazil' in region_lower:
        bac = BAC_PER_HECTARE['south_america']
        region_key = 'south_america'
    elif 'australia' in region_lower:
        bac = BAC_PER_HECTARE['australia']
        region_key = 'australia'
    elif 'africa' in region_lower or 'drc' in region_lower or 'mali' in region_lower:
        bac = BAC_PER_HECTARE['africa']
        region_key = 'africa'
    elif 'europe' in region_lower:
        bac = BAC_PER_HECTARE['europe']
        region_key = 'europe'
    elif 'asia' in region_lower or 'indonesia' in region_lower or 'philippines' in region_lower:
        bac = BAC_PER_HECTARE['asia']
        region_key = 'asia'
    else:
        bac = BAC_PER_HECTARE['other']
        region_key = 'other'
    
    # Calculate base value
    base_value = area_hectares * bac
    
    # Apply PEM
    appraised_value = base_value * pem
    
    # Calculate range (±20%)
    low_value = appraised_value * 0.80
    high_value = appraised_value * 1.20
    
    return {
        'area_hectares': area_hectares,
        'region': region,
        'bac_per_hectare': bac,
        'base_value': base_value,
        'pem': pem,
        'appraised_value': appraised_value,
        'value_range': {
            'low': low_value,
            'mid': appraised_value,
            'high': high_value
        },
        'methodology': 'Base Acquisition Cost (BAC)',
        'calculation_date': datetime.now().isoformat()
    }


def calculate_kilburn_valuation(
    regional_prospectivity: int,
    project_maturity: int,
    local_geology: int,
    analytical_data: int,
    exploration_expenditure: float = 0,
    area_hectares: float = 0,
    region: str = 'North America',
    years_since_expenditure: int = 0
) -> Dict:
    """
    Complete Kilburn/Cost Approach valuation combining geoscientific rating with MEE and BAC
    """
    # Calculate Kilburn rating
    rating, category = calculate_kilburn_rating(
        regional_prospectivity, project_maturity, local_geology, analytical_data
    )
    
    # Calculate PEM
    pem = calculate_pem(rating, category)
    
    result = {
        'geoscientific_rating': {
            'regional_prospectivity': regional_prospectivity,
            'project_maturity': project_maturity,
            'local_geology': local_geology,
            'analytical_data': analytical_data,
            'composite_rating': rating,
            'category': category,
        },
        'pem': pem,
        'calculation_date': datetime.now().isoformat()
    }
    
    # Calculate MEE if expenditure provided
    if exploration_expenditure > 0:
        mee_result = calculate_mee_valuation(
            exploration_expenditure, pem, years_since_expenditure
        )
        result['mee_valuation'] = mee_result
    
    # Calculate BAC if area provided
    if area_hectares > 0:
        bac_result = calculate_bac_valuation(area_hectares, region, pem)
        result['bac_valuation'] = bac_result
    
    # Determine preferred valuation
    if exploration_expenditure > 0 and area_hectares > 0:
        # Use higher of MEE or BAC
        if result['mee_valuation']['appraised_value'] > result['bac_valuation']['appraised_value']:
            result['preferred_valuation'] = result['mee_valuation']['appraised_value']
            result['preferred_methodology'] = 'MEE'
        else:
            result['preferred_valuation'] = result['bac_valuation']['appraised_value']
            result['preferred_methodology'] = 'BAC'
    elif exploration_expenditure > 0:
        result['preferred_valuation'] = result['mee_valuation']['appraised_value']
        result['preferred_methodology'] = 'MEE'
    elif area_hectares > 0:
        result['preferred_valuation'] = result['bac_valuation']['appraised_value']
        result['preferred_methodology'] = 'BAC'
    else:
        result['preferred_valuation'] = None
        result['preferred_methodology'] = None
    
    return result


def generate_kilburn_from_extraction(extracted_data: Dict) -> Dict:
    """
    Generate Kilburn valuation from AI-extracted document data
    
    Args:
        extracted_data: Data extracted from documents by GPT-5.1
    
    Returns:
        Complete Kilburn/Cost Approach valuation
    """
    project_info = extracted_data.get('project_info', {})
    exploration = extracted_data.get('exploration', {})
    
    regional = exploration.get('regional_prospectivity', 0)
    if regional == 0 or regional is None:
        stage = project_info.get('development_stage', '').lower()
        if 'production' in stage or 'construction' in stage:
            regional = 4
        elif 'feasibility' in stage or 'permitted' in stage:
            regional = 3
        elif 'advanced' in stage or 'pre_feasibility' in stage:
            regional = 3
        elif 'exploration' in stage:
            regional = 2
        else:
            regional = 2
    regional = max(1, min(4, int(regional)))
    
    maturity = exploration.get('project_maturity_score', 0)
    if maturity == 0 or maturity is None:
        stage = project_info.get('development_stage', '').lower()
        if 'production' in stage:
            maturity = 4
        elif 'construction' in stage or 'permitted' in stage:
            maturity = 4
        elif 'feasibility' in stage:
            maturity = 3
        elif 'pre_feasibility' in stage or 'pfs' in stage:
            maturity = 3
        elif 'advanced' in stage:
            maturity = 2
        else:
            maturity = 2
    maturity = max(1, min(4, int(maturity)))
    
    geology = exploration.get('local_geology_score', 0)
    if geology == 0 or geology is None:
        resources = extracted_data.get('resources', {})
        total_mi = resources.get('total_mi_contained_metal', 0)
        if total_mi > 0:
            geology = 3
        else:
            geology = 2
    geology = max(1, min(4, int(geology)))
    
    data_quality = exploration.get('analytical_data_quality', 0)
    if data_quality == 0 or data_quality is None:
        report_type = extracted_data.get('data_quality', {}).get('report_type', '')
        if '43-101' in report_type or 'JORC' in report_type:
            data_quality = 3
        else:
            data_quality = 2
    data_quality = max(1, min(4, int(data_quality)))
    
    exploration_spend = exploration.get('historical_exploration_spend', 0)
    if exploration_spend == 0:
        drill_meters = exploration.get('drill_meters_completed', 0)
        exploration_spend = drill_meters * 0.0003
    
    area_km2 = project_info.get('property_area_km2', 0)
    area_hectares = area_km2 * 100 if area_km2 > 0 else 1000
    
    location = project_info.get('location', 'Unknown')
    jurisdiction = project_info.get('jurisdiction', 'Tier 2')
    if 'canada' in location.lower() or 'australia' in location.lower() or 'usa' in location.lower():
        region = 'North America'
    elif 'chile' in location.lower() or 'peru' in location.lower() or 'mexico' in location.lower():
        region = 'South America'
    elif 'africa' in location.lower():
        region = 'Africa'
    else:
        region = 'North America'
    
    result = calculate_kilburn_valuation(
        regional_prospectivity=regional,
        project_maturity=maturity,
        local_geology=geology,
        analytical_data=data_quality,
        exploration_expenditure=exploration_spend,
        area_hectares=area_hectares,
        region=region,
        years_since_expenditure=0
    )
    
    preferred_value = result.get('preferred_valuation', 0)
    composite_rating = result.get('geoscientific_rating', {}).get('composite_rating', 0)
    if preferred_value and preferred_value > 0:
        if composite_rating >= 3.0:
            recommendation = "Strong Floor Value - Exploration upside significant"
            color = "green"
        elif composite_rating >= 2.5:
            recommendation = "Solid Floor Value - Additional work warranted"
            color = "blue"
        else:
            recommendation = "Low Floor Value - High exploration risk"
            color = "orange"
    else:
        recommendation = "Insufficient Data - Cannot calculate floor value"
        color = "red"
    
    result['recommendation'] = {
        'text': recommendation,
        'color': color
    }
    
    result['valuation_summary'] = {
        'recommended_value': preferred_value if preferred_value else 0,
        'methodology': result.get('preferred_methodology', 'Unknown'),
        'pem': result.get('pem', 1.0),
        'average_rating': result.get('geoscientific_rating', {}).get('composite_rating', 0)
    }
    
    return result


def render_kilburn_analysis():
    """Render the Kilburn/Cost Approach analysis UI in Streamlit"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #4a148c, #7b1fa2); padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: white; margin: 0;'>🔬 PwC Cost Approach Valuation</h3>
        <p style='color: #e0e0e0; margin: 5px 0 0 0;'>Kilburn geoscientific rating with MEE methodology</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    The Cost Approach is the preferred methodology for early-stage exploration properties 
    where DCF analysis is not appropriate. It uses geoscientific rating to adjust historical 
    exploration expenditure.
    """)
    
    st.markdown("### Geoscientific Rating Factors")
    st.markdown("Rate each factor from 1 (Low) to 4 (Very High)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Regional Prospectivity")
        regional_prospectivity = st.slider(
            "Geological setting and regional mineral potential",
            min_value=1, max_value=4, value=2,
            help="1=Limited potential | 2=Some indicators | 3=Favorable setting | 4=Proven district"
        )
        
        st.markdown(f"**Selected:** {RATING_FACTORS['regional_prospectivity']['levels'][regional_prospectivity]['name']}")
        st.caption(RATING_FACTORS['regional_prospectivity']['levels'][regional_prospectivity]['desc'])
        
        st.markdown("---")
        
        st.markdown("#### Project Maturity")
        project_maturity = st.slider(
            "Stage of exploration and technical advancement",
            min_value=1, max_value=4, value=2,
            help="1=Grassroots | 2=Early Stage | 3=Advanced | 4=Pre-Development"
        )
        
        st.markdown(f"**Selected:** {RATING_FACTORS['project_maturity']['levels'][project_maturity]['name']}")
        st.caption(RATING_FACTORS['project_maturity']['levels'][project_maturity]['desc'])
    
    with col2:
        st.markdown("#### Local Geology")
        local_geology = st.slider(
            "On-property geological indicators",
            min_value=1, max_value=4, value=2,
            help="1=Poor indicators | 2=Fair | 3=Good | 4=Excellent mineralization"
        )
        
        st.markdown(f"**Selected:** {RATING_FACTORS['local_geology']['levels'][local_geology]['name']}")
        st.caption(RATING_FACTORS['local_geology']['levels'][local_geology]['desc'])
        
        st.markdown("---")
        
        st.markdown("#### Analytical Data Quality")
        analytical_data = st.slider(
            "Quality and reliability of technical data",
            min_value=1, max_value=4, value=2,
            help="1=Poor QAQC | 2=Fair | 3=Good protocols | 4=Excellent verification"
        )
        
        st.markdown(f"**Selected:** {RATING_FACTORS['analytical_data']['levels'][analytical_data]['name']}")
        st.caption(RATING_FACTORS['analytical_data']['levels'][analytical_data]['desc'])
    
    st.markdown("---")
    st.markdown("### Cost Inputs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        exploration_expenditure = st.number_input(
            "Historical Exploration Expenditure (USD)",
            min_value=0.0,
            value=5000000.0,
            step=500000.0,
            format="%.0f",
            help="Total exploration spending to date"
        )
        
        years_since = st.number_input(
            "Years Since Expenditure",
            min_value=0,
            max_value=20,
            value=2,
            help="For inflation adjustment"
        )
    
    with col2:
        area_hectares = st.number_input(
            "Property Area (hectares)",
            min_value=0.0,
            value=10000.0,
            step=1000.0,
            format="%.0f",
            help="Total area of mineral claims"
        )
        
        region = st.selectbox(
            "Geographic Region",
            ["North America", "South America", "Australia", "Africa", "Europe", "Asia"],
            help="Region affects base acquisition cost"
        )
    
    st.markdown("---")
    
    if st.button("🔬 Calculate Kilburn Valuation", type="primary", use_container_width=True):
        with st.spinner("Calculating cost approach valuation..."):
            # Calculate valuation
            result = calculate_kilburn_valuation(
                regional_prospectivity=regional_prospectivity,
                project_maturity=project_maturity,
                local_geology=local_geology,
                analytical_data=analytical_data,
                exploration_expenditure=exploration_expenditure,
                area_hectares=area_hectares,
                region=region,
                years_since_expenditure=years_since
            )
            
            # Store in session state
            st.session_state['kilburn_result'] = result
            
            # Display results
            st.markdown("### 📊 Valuation Results")
            
            # Geoscientific rating summary
            rating_data = result['geoscientific_rating']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Composite Rating",
                    f"{rating_data['composite_rating']:.2f}/4.00",
                    help="Average of all four factors"
                )
            
            with col2:
                st.metric(
                    "Rating Category",
                    rating_data['category'].replace('_', ' ').title(),
                    help="Overall prospectivity category"
                )
            
            with col3:
                st.metric(
                    "PEM Multiplier",
                    f"{result['pem']:.2f}x",
                    help="Prospectivity Enhancement Multiplier"
                )
            
            # Rating breakdown
            st.markdown("#### Rating Factor Breakdown")
            
            factor_cols = st.columns(4)
            factors = [
                ('regional_prospectivity', '🌍 Regional', rating_data['regional_prospectivity']),
                ('project_maturity', '📈 Maturity', rating_data['project_maturity']),
                ('local_geology', '⛰️ Local', rating_data['local_geology']),
                ('analytical_data', '📊 Data', rating_data['analytical_data'])
            ]
            
            for i, (key, label, value) in enumerate(factors):
                with factor_cols[i]:
                    color = ['#ef5350', '#ff9800', '#4caf50', '#2196f3'][value - 1]
                    st.markdown(f"""
                    <div style='background: {color}; padding: 10px; border-radius: 8px; text-align: center; color: white;'>
                        <div style='font-size: 12px;'>{label}</div>
                        <div style='font-size: 24px; font-weight: bold;'>{value}/4</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # MEE Valuation
            if 'mee_valuation' in result:
                mee = result['mee_valuation']
                st.markdown("#### MEE (Multiple of Exploration Expenditure)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Expenditure:** ${mee['exploration_expenditure']:,.0f}")
                    st.markdown(f"**Inflation Adj:** {mee['inflation_adjustment']:.2f}x")
                with col2:
                    st.markdown(f"**Adjusted Base:** ${mee['adjusted_expenditure']:,.0f}")
                    st.markdown(f"**PEM Applied:** {mee['pem']:.2f}x")
                with col3:
                    st.markdown(f"**Appraised Value:** ${mee['appraised_value']:,.0f}")
                    st.markdown(f"**Range:** ${mee['value_range']['low']:,.0f} - ${mee['value_range']['high']:,.0f}")
            
            # BAC Valuation
            if 'bac_valuation' in result:
                bac = result['bac_valuation']
                st.markdown("#### BAC (Base Acquisition Cost)")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Area:** {bac['area_hectares']:,.0f} hectares")
                    st.markdown(f"**BAC/ha:** ${bac['bac_per_hectare']:.2f}")
                with col2:
                    st.markdown(f"**Base Value:** ${bac['base_value']:,.0f}")
                    st.markdown(f"**PEM Applied:** {bac['pem']:.2f}x")
                with col3:
                    st.markdown(f"**Appraised Value:** ${bac['appraised_value']:,.0f}")
                    st.markdown(f"**Range:** ${bac['value_range']['low']:,.0f} - ${bac['value_range']['high']:,.0f}")
            
            # Preferred Valuation
            if result.get('preferred_valuation'):
                st.markdown("---")
                st.markdown("#### 🎯 Recommended Valuation")
                
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #1b5e20, #388e3c); padding: 20px; border-radius: 10px; text-align: center;'>
                    <div style='color: #a5d6a7; font-size: 14px;'>Preferred Methodology: {result['preferred_methodology']}</div>
                    <div style='color: white; font-size: 32px; font-weight: bold;'>${result['preferred_valuation']:,.0f}</div>
                    <div style='color: #a5d6a7; font-size: 12px;'>Based on higher of MEE or BAC approach</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.success("Cost approach valuation complete!")


def get_kilburn_for_report(
    ratings: Dict,
    exploration_expenditure: float = 0,
    area_hectares: float = 0,
    region: str = 'North America'
) -> Optional[Dict]:
    """
    Generate Kilburn valuation for PDF report
    """
    if not ratings:
        return None
    
    return calculate_kilburn_valuation(
        regional_prospectivity=ratings.get('regional_prospectivity', 2),
        project_maturity=ratings.get('project_maturity', 2),
        local_geology=ratings.get('local_geology', 2),
        analytical_data=ratings.get('analytical_data', 2),
        exploration_expenditure=exploration_expenditure,
        area_hectares=area_hectares,
        region=region
    )
