"""
Oreplot Advanced Valuation Page
AI-powered document analysis with 5 professional valuation methodologies
Design matches Light AI with project inputs and document upload
"""

import streamlit as st
import io
from datetime import datetime
from typing import Dict, Any, List

from ai_access_control import (
    has_advanced_ai_access, 
    get_tier_display_name,
    ADVANCED_AI_FEATURES,
    get_upgrade_message
)
from document_extractor import DocumentExtractor
from advanced_ai_analyzer import AdvancedAIAnalyzer
from format_utils import format_currency
from report_generator import ReportGenerator
from components.ai_chat import render_chat_interface, render_compact_chat_input, set_context, init_chat_state


def render_advanced_ai_page(current_user: dict):
    """Render the Oreplot Advanced analysis page with document upload and valuation"""
    
    if not has_advanced_ai_access(current_user):
        render_access_denied(current_user)
        return
    
    st.markdown("""
        <h1 style='background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem;'>
            🟣 Oreplot Advanced Valuation Agent
        </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <p style='color: #64748B; font-size: 1.1rem; margin-bottom: 1.5rem;'>
            Upload your data room documents and let AI calculate project value using 5 professional valuation methodologies
        </p>
    """, unsafe_allow_html=True)
    
    if 'advanced_view_mode' not in st.session_state:
        st.session_state.advanced_view_mode = 'new_analysis'
    if 'advanced_analysis_result' not in st.session_state:
        st.session_state.advanced_analysis_result = None
    if 'advanced_extracted_docs' not in st.session_state:
        st.session_state.advanced_extracted_docs = None
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 New Analysis", use_container_width=True,
                    type="primary" if st.session_state.advanced_view_mode == 'new_analysis' else "secondary"):
            st.session_state.advanced_view_mode = 'new_analysis'
            st.rerun()
    with col2:
        if st.button("📊 View Results", use_container_width=True,
                    type="primary" if st.session_state.advanced_view_mode == 'results' else "secondary",
                    disabled=st.session_state.advanced_analysis_result is None):
            st.session_state.advanced_view_mode = 'results'
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.advanced_view_mode == 'new_analysis':
        render_new_analysis_form(current_user)
    elif st.session_state.advanced_view_mode == 'results':
        render_analysis_results(current_user)


def render_new_analysis_form(current_user: dict):
    """Render the new analysis form with project inputs and document upload"""
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #8B5CF6 0%, #A855F7 50%, #EC4899 100%); 
                    padding: 20px; border-radius: 12px; margin-bottom: 20px;'>
            <h3 style='color: white; margin: 0;'>🎯 Advanced Valuation Analysis</h3>
            <p style='color: rgba(255,255,255,0.9); margin: 5px 0 0 0;'>
                Upload data room documents for comprehensive AI-powered valuation
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    render_valuation_methods_info()
    
    st.markdown("### 📋 Project Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input(
            "Project Name *",
            placeholder="e.g., Golden Ridge Gold Project",
            key="adv_project_name",
            help="Enter the name of the mining project"
        )
    
    with col2:
        primary_commodity = st.selectbox(
            "Primary Commodity",
            ["Gold", "Silver", "Copper", "Lithium", "Nickel", "Zinc", "Uranium", "Platinum", "Other"],
            key="adv_commodity",
            help="Select the primary commodity"
        )
    
    st.markdown("---")
    st.markdown("### 📁 Upload Data Room Documents")
    
    st.markdown("""
        <div style='background: #F0F9FF; padding: 15px; border-radius: 10px; 
                    border-left: 4px solid #0284C7; margin-bottom: 15px;'>
            <p style='color: #0369A1; margin: 0; font-size: 0.95rem;'>
                <strong>Supported Documents:</strong> PDF (NI 43-101, JORC, Feasibility Studies), 
                DOCX, XLSX, CSV, TXT • <strong>Maximum:</strong> 5GB total upload
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "Upload Technical Reports & Financial Data",
        type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        key="adv_uploaded_files",
        help="Upload NI 43-101, JORC reports, feasibility studies, financial models, resource estimates"
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        total_size = sum(f.size for f in uploaded_files)
        
        for f in uploaded_files[:10]:
            size_mb = f.size / (1024 * 1024)
            st.markdown(f"- `{f.name}` ({size_mb:.2f} MB)")
        
        if len(uploaded_files) > 10:
            st.markdown(f"*...and {len(uploaded_files) - 10} more files*")
        
        st.markdown(f"**Total size:** {total_size / (1024 * 1024):.2f} MB")
    
    st.markdown("---")
    
    init_chat_state("advanced_ai_chat")
    if uploaded_files:
        set_context("advanced_ai_chat", {
            "uploaded_files": [f.name for f in uploaded_files],
            "project_name": project_name,
            "analysis_result": st.session_state.get('advanced_analysis_result')
        })
    
    render_compact_chat_input(
        chat_key="advanced_ai_chat",
        ai_tier="advanced",
        placeholder_text="Share important details about your project or ask questions..."
    )
    
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        run_analysis = st.button(
            "🚀 Generate Advanced Valuation Analysis",
            type="primary",
            use_container_width=True,
            disabled=not (project_name and uploaded_files)
        )
    
    with col2:
        if st.button("🔄 Clear", use_container_width=True):
            st.session_state.advanced_analysis_result = None
            st.session_state.advanced_extracted_docs = None
            st.rerun()
    
    if not project_name:
        st.info("💡 Enter a project name and upload documents to generate analysis")
    elif not uploaded_files:
        st.info("💡 Upload at least one document to generate analysis")
    
    if run_analysis and project_name and uploaded_files:
        run_advanced_analysis(project_name, "", primary_commodity, uploaded_files, current_user)


def render_valuation_methods_info():
    """Render information about the 5 valuation methodologies"""
    
    with st.expander("📚 5 Professional Valuation Methodologies", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **1. Probability-Weighted DCF (Risk-Adjusted NPV)**
            - DCF multiplied by stage-gate success probabilities
            - Incorporates technical, geological, and execution risks
            
            **2. Monte Carlo Risk Modeling**
            - 10,000+ simulations with varying prices, grades, costs
            - Generates P10/P50/P90 distribution with VaR metrics
            
            **3. Income Approach - Discounted Cash Flow**
            - Cash flow projection based on production & costs
            - Represents intrinsic economic value under base case
            """)
        
        with col2:
            st.markdown("""
            **4. Cost Approach (Kilburn Method)**
            - Values early-stage exploration based on replacement cost
            - Considers past exploration spend and discovery potential
            
            **5. Decision Tree / Stage-Gate (EMV)**
            - Sequential decision model with costs and probabilities
            - Expected Monetary Value at each project stage
            """)


def run_advanced_analysis(project_name: str, description: str, commodity: str, 
                          uploaded_files: List, current_user: dict):
    """Run the complete advanced valuation analysis"""
    
    progress_bar = st.progress(0, text="Initializing analysis...")
    status_container = st.container()
    
    try:
        with status_container:
            st.info("📄 **Step 1/4:** Extracting text from documents...")
        progress_bar.progress(10, text="Extracting document text...")
        
        extracted_docs = []
        for i, file in enumerate(uploaded_files):
            file_bytes = file.read()
            file.seek(0)
            
            progress_bar.progress(
                10 + int(40 * (i + 1) / len(uploaded_files)),
                text=f"Processing: {file.name}..."
            )
            
            result = DocumentExtractor.extract_text(file.name, file_bytes)
            extracted_docs.append(result)
        
        st.session_state.advanced_extracted_docs = extracted_docs
        
        successful_docs = [d for d in extracted_docs if d.get('success')]
        
        with status_container:
            st.success(f"✅ Successfully extracted {len(successful_docs)}/{len(uploaded_files)} documents")
        
        if not successful_docs:
            st.error("❌ No documents could be processed. Please check file formats.")
            progress_bar.empty()
            return
        
        with status_container:
            st.info("🤖 **Step 2/4:** AI extracting financial and technical data...")
        progress_bar.progress(55, text="AI analyzing document content...")
        
        analysis_result = AdvancedAIAnalyzer.run_complete_analysis(extracted_docs)
        
        if 'error' in analysis_result and 'valuations' not in analysis_result:
            st.error(f"❌ Analysis error: {analysis_result['error']}")
            progress_bar.empty()
            return
        
        with status_container:
            st.info("📊 **Step 3/4:** Running 5 valuation methodologies...")
        progress_bar.progress(80, text="Calculating valuations...")
        
        analysis_result['project_name'] = project_name
        analysis_result['project_description'] = description
        analysis_result['primary_commodity'] = commodity
        analysis_result['uploaded_files'] = [f.name for f in uploaded_files]
        analysis_result['analysis_date'] = datetime.now().isoformat()
        analysis_result['user_id'] = current_user.get('id')
        
        with status_container:
            st.info("📝 **Step 4/4:** Generating valuation narrative...")
        progress_bar.progress(95, text="Generating narrative...")
        
        st.session_state.advanced_analysis_result = analysis_result
        
        progress_bar.progress(100, text="Analysis complete!")
        
        with status_container:
            st.success("🎉 **Advanced Valuation Analysis Complete!**")
        
        st.session_state.advanced_view_mode = 'results'
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        progress_bar.empty()


def render_analysis_results(current_user: dict):
    """Render the analysis results with all valuation methods"""
    
    result = st.session_state.advanced_analysis_result
    
    if not result:
        st.warning("No analysis results available. Please run a new analysis.")
        return
    
    project_name = result.get('project_name', 'Mining Project')
    summary = result.get('summary', {})
    valuations = result.get('valuations', {})
    extracted = result.get('extracted_data', {})
    narrative = result.get('narrative', {})
    
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); 
                    padding: 25px; border-radius: 15px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0 0 10px 0;'>📊 {project_name}</h2>
            <p style='color: rgba(255,255,255,0.9); margin: 0;'>
                Advanced Valuation Analysis • {summary.get('commodity', 'Unknown')} • 
                {summary.get('stage', 'Unknown')} Stage
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    render_valuation_summary(summary, extracted)
    
    # Show derivations if any values were calculated from other fields
    derivations = result.get('derivations', [])
    if derivations:
        with st.expander("📐 Data Derivations (values calculated from extracted data)"):
            for d in derivations:
                st.markdown(f"- {d}")
    
    # Show missing inputs report if there are issues
    missing_report = result.get('missing_inputs_report', {})
    if missing_report:
        with st.expander("⚠️ Missing Data for Some Valuations", expanded=True):
            st.markdown("**The following data is needed for complete valuations:**")
            for method, missing_items in missing_report.items():
                st.markdown(f"**{method}:** {', '.join(missing_items)}")
            st.markdown("""
            **Tip:** Upload a document that contains:
            - Annual production rate (oz/year, tonnes/year)
            - Commodity price assumption ($/oz, $/tonne)
            - Operating cost or AISC ($/oz, $/tonne)
            """)
    
    if narrative.get('executive_summary'):
        st.markdown("### 📝 Executive Summary")
        st.markdown(narrative['executive_summary'])
    
    st.markdown("---")
    st.markdown("### 📈 Detailed Valuation Results")
    
    tabs = st.tabs([
        "🎯 Probability DCF",
        "💰 Income DCF",
        "🎲 Monte Carlo",
        "🔬 Kilburn Method",
        "🌳 Decision Tree EMV"
    ])
    
    with tabs[0]:
        render_probability_dcf_results(valuations.get('probability_dcf', {}))
    
    with tabs[1]:
        render_income_dcf_results(valuations.get('income_dcf', {}))
    
    with tabs[2]:
        render_monte_carlo_results(valuations.get('monte_carlo', {}))
    
    with tabs[3]:
        render_kilburn_results(valuations.get('kilburn', {}))
    
    with tabs[4]:
        render_decision_tree_results(valuations.get('decision_tree', {}))
    
    st.markdown("---")
    render_download_section(result, current_user)
    
    st.markdown("---")
    st.markdown("### 💬 Discuss Valuation with Oreplot AI")
    st.markdown("Have questions about the valuation? Need to point out corrections? Chat with Oreplot AI below.")
    
    set_context("advanced_ai_chat", {
        "uploaded_files": result.get('uploaded_files', []),
        "project_name": project_name,
        "extracted_text": str(extracted)[:3000],
        "analysis_result": result
    })
    
    render_chat_interface(
        chat_key="advanced_ai_chat",
        ai_tier="advanced",
        placeholder_text="Ask questions about the valuation or point out corrections...",
        height=250
    )


def render_valuation_summary(summary: Dict, extracted: Dict):
    """Render the valuation summary metrics"""
    
    val_range = summary.get('valuation_range', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Valuation Range",
            f"${val_range.get('low', 0):.0f}M - ${val_range.get('high', 0):.0f}M",
            delta=f"Mid: ${val_range.get('mid', 0):.0f}M"
        )
    
    with col2:
        base_npv = extracted.get('economics', {}).get('npv', 0)
        st.metric(
            "Base Case NPV",
            format_currency(base_npv, decimals=0) if base_npv else "N/A"
        )
    
    with col3:
        base_irr = extracted.get('economics', {}).get('irr', 0)
        st.metric(
            "Base Case IRR",
            f"{base_irr:.1f}%" if base_irr else "N/A"
        )
    
    with col4:
        methods_done = summary.get('methods_completed', 0)
        st.metric(
            "Methods Completed",
            f"{methods_done}/5"
        )
    
    overall_rec = summary.get('overall_recommendation', {})
    color_map = {
        'green': '#059669',
        'blue': '#2563EB',
        'orange': '#D97706',
        'red': '#DC2626',
        'gray': '#6B7280'
    }
    rec_color = color_map.get(overall_rec.get('color', 'gray'), '#6B7280')
    
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, {rec_color}15 0%, {rec_color}25 100%); 
                    padding: 15px; border-radius: 10px; border-left: 4px solid {rec_color}; margin: 15px 0;'>
            <h4 style='color: {rec_color}; margin: 0 0 5px 0;'>📋 Overall Recommendation</h4>
            <p style='color: #1E293B; margin: 0; font-size: 1.1rem;'><strong>{overall_rec.get('text', 'N/A')}</strong></p>
        </div>
    """, unsafe_allow_html=True)


def render_probability_dcf_results(data: Dict):
    """Render Probability-Weighted DCF results"""
    
    if 'error' in data:
        error_msg = data.get('message', data['error'])
        missing = data.get('missing_inputs', [])
        if missing:
            st.warning(f"⚠️ **Insufficient Data for Probability DCF**\n\nMissing: {', '.join(missing)}")
        else:
            st.error(f"Analysis error: {error_msg}")
        return
    
    if not data:
        st.info("Probability DCF analysis not available")
        return
    
    st.markdown("#### Risk-Adjusted Valuation")
    
    base_case = data.get('base_case', {})
    risk_adj = data.get('risk_adjusted_valuation', {})
    prob_analysis = data.get('probability_analysis', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Base Case NPV", format_currency(base_case.get('npv', 0), decimals=1))
    with col2:
        st.metric("Risk-Adjusted NPV", format_currency(risk_adj.get('risk_adjusted_npv', 0), decimals=1))
    with col3:
        st.metric("Success Probability", f"{prob_analysis.get('probability_percent', 0):.1f}%")
    
    st.markdown("##### Stage Probabilities")
    stage_probs = prob_analysis.get('stage_probabilities', {})
    for stage, prob in stage_probs.items():
        st.progress(prob, text=f"{stage.replace('_', ' ').title()}: {prob*100:.0f}%")
    
    rec = data.get('recommendation', {})
    if rec.get('text'):
        st.info(f"**Recommendation:** {rec['text']}")


def render_income_dcf_results(data: Dict):
    """Render Income Approach DCF results"""
    
    if 'error' in data:
        error_msg = data.get('message', data['error'])
        missing = data.get('missing_inputs', [])
        if missing:
            st.warning(f"⚠️ **Insufficient Data for Income DCF**\n\nMissing: {', '.join(missing)}")
        else:
            st.error(f"Analysis error: {error_msg}")
        return
    
    if not data:
        st.info("Income DCF analysis not available")
        return
    
    st.markdown("#### Base Case Economics")
    
    val_summary = data.get('valuation_summary', {})
    proj_econ = data.get('project_economics', {})
    capital = data.get('capital_structure', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("NPV", format_currency(val_summary.get('npv', 0), decimals=1))
    with col2:
        st.metric("IRR", f"{val_summary.get('irr_percent', 0):.1f}%")
    with col3:
        st.metric("Payback", f"{val_summary.get('payback_years', 'N/A')} years")
    with col4:
        st.metric("Mine Life", f"{val_summary.get('mine_life', 0)} years")
    
    st.markdown("##### Project Economics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("AISC", f"${proj_econ.get('aisc', 0):.0f}/{proj_econ.get('production_unit', 'unit')}")
    with col2:
        st.metric("Initial CAPEX", format_currency(capital.get('initial_capex', 0), decimals=0))
    with col3:
        st.metric("Margin", f"{proj_econ.get('margin_percent', 0):.1f}%")
    
    rec = data.get('recommendation', {})
    if rec.get('text'):
        st.info(f"**Recommendation:** {rec['text']}")


def render_monte_carlo_results(data: Dict):
    """Render Monte Carlo simulation results"""
    
    if 'error' in data:
        error_msg = data.get('message', data['error'])
        missing = data.get('missing_inputs', [])
        if missing:
            st.warning(f"⚠️ **Insufficient Data for Monte Carlo**\n\nMissing: {', '.join(missing)}")
        else:
            st.error(f"Analysis error: {error_msg}")
        return
    
    if not data:
        st.info("Monte Carlo analysis not available")
        return
    
    st.markdown("#### NPV Distribution (10,000 Simulations)")
    
    npv_stats = data.get('npv_statistics', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        p10 = npv_stats.get('p10', 0)
        st.metric("P10 (Downside)", format_currency(p10/1e6, decimals=1) if isinstance(p10, (int, float)) else "N/A")
    with col2:
        p50 = npv_stats.get('p50', 0)
        st.metric("P50 (Base)", format_currency(p50/1e6, decimals=1) if isinstance(p50, (int, float)) else "N/A")
    with col3:
        p90 = npv_stats.get('p90', 0)
        st.metric("P90 (Upside)", format_currency(p90/1e6, decimals=1) if isinstance(p90, (int, float)) else "N/A")
    with col4:
        prob_pos = npv_stats.get('prob_positive', 0)
        st.metric("Prob. Positive", f"{prob_pos*100:.0f}%" if isinstance(prob_pos, (int, float)) else "N/A")
    
    var_5 = npv_stats.get('var_5', 0)
    if var_5:
        st.metric("Value at Risk (5%)", format_currency(var_5/1e6, decimals=1))
    
    real_options = data.get('real_options_value', 0)
    if real_options:
        st.metric("Real Options Value", format_currency(real_options/1e6, decimals=1))
    
    rec = data.get('recommendation', {})
    if rec.get('text'):
        st.info(f"**Recommendation:** {rec['text']}")


def render_kilburn_results(data: Dict):
    """Render Kilburn Method / Cost Approach results"""
    
    if 'error' in data:
        error_msg = data.get('message', data['error'])
        missing = data.get('missing_inputs', [])
        if missing:
            st.warning(f"⚠️ **Insufficient Data for Kilburn Method**\n\nMissing: {', '.join(missing)}")
        else:
            st.error(f"Analysis error: {error_msg}")
        return
    
    if not data:
        st.info("Kilburn analysis not available")
        return
    
    st.markdown("#### Exploration Floor Value")
    
    geo_rating = data.get('geoscientific_rating', {})
    val_summary = data.get('valuation_summary', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("PEM Multiplier", f"{val_summary.get('pem', 0):.2f}x")
    with col2:
        st.metric("Avg. Rating", f"{val_summary.get('average_rating', 0):.1f}/4.0")
    with col3:
        val = val_summary.get('recommended_value', 0)
        st.metric("Floor Value", format_currency(val/1e6, decimals=2) if val > 1000000 else f"${val:,.0f}")
    
    st.markdown("##### Geoscientific Rating Breakdown")
    for factor in ['regional_prospectivity', 'project_maturity', 'local_geology', 'analytical_data']:
        score = geo_rating.get(factor, 0)
        if score:
            st.progress(score / 4.0, text=f"{factor.replace('_', ' ').title()}: {score}/4")
    
    rec = data.get('recommendation', {})
    if rec.get('text'):
        st.info(f"**Recommendation:** {rec['text']}")


def render_decision_tree_results(data: Dict):
    """Render Decision Tree / EMV results"""
    
    if 'error' in data:
        error_msg = data.get('message', data['error'])
        missing = data.get('missing_inputs', [])
        if missing:
            st.warning(f"⚠️ **Insufficient Data for Decision Tree EMV**\n\nMissing: {', '.join(missing)}")
        else:
            st.error(f"Analysis error: {error_msg}")
        return
    
    if not data:
        st.info("Decision Tree analysis not available")
        return
    
    st.markdown("#### Expected Monetary Value Analysis")
    
    val_summary = data.get('valuation_summary', {})
    decision = data.get('decision_analysis', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("EMV", format_currency(val_summary.get('emv', 0), decimals=1))
    with col2:
        st.metric("Terminal Value", format_currency(val_summary.get('terminal_value', 0), decimals=1))
    with col3:
        st.metric("Prob. to Production", f"{val_summary.get('probability_to_production', 0):.1f}%")
    with col4:
        st.metric("Time to Production", f"{val_summary.get('total_time_to_production', 0):.1f} yrs")
    
    st.markdown("##### Stage-Gate Breakdown")
    stages = data.get('stage_gate_analysis', [])
    for stage in stages[:5]:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{stage.get('stage_name', 'Stage')}**")
        with col2:
            st.write(f"Cost: ${stage.get('cost', 0):.1f}M")
        with col3:
            st.write(f"Success: {stage.get('success_probability', 0):.0f}%")
    
    options = data.get('real_options_value', {})
    if options and isinstance(options, dict):
        total_options = options.get('total_options_value', 0)
        if total_options:
            st.metric("Real Options Value", format_currency(total_options, decimals=1))
    
    rec = data.get('recommendation', {})
    if rec.get('text'):
        st.info(f"**Recommendation:** {rec['text']}")


def render_download_section(result: Dict, current_user: dict):
    """Render the download report section"""
    
    st.markdown("### 📥 Download Report")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_bytes = generate_advanced_pdf_report(result)
                    
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"{result.get('project_name', 'Project')}_Advanced_Valuation_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("PDF report generated successfully!")
                except Exception as e:
                    st.error(f"Failed to generate PDF: {str(e)}")
    
    with col2:
        if st.button("🔄 New Analysis", use_container_width=True):
            st.session_state.advanced_view_mode = 'new_analysis'
            st.session_state.advanced_analysis_result = None
            st.rerun()
    
    with col3:
        if st.button("💾 Save to Projects", use_container_width=True):
            try:
                from project_manager import ProjectManager
                
                project = ProjectManager.create_project(
                    user_id=current_user['id'],
                    name=result.get('project_name', 'Advanced AI Project'),
                    description=result.get('project_description', ''),
                    location='',
                    commodity=result.get('primary_commodity', '')
                )
                
                summary = result.get('summary', {})
                val_range = summary.get('valuation_range', {})
                
                analysis_data = {
                    'categories': {},
                    'executive_summary': result.get('narrative', {}).get('executive_summary', ''),
                    'extracted_data': result.get('extracted_data', {}),
                    'valuations': result.get('valuations', {}),
                    'valuation_summary': summary
                }
                
                scoring_data = {
                    'total_score': summary.get('methods_completed', 0) * 20,
                    'probability_of_success': 0,
                    'risk_band': 'ADVANCED VALUATION',
                    'risk_category': 'Advanced Valuation',
                    'category_contributions': {}
                }
                
                rec_text = summary.get('overall_recommendation', {}).get('text', 'See detailed valuation results.')
                recommendations = [rec_text] if rec_text else ['See detailed valuation results.']
                
                saved_analysis = ProjectManager.save_analysis(
                    project_id=project['id'],
                    analysis_data=analysis_data,
                    scoring_data=scoring_data,
                    recommendations=recommendations,
                    analysis_type='advanced_ai'
                )
                
                st.success(f"✅ Saved to project: {project['name']}")
            except Exception as e:
                st.error(f"Failed to save: {str(e)}")


def generate_advanced_pdf_report(result: Dict) -> bytes:
    """Generate PDF report for advanced valuation analysis"""
    from fpdf import FPDF
    
    class AdvancedValuationReport(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'Advanced Valuation Report - Oreplot', 0, 1, 'C')
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    pdf = AdvancedValuationReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, 'Analysis Type: Oreplot Advanced Analysis', 0, 1, 'R')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, result.get('project_name', 'Mining Project'), 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
    pdf.ln(10)
    
    summary = result.get('summary', {})
    val_range = summary.get('valuation_range', {})
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Valuation Summary', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Valuation Range: ${val_range.get('low', 0):.1f}M - ${val_range.get('high', 0):.1f}M", 0, 1)
    pdf.cell(0, 8, f"Median Value: ${val_range.get('mid', 0):.1f}M", 0, 1)
    pdf.cell(0, 8, f"Methods Completed: {summary.get('methods_completed', 0)}/5", 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f"Recommendation: {summary.get('overall_recommendation', {}).get('text', 'N/A')}", 0, 1)
    pdf.ln(10)
    
    narrative = result.get('narrative', {})
    if narrative.get('executive_summary'):
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Executive Summary', 0, 1)
        pdf.set_font('Arial', '', 10)
        
        exec_summary = narrative['executive_summary']
        exec_summary = exec_summary.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 6, exec_summary)
        pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Valuation Methods', 0, 1)
    
    valuations = result.get('valuations', {})
    
    methods = [
        ('Probability-Weighted DCF', 'probability_dcf', 'risk_adjusted_valuation', 'risk_adjusted_npv'),
        ('Income DCF', 'income_dcf', 'valuation_summary', 'npv'),
        ('Monte Carlo P50', 'monte_carlo', 'npv_statistics', 'p50'),
        ('Kilburn Method', 'kilburn', 'valuation_summary', 'recommended_value'),
        ('Decision Tree EMV', 'decision_tree', 'valuation_summary', 'emv')
    ]
    
    pdf.set_font('Arial', '', 10)
    for name, key, sub_key, value_key in methods:
        val_data = valuations.get(key, {})
        if 'error' not in val_data:
            sub_data = val_data.get(sub_key, {})
            value = sub_data.get(value_key, 0)
            if value:
                if key == 'monte_carlo' or key == 'kilburn':
                    value = value / 1e6
                pdf.cell(0, 6, f"{name}: ${value:.1f}M", 0, 1)
        else:
            pdf.cell(0, 6, f"{name}: Error in calculation", 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 9)
    pdf.cell(0, 6, "This report was generated by Oreplot Advanced AI Valuation Agent.", 0, 1)
    pdf.cell(0, 6, "For detailed methodology, please refer to full technical documentation.", 0, 1)
    
    output = pdf.output(dest='S')
    if isinstance(output, bytes):
        return output
    elif isinstance(output, bytearray):
        return bytes(output)
    else:
        return output.encode('latin-1')


def render_access_denied(current_user: dict):
    """Render access denied message with upgrade information"""
    st.markdown("""
        <div style='background: linear-gradient(135deg, #FEE2E2 0%, #FECACA 100%); 
                    padding: 2rem; border-radius: 12px; text-align: center; margin: 2rem 0;'>
            <h2 style='color: #DC2626; margin-bottom: 1rem;'>🔒 Advanced AI Access Required</h2>
            <p style='color: #7F1D1D; font-size: 1.1rem;'>
                Your current plan does not include Advanced AI features.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🟣 Advanced AI Features Include:")
    
    feature_cols = st.columns(3)
    for idx, feature in enumerate(ADVANCED_AI_FEATURES):
        with feature_cols[idx % 3]:
            st.markdown(f"""
                <div style='background: #F8FAFC; padding: 1rem; border-radius: 8px; 
                            margin-bottom: 1rem; border-left: 4px solid #8B5CF6;'>
                    <h4 style='margin: 0 0 0.5rem 0;'>{feature['icon']} {feature['name']}</h4>
                    <p style='color: #64748B; margin: 0; font-size: 0.9rem;'>{feature['description']}</p>
                </div>
            """, unsafe_allow_html=True)
    
    st.info("💡 Contact your administrator to upgrade your AI access tier.")
