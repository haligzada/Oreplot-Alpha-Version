import streamlit as st
from database import SessionLocal
from comparables_manager import ComparablesManager
from models import ComparableProject

def render_comparables_page():
    """Render the Global Comparables Database page"""
    st.markdown("<h1 style='background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem;'>🌍 Global Comparables Database</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B; font-size: 1.1rem; margin-bottom: 2rem;'>Benchmark your mining projects against real-world analogues</p>", unsafe_allow_html=True)
    
    db = SessionLocal()
    
    try:
        tabs = st.tabs(["🔍 Browse Projects", "📊 Benchmark Statistics", "ℹ️ About"])
        
        with tabs[0]:
            render_browse_comparables(db)
        
        with tabs[1]:
            render_benchmark_stats(db)
        
        with tabs[2]:
            render_about_section()
    
    finally:
        db.close()

def render_browse_comparables(db):
    """Render the browse comparables interface"""
    st.subheader("Browse Comparable Mining Projects")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search projects", placeholder="Project name, company, or location...")
    
    with col2:
        commodity_filter = st.selectbox(
            "Commodity",
            ["All", "Copper", "Gold", "Lithium", "Nickel", "Zinc", "Silver", "PGM"],
            index=0
        )
    
    with col3:
        stage_filter = st.selectbox(
            "Project Stage",
            ["All", "exploration", "development", "production"],
            index=0
        )
    
    col4, col5 = st.columns(2)
    with col4:
        min_score = st.slider("Minimum Overall Score", 0.0, 10.0, 0.0, 0.5)
    with col5:
        max_score = st.slider("Maximum Overall Score", 0.0, 10.0, 10.0, 0.5)
    
    filters = {}
    if search_term:
        filters['search'] = search_term
    if commodity_filter != "All":
        filters['commodity'] = commodity_filter
    if stage_filter != "All":
        filters['project_stage'] = stage_filter
    if min_score > 0:
        filters['min_score'] = min_score
    if max_score < 10:
        filters['max_score'] = max_score
    
    comparables = ComparablesManager.get_all_comparables(db, filters)
    
    st.markdown(f"**Found {len(comparables)} projects**")
    
    if not comparables:
        st.info("No projects match your search criteria. Try adjusting the filters.")
        return
    
    for comp in comparables:
        with st.expander(f"**{comp.name}** - {comp.commodity or 'N/A'} ({comp.project_stage or 'N/A'})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Project Details")
                st.markdown(f"**Company:** {comp.company or 'N/A'}")
                st.markdown(f"**Location:** {comp.location}, {comp.country}" if comp.location and comp.country else f"{comp.country or comp.location or 'N/A'}")
                st.markdown(f"**Commodity:** {comp.commodity or 'N/A'}")
                st.markdown(f"**Stage:** {comp.project_stage or 'N/A'}")
                st.markdown(f"**Status:** {comp.status or 'N/A'}")
            
            with col2:
                st.markdown("#### Resource & Economics")
                if comp.total_resource_mt and comp.grade:
                    st.markdown(f"**Resource:** {comp.total_resource_mt:.1f} Mt @ {comp.grade:.2f} {comp.grade_unit or ''}")
                if comp.capex_millions_usd:
                    st.markdown(f"**CAPEX:** ${comp.capex_millions_usd:.0f}M USD")
                if comp.npv_millions_usd:
                    st.markdown(f"**NPV:** ${comp.npv_millions_usd:.0f}M USD")
                if comp.irr_percent:
                    st.markdown(f"**IRR:** {comp.irr_percent:.1f}%")
                if comp.mine_life_years:
                    st.markdown(f"**Mine Life:** {comp.mine_life_years:.0f} years")
            
            with col3:
                st.markdown("#### Scores")
                if comp.overall_score:
                    st.metric("Overall Score", f"{comp.overall_score:.1f}/10")
                
                score_cols = st.columns(2)
                with score_cols[0]:
                    if comp.geology_score:
                        st.markdown(f"**Geology:** {comp.geology_score:.1f}/10")
                    if comp.resource_score:
                        st.markdown(f"**Resource:** {comp.resource_score:.1f}/10")
                    if comp.economics_score:
                        st.markdown(f"**Economics:** {comp.economics_score:.1f}/10")
                
                with score_cols[1]:
                    if comp.legal_score:
                        st.markdown(f"**Legal:** {comp.legal_score:.1f}/10")
                    if comp.permitting_score:
                        st.markdown(f"**Permitting:** {comp.permitting_score:.1f}/10")
                    if comp.data_quality_score:
                        st.markdown(f"**Data Quality:** {comp.data_quality_score:.1f}/10")
            
            if comp.notes:
                st.markdown("---")
                st.markdown(f"**Notes:** {comp.notes}")
            
            if comp.data_source:
                st.markdown(f"**Source:** {comp.data_source}")

def render_benchmark_stats(db):
    """Render benchmark statistics"""
    st.subheader("Benchmark Statistics")
    
    commodity_filter = st.selectbox(
        "Filter by Commodity",
        ["All Commodities", "Copper", "Gold", "Lithium", "Nickel", "Zinc"],
        key="stats_commodity"
    )
    
    commodity = None if commodity_filter == "All Commodities" else commodity_filter
    stats = ComparablesManager.get_benchmark_stats(db, commodity)
    
    st.markdown(f"### Statistics for {commodity_filter}")
    st.markdown(f"**Total Projects:** {stats['total_projects']}")
    
    st.markdown("### Average Scores")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Score", f"{stats['avg_overall_score']:.2f}/10")
        st.metric("Geology Score", f"{stats['avg_geology_score']:.2f}/10")
    
    with col2:
        st.metric("Resource Score", f"{stats['avg_resource_score']:.2f}/10")
        st.metric("Economics Score", f"{stats['avg_economics_score']:.2f}/10")
    
    with col3:
        st.metric("Legal Score", f"{stats['avg_legal_score']:.2f}/10")
        st.metric("Permitting Score", f"{stats['avg_permitting_score']:.2f}/10")
    
    st.markdown("### Economic Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if stats['avg_capex_millions'] > 0:
            st.metric("Avg CAPEX", f"${stats['avg_capex_millions']:.0f}M USD")
    
    with col2:
        if stats['avg_npv_millions'] > 0:
            st.metric("Avg NPV", f"${stats['avg_npv_millions']:.0f}M USD")
    
    with col3:
        if stats['avg_irr_percent'] > 0:
            st.metric("Avg IRR", f"{stats['avg_irr_percent']:.1f}%")

def render_about_section():
    """Render about section for comparables database"""
    st.markdown("""
    ### About the Global Comparables Database
    
    The Global Comparables Database contains reference data from real mining projects worldwide, 
    enabling you to benchmark your projects against industry standards and similar assets.
    
    #### Data Sources
    - NI 43-101 Technical Reports
    - Prefeasibility and Feasibility Studies
    - Company investor presentations
    - Public filings and disclosures
    - Industry databases and reports
    
    #### Key Features
    - **Comprehensive Coverage**: Projects across all commodities and development stages
    - **Detailed Metrics**: Resource estimates, economics, scores, and risk factors
    - **Benchmarking**: Compare your projects against similar assets
    - **Statistical Analysis**: Industry averages and percentile rankings
    
    #### Use Cases
    - Validate project valuations
    - Assess project competitiveness
    - Identify peer groups
    - Support investment decisions
    - Due diligence reference
    
    #### Data Quality
    All data is sourced from public disclosures and technical reports. Quality ratings 
    indicate reliability of source data (High, Medium, Low).
    """)
