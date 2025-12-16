import streamlit as st
from datetime import datetime
from project_manager import ProjectManager
from report_generator import ReportGenerator

def render_reports_page(current_user):
    """Render the reports page with auto-generated reports and exports"""
    
    st.title("📄 Reports")
    st.markdown("### Download and Export Due Diligence Reports")
    
    # Get all user projects and analyses
    user_projects = ProjectManager.get_user_projects(current_user['id'])
    
    # Collect all analyses across projects
    all_reports = []
    for project in user_projects:
        analyses = ProjectManager.get_project_analyses(project['id'])
        for analysis in analyses:
            all_reports.append({
                'project': project,
                'analysis': analysis
            })
    
    # Sort by date
    all_reports.sort(key=lambda x: x['analysis']['created_at'], reverse=True)
    
    # Summary statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Reports", len(all_reports))
    
    with col2:
        this_month = sum(1 for r in all_reports if (datetime.now() - r['analysis']['created_at']).days < 30)
        st.metric("This Month", this_month)
    
    with col3:
        avg_score = sum(r['analysis']['total_score'] for r in all_reports) / len(all_reports) if all_reports else 0
        st.metric("Avg Score", f"{avg_score:.1f}")
    
    st.markdown("---")
    
    # Filter options
    col_filter, col_export = st.columns([3, 1])
    
    with col_filter:
        filter_option = st.selectbox(
            "Filter reports by risk category",
            ["All Reports", "Low Risk", "Moderate Risk", "High Risk"]
        )
    
    with col_export:
        if st.button("📦 Batch Export", use_container_width=True):
            st.info("Batch export feature coming soon!")
    
    # Filter reports
    filtered_reports = all_reports
    if filter_option == "Low Risk":
        filtered_reports = [r for r in all_reports if r['analysis']['total_score'] >= 70]
    elif filter_option == "Moderate Risk":
        filtered_reports = [r for r in all_reports if 50 <= r['analysis']['total_score'] < 70]
    elif filter_option == "High Risk":
        filtered_reports = [r for r in all_reports if r['analysis']['total_score'] < 50]
    
    st.markdown(f"**{len(filtered_reports)} reports** available")
    st.markdown("---")
    
    # Display reports
    if filtered_reports:
        for report in filtered_reports:
            project = report['project']
            analysis = report['analysis']
            
            # Determine status color
            score = analysis['total_score']
            if score >= 70:
                status_color = "#10B981"
                risk_badge = "LOW RISK"
            elif score >= 50:
                status_color = "#F59E0B"
                risk_badge = "MODERATE"
            else:
                status_color = "#EF4444"
                risk_badge = "HIGH RISK"
            
            # Determine analysis type badge
            analysis_type = analysis.get('analysis_type', 'light_ai')
            if analysis_type == 'advanced_ai':
                ai_badge = "🟣 Oreplot Advanced"
                ai_badge_color = "#8B5CF6"
            else:
                ai_badge = "🔵 Oreplot Light"
                ai_badge_color = "#3B82F6"
            
            col_info, col_actions = st.columns([3, 1])
            
            with col_info:
                # Create expandable section for detailed view
                with st.expander(f"📋 {project['name']} ({ai_badge}) - {risk_badge} (Score: {score:.1f}/100)", expanded=False):
                    st.markdown(f"""
                    <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {status_color};">
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; font-size: 0.875rem; color: #64748B; margin-bottom: 1rem;">
                            <div><strong>Score:</strong> {score:.1f}/100</div>
                            <div><strong>Success Rate:</strong> {analysis['probability_of_success']*100:.1f}%</div>
                            <div><strong>Analysis ID:</strong> #{analysis['id']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display detailed category findings
                    st.markdown("### 📊 Category Analysis")
                    
                    # Get the structured category data from ai_analysis_raw
                    ai_raw_data = analysis.get('ai_analysis_raw', {})
                    categories_data = ai_raw_data.get('categories', {})
                    
                    category_info = [
                        ('geology_prospectivity', '🌍 Geology/Prospectivity', analysis.get('geology_score', 0), analysis.get('geology_weight', 0)),
                        ('resource_potential', '💎 Resource Potential', analysis.get('resource_score', 0), analysis.get('resource_weight', 0)),
                        ('economics', '💰 Economics', analysis.get('economics_score', 0), analysis.get('economics_weight', 0)),
                        ('legal_title', '⚖️ Legal/Title', analysis.get('legal_score', 0), analysis.get('legal_weight', 0)),
                        ('permitting_esg', '🌱 Permitting/ESG', analysis.get('permitting_score', 0), analysis.get('permitting_weight', 0)),
                        ('data_quality', '📈 Data Quality', analysis.get('data_quality_score', 0), analysis.get('data_quality_weight', 0))
                    ]
                    
                    for cat_key, cat_name, score, weight in category_info:
                        with st.container():
                            st.markdown(f"**{cat_name}** (Score: {score:.1f}/10, Weight: {weight*100:.0f}%)")
                            
                            cat_data = categories_data.get(cat_key, {})
                            
                            # Display rationale
                            if cat_data.get('rationale'):
                                st.markdown(f"**Rationale:** {cat_data['rationale']}")
                            
                            # Display facts found
                            if cat_data.get('facts_found'):
                                st.markdown("**✓ Evidence Found:**")
                                for fact in cat_data['facts_found']:
                                    st.markdown(f"- {fact}")
                            
                            # Display missing information
                            if cat_data.get('missing_info'):
                                st.markdown("**⚠️ Missing Information:**")
                                for missing in cat_data['missing_info']:
                                    st.markdown(f"- {missing}")
                            
                            # Fallback to formatted findings if structured data not available
                            if not cat_data and analysis.get(f'{cat_key.split("_")[0]}_findings'):
                                st.markdown(analysis.get(f'{cat_key.split("_")[0]}_findings', 'No findings available'))
                            elif not cat_data:
                                st.markdown('No findings available')
                            
                            st.markdown("---")
                    
                    # Recommendations
                    if analysis.get('recommendations'):
                        st.markdown("### 💡 Recommendations")
                        recommendations = analysis.get('recommendations')
                        if isinstance(recommendations, list):
                            for rec in recommendations:
                                st.markdown(f"• {rec}")
                        else:
                            st.markdown(str(recommendations))
            
            with col_actions:
                # Get the full analysis data from ai_analysis_raw for PDF generation
                ai_raw_data = analysis.get('ai_analysis_raw', {})
                analysis_data = {
                    'project_name': project['name'],
                    'categories': ai_raw_data.get('categories', {}),
                    'overall_observations': ai_raw_data.get('overall_observations', '')
                }
                
                scoring_result = {
                    'total_score': analysis['total_score'],
                    'risk_band': analysis['risk_category'],
                    'probability_of_success': analysis['probability_of_success'],
                    'category_contributions': {
                        'geology_prospectivity': {
                            'raw_score': analysis.get('geology_score', 0),
                            'weight': analysis.get('geology_weight', 0),
                            'contribution': analysis.get('geology_contribution', 0)
                        },
                        'resource_potential': {
                            'raw_score': analysis.get('resource_score', 0),
                            'weight': analysis.get('resource_weight', 0),
                            'contribution': analysis.get('resource_contribution', 0)
                        },
                        'economics': {
                            'raw_score': analysis.get('economics_score', 0),
                            'weight': analysis.get('economics_weight', 0),
                            'contribution': analysis.get('economics_contribution', 0)
                        },
                        'legal_title': {
                            'raw_score': analysis.get('legal_score', 0),
                            'weight': analysis.get('legal_weight', 0),
                            'contribution': analysis.get('legal_contribution', 0)
                        },
                        'permitting_esg': {
                            'raw_score': analysis.get('permitting_score', 0),
                            'weight': analysis.get('permitting_weight', 0),
                            'contribution': analysis.get('permitting_contribution', 0)
                        },
                        'data_quality': {
                            'raw_score': analysis.get('data_quality_score', 0),
                            'weight': analysis.get('data_quality_weight', 0),
                            'contribution': analysis.get('data_quality_contribution', 0)
                        }
                    }
                }
                
                docs = ProjectManager.get_project_documents(project['id'])
                uploaded_files = [doc['file_name'] for doc in docs]
                recommendations = analysis.get('recommendations', [])
                
                # Extract sustainability data if available
                sustainability_scoring = None
                sustainability_analysis = None
                
                if analysis.get('sustainability_score') is not None:
                    # Determine rating based on sustainability score
                    sust_score = analysis['sustainability_score']
                    if sust_score >= 80:
                        rating = "EXCELLENT"
                        description = "Industry-leading sustainability practices - ESG excellence"
                    elif sust_score >= 65:
                        rating = "GOOD"
                        description = "Strong sustainability performance - above industry standards"
                    elif sust_score >= 50:
                        rating = "MODERATE"
                        description = "Acceptable sustainability performance - meets basic standards"
                    else:
                        rating = "NEEDS IMPROVEMENT"
                        description = "Sustainability concerns - requires significant improvements"
                    
                    sustainability_scoring = {
                        'sustainability_score': sust_score,
                        'rating': rating,
                        'description': description,
                        'category_contributions': {
                            'environmental': {
                                'raw_score': analysis.get('environmental_score', 0),
                                'weight': analysis.get('environmental_weight', 0),
                                'contribution': analysis.get('environmental_contribution', 0)
                            },
                            'social': {
                                'raw_score': analysis.get('social_score', 0),
                                'weight': analysis.get('social_weight', 0),
                                'contribution': analysis.get('social_contribution', 0)
                            },
                            'governance': {
                                'raw_score': analysis.get('governance_score', 0),
                                'weight': analysis.get('governance_weight', 0),
                                'contribution': analysis.get('governance_contribution', 0)
                            },
                            'climate': {
                                'raw_score': analysis.get('climate_score', 0),
                                'weight': analysis.get('climate_weight', 0),
                                'contribution': analysis.get('climate_contribution', 0)
                            }
                        }
                    }
                    
                    # Extract sustainability analysis from ai_analysis_raw
                    sustainability_raw = ai_raw_data.get('sustainability_categories', {})
                    if sustainability_raw:
                        sustainability_analysis = {
                            'sustainability_categories': sustainability_raw,
                            'overall_sustainability_notes': ai_raw_data.get('overall_sustainability_notes', '')
                        }
                
                pdf_bytes = ReportGenerator.generate_pdf_report(
                    project['name'],
                    analysis_data,
                    scoring_result,
                    uploaded_files,
                    recommendations,
                    sustainability_analysis=sustainability_analysis,
                    sustainability_scoring=sustainability_scoring,
                    analysis_type=analysis_type
                )
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=f"{project['name']}_Report_{analysis['id']}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"download_{analysis['id']}"
                )
            
            st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.info("No reports available. Run an analysis to generate reports!")
        
        if st.button("➕ Create New Analysis", type="primary"):
            st.session_state.current_page = 'ai_agent'
            st.session_state.view_mode = 'new_analysis'
            st.rerun()
