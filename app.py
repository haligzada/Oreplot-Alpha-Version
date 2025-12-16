import streamlit as st
from datetime import datetime
from document_extractor import DocumentExtractor
from ai_analyzer import MiningProjectAnalyzer
from scoring_engine import ScoringEngine
from report_generator import ReportGenerator
from auth import require_auth, render_user_info
from project_manager import ProjectManager
from template_manager import TemplateManager
from comparables_manager import ComparablesManager
from database import SessionLocal
from comparables_scheduler import start_scheduler

# Import page modules
from page_modules.dashboard_page import render_dashboard
from page_modules.projects_page import render_projects_page
from page_modules.reports_page import render_reports_page
from page_modules.comparables_page import render_comparables_page
from page_modules.financials_page import render_financials_page
from page_modules.profile_page import render_profile_page
from page_modules.account_settings_page import render_account_settings_page
from page_modules.app_settings_page import render_app_settings_page
from page_modules.billing_page import render_billing_page
from page_modules.team_page import render_team_page
from page_modules.login_page import render_login_page
from page_modules.admin_panel_page import render_admin_panel_page
from page_modules.advanced_ai_page import render_advanced_ai_page
from components.navigation import render_top_navigation, render_user_menu_dropdown
from components.ai_chat import render_chat_interface, render_compact_chat_input, set_context, clear_chat, init_chat_state
from ai_access_control import has_light_ai_access, has_advanced_ai_access, get_user_ai_features, LIGHT_AI_FEATURES, ADVANCED_AI_FEATURES
st.set_page_config(
    page_title="Oreplot - AI Mining Due Diligence",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

current_user = require_auth()

# Session timeout disabled - users stay logged in via authentication
# Sessions are now persistent until user explicitly logs out

# If not authenticated, show login page
if current_user is None:
    render_login_page()
    st.stop()

# Initialize current_page in session state if not set
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

# Start the comparables update scheduler (runs once on app startup)
if 'scheduler_started' not in st.session_state:
    try:
        start_scheduler()
        st.session_state.scheduler_started = True
    except Exception as e:
        pass  # Silently handle scheduler errors to avoid disrupting the app

# Render top navigation and get current page
current_page = render_top_navigation()

# Render user menu in sidebar
render_user_menu_dropdown(current_user)


st.sidebar.markdown("## 📂 Navigation")

col_a, col_b = st.sidebar.columns(2)
with col_a:
    if st.button("➕ New Analysis", use_container_width=True):
        st.session_state.current_page = 'ai_agent'
        st.session_state.view_mode = 'new_analysis'
        st.session_state.current_project = None
        st.session_state.analysis_result = None
        st.rerun()
with col_b:
    if st.button("⚙️ Templates", use_container_width=True):
        st.session_state.current_page = 'ai_agent'
        st.session_state.view_mode = 'template_manager'
        st.rerun()

col_c, col_d = st.sidebar.columns(2)
with col_c:
    if st.button("🌍 Comparables", use_container_width=True):
        st.session_state.current_page = 'ai_agent'
        st.session_state.view_mode = 'comparables'
        st.rerun()

st.sidebar.markdown("## 📂 Projects")
user_projects = ProjectManager.get_user_projects(current_user['id'])

if user_projects:
    selected_project_id = st.sidebar.selectbox(
        "Select a project to view",
        options=[None] + [p['id'] for p in user_projects],
        format_func=lambda x: "-- Select --" if x is None else next((p['name'] for p in user_projects if p['id'] == x), "Unknown")
    )
    
    if selected_project_id:
        project = next((p for p in user_projects if p['id'] == selected_project_id), None)
        if project:
            st.sidebar.markdown(f"**{project['name']}**")
            st.sidebar.markdown(f"📍 {project['location'] or 'N/A'}")
            st.sidebar.markdown(f"⚒️ {project['commodity'] or 'N/A'}")
            st.sidebar.markdown(f"📊 {project['analysis_count']} analysis(es)")
            
            if st.sidebar.button("View Project", use_container_width=True):
                st.session_state.current_page = 'ai_agent'
                st.session_state.view_mode = 'view_project'
                st.session_state.current_project = project
                st.rerun()
else:
    st.sidebar.info("No projects yet. Create your first analysis!")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background-color: #FFFFFF;
    }
    .stApp {
        background-color: #FFFFFF;
    }
    
    [data-testid="stSidebar"] {
        background-color: #F8F9FB;
        border-right: 1px solid #E5E7EB;
    }
    
    h1 {
        color: #0F172A;
        font-weight: 800;
        letter-spacing: -0.8px;
        font-size: 2.5rem;
    }
    h2, h3 {
        color: #1E293B;
        font-weight: 700;
    }
    h4 {
        color: #334155;
        font-weight: 600;
    }
    
    .chat-message {
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    .user-message {
        border-left: 3px solid #7C3AED;
        background-color: #F5F3FF;
    }
    .agent-message {
        border-left: 3px solid #3B82F6;
        background-color: #EFF6FF;
    }
    
    .score-display {
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        padding: 2.5rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #F0F9FF 0%, #EFF6FF 100%);
        border: 2px solid #BFDBFE;
        margin: 1.5rem 0;
    }
    .category-card {
        background-color: #FFFFFF;
        padding: 1.25rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
        border-left: 4px solid #3B82F6;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        color: #FFFFFF;
        font-weight: 600;
        border-radius: 10px;
        border: none;
        padding: 0.625rem 1.5rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 12px -1px rgba(59, 130, 246, 0.3);
    }
    
    .file-upload-section {
        background-color: #F8F9FB;
        padding: 2rem;
        border-radius: 16px;
        border: 2px dashed #CBD5E1;
    }
    
    .stMarkdown p, .stMarkdown li {
        color: #475569;
        line-height: 1.7;
    }
    
    .stSelectbox label, .stTextInput label, .stTextArea label {
        color: #334155 !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
    }
    
    .oreplot-logo {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.05em;
        margin-bottom: 0.5rem;
    }
    
    .oreplot-subtitle {
        color: #64748B;
        font-size: 1.05rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Page Routing Logic
if current_page == 'dashboard':
    render_dashboard(current_user)

elif current_page == 'projects':
    render_projects_page(current_user)

elif current_page == 'reports':
    render_reports_page(current_user)

elif current_page == 'financials':
    render_financials_page(current_user)

elif current_page == 'profile':
    render_profile_page(current_user)

elif current_page == 'account_settings':
    render_account_settings_page(current_user)

elif current_page == 'app_settings':
    render_app_settings_page(current_user)

elif current_page == 'billing':
    render_billing_page(current_user)

elif current_page == 'team':
    render_team_page(current_user)

elif current_page == 'admin_panel':
    render_admin_panel_page(current_user)

elif current_page == 'admin_comparables':
    from page_modules.admin_comparables_page import render_admin_comparables_page
    render_admin_comparables_page(current_user)

elif current_page == 'ai_agent':
    # AI Agent page - Two-tier AI system (Light AI + Advanced AI)

    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'uploaded_files_data' not in st.session_state:
        st.session_state.uploaded_files_data = []
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'new_analysis'
    if 'ai_tier_mode' not in st.session_state:
        st.session_state.ai_tier_mode = 'light_ai'

    ai_features = get_user_ai_features(current_user)
    light_access = ai_features['light_ai']['enabled']
    advanced_access = ai_features['advanced_ai']['enabled']

    st.markdown('<div class="oreplot-subtitle" style="margin-bottom: 1rem;">AI-Powered Mining Due Diligence Platform</div>', unsafe_allow_html=True)
    
    tier_col1, tier_col2, tier_spacer = st.columns([1.5, 1.5, 3])
    
    with tier_col1:
        light_disabled = not light_access
        light_btn_type = "primary" if st.session_state.ai_tier_mode == 'light_ai' and not light_disabled else "secondary"
        if st.button("🔵 Oreplot Light", use_container_width=True, type=light_btn_type, 
                    disabled=light_disabled, help="Standard analysis, scoring, and reports" if light_access else "Access not available"):
            st.session_state.ai_tier_mode = 'light_ai'
            st.session_state.view_mode = 'new_analysis'
            st.rerun()
    
    with tier_col2:
        advanced_disabled = not advanced_access
        advanced_btn_type = "primary" if st.session_state.ai_tier_mode == 'advanced_ai' and not advanced_disabled else "secondary"
        if st.button("🟣 Oreplot Advanced", use_container_width=True, type=advanced_btn_type,
                    disabled=advanced_disabled, help="PwC valuation, Monte Carlo, market multiples" if advanced_access else "Upgrade required"):
            st.session_state.ai_tier_mode = 'advanced_ai'
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.ai_tier_mode == 'advanced_ai':
        render_advanced_ai_page(current_user)
    else:
        col_btn1, col_btn2, col_btn3, col_spacer = st.columns([1, 1, 1.2, 2])
        with col_btn1:
            if st.button("📝 New Analysis", use_container_width=True, 
                        type="primary" if st.session_state.view_mode == 'new_analysis' else "secondary"):
                st.session_state.view_mode = 'new_analysis'
                st.session_state.current_project = None
                st.session_state.analysis_result = None
                st.rerun()
        with col_btn2:
            if st.button("⚙️ Template Manager", use_container_width=True,
                        type="primary" if st.session_state.view_mode == 'template_manager' else "secondary"):
                st.session_state.view_mode = 'template_manager'
                st.rerun()
        with col_btn3:
            if st.button("🌍 Comparables DB", use_container_width=True,
                        type="primary" if st.session_state.view_mode == 'comparables' else "secondary"):
                st.session_state.view_mode = 'comparables'
                st.rerun()
        
        st.markdown("---")

    if st.session_state.ai_tier_mode == 'light_ai' and st.session_state.view_mode == 'view_project' and st.session_state.current_project:
        project = st.session_state.current_project
        st.markdown(f"### 🏔️ {project['name']}")
    
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"**📍 Location:** {project['location'] or 'N/A'}")
            st.markdown(f"**⚒️ Commodity:** {project['commodity'] or 'N/A'}")
        with col_info2:
            st.markdown(f"**📅 Created:** {project['created_at'].strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**📊 Analyses:** {project['analysis_count']}")
    
        if project.get('description'):
            st.markdown(f"**Description:** {project['description']}")
    
        st.markdown("---")
        st.markdown("### 📋 Analysis History")
    
        analyses = ProjectManager.get_project_analyses(project['id'])
    
        if not analyses:
            st.info("No analyses yet for this project.")
        else:
            for analysis_summary in analyses:
                with st.expander(f"Analysis from {analysis_summary['created_at'].strftime('%Y-%m-%d %H:%M')} - Score: {analysis_summary['total_score']}/100"):
                    st.markdown(f"**Risk Category:** {analysis_summary['risk_category']}")
                    st.markdown(f"**Probability of Success:** {analysis_summary['probability_of_success']*100:.1f}%")
                
                    if st.button(f"View Full Analysis", key=f"view_analysis_{analysis_summary['id']}"):
                        full_analysis = ProjectManager.get_analysis_details(analysis_summary['id'])
                    
                        category_contributions = {}
                        for cat_key, cat_data in full_analysis['categories'].items():
                            category_contributions[cat_key] = {
                                'raw_score': cat_data['score'],
                                'weight': cat_data['weight'],
                                'contribution': cat_data['contribution']
                            }
                    
                        st.session_state.analysis_result = {
                            'analysis': {
                                'categories': full_analysis['categories'],
                                'overall_observations': full_analysis.get('ai_analysis_raw', {}).get('overall_observations', '')
                            },
                            'scoring': {
                                'total_score': full_analysis['total_score'],
                                'risk_category': full_analysis['risk_category'],
                                'risk_band': full_analysis['risk_category'],
                                'probability_of_success': full_analysis['probability_of_success'],
                                'recommendation': f"Historical analysis from {full_analysis['created_at'].strftime('%Y-%m-%d')}",
                                'categories': full_analysis['categories'],
                                'category_contributions': category_contributions
                            },
                            'recommendations': full_analysis['recommendations'],
                            'sustainability_scoring': full_analysis.get('sustainability_scoring'),
                            'sustainability_analysis': full_analysis.get('sustainability_analysis'),
                            'project_id': full_analysis['project_id'],
                            'analysis_id': full_analysis['id']
                        }
                        st.rerun()

    elif st.session_state.ai_tier_mode == 'light_ai' and st.session_state.view_mode == 'new_analysis':
        st.markdown("### 📝 New Project Analysis")
    
        with st.expander("🏔️ Project Information", expanded=True):
            project_name = st.text_input("Project Name *", value=st.session_state.get('project_name', ''), key="project_name_input")

    if st.session_state.ai_tier_mode == 'light_ai' and st.session_state.view_mode == 'new_analysis':
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown('<div class="file-upload-section">', unsafe_allow_html=True)
            st.markdown("#### 📁 Upload Project Documents")
            st.markdown("Accepted formats: PDF, DOCX, XLSX, CSV, TXT, JPEG, PNG")
            st.markdown("💡 **Bulk Upload Support:** Upload entire data rooms with hundreds of documents (up to 5GB total)")
        
            uploaded_files = st.file_uploader(
                "Drag and drop files here",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'jpg', 'jpeg', 'png'],
                label_visibility="collapsed",
                help="Upload individual files or entire folders. Maximum 5GB total, 1GB per file."
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
            if uploaded_files:
                total_size_mb = sum(f.size for f in uploaded_files) / (1024 * 1024)
                st.markdown(f"**{len(uploaded_files)} file(s) uploaded** ({total_size_mb:.1f} MB total)")
                
                if len(uploaded_files) <= 10:
                    for file in uploaded_files:
                        st.markdown(f"- `{file.name}` ({file.size / (1024*1024):.2f} MB)")
                else:
                    with st.expander(f"📋 View all {len(uploaded_files)} files"):
                        for file in uploaded_files:
                            st.markdown(f"- `{file.name}` ({file.size / (1024*1024):.2f} MB)")

        with col2:
            st.markdown("#### 🎯 Quick Actions")
        
            # Template selection
            user_templates = TemplateManager.get_user_templates(current_user['id'])
            default_template = TemplateManager.get_default_template(current_user['id'])
        
            if user_templates:
                template_options = [{'id': None, 'name': 'Standard Weights'}] + user_templates
                default_index = 0
                if default_template:
                    default_index = next((i for i, t in enumerate(template_options) if t.get('id') == default_template['id']), 0)
            
                selected_template_idx = st.selectbox(
                    "Scoring Template",
                    range(len(template_options)),
                    index=default_index,
                    format_func=lambda i: template_options[i]['name'] + (' ⭐' if template_options[i].get('is_default') else ''),
                    key="selected_template"
                )
                selected_template = template_options[selected_template_idx]
            else:
                st.info("Using standard weights. Create custom templates in Template Manager.")
                selected_template = None
        
            can_generate = uploaded_files and st.session_state.get('project_name_input', '').strip()
            if not st.session_state.get('project_name_input', '').strip():
                st.warning("⚠️ Project name required")
        
        init_chat_state("light_ai_chat")
        if uploaded_files:
            set_context("light_ai_chat", {
                "uploaded_files": [f.name for f in uploaded_files],
                "project_name": st.session_state.get('project_name_input', ''),
                "analysis_result": st.session_state.get('analysis_result')
            })
        
        render_compact_chat_input(
            chat_key="light_ai_chat",
            ai_tier="light",
            placeholder_text="Share important details about your project or ask questions..."
        )
    
        if st.button("🚀 Generate Analysis", use_container_width=True, disabled=not can_generate):
            total_files = len(uploaded_files)
            
            st.markdown("### 📊 Processing Progress")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            extracted_docs = []
            failed_files = []
            
            batch_size = 10
            for batch_idx in range(0, total_files, batch_size):
                batch_end = min(batch_idx + batch_size, total_files)
                batch_files = uploaded_files[batch_idx:batch_end]
                
                status_text.markdown(f"🔍 Processing batch {batch_idx // batch_size + 1} of {(total_files + batch_size - 1) // batch_size} ({batch_idx + 1}-{batch_end} of {total_files} files)...")
                
                for idx, file in enumerate(batch_files):
                    try:
                        file_bytes = file.read()
                        result = DocumentExtractor.extract_text(file.name, file_bytes)
                        extracted_docs.append(result)
                        if not result.get('success', False):
                            failed_files.append(file.name)
                        file.seek(0)
                    except Exception as e:
                        failed_files.append(file.name)
                        extracted_docs.append({
                            'file_name': file.name,
                            'success': False,
                            'error': str(e),
                            'text': ''
                        })
                    
                    current_progress = (batch_idx + idx + 1) / total_files
                    progress_bar.progress(current_progress)
            
            progress_bar.progress(1.0)
            status_text.markdown(f"✅ Processed {total_files} files ({len(extracted_docs) - len(failed_files)} successful, {len(failed_files)} failed)")
            
            st.session_state.uploaded_files_data = extracted_docs
            
            drill_databases = [doc for doc in extracted_docs if doc.get('is_drill_database')]
            if drill_databases:
                st.success(f"🔬 Detected {len(drill_databases)} drill database(s) - QAQC analysis performed")
                for db in drill_databases:
                    with st.expander(f"📊 QAQC Report: {db['file_name']}", expanded=True):
                        st.markdown(f"**QAQC Score: {db.get('qaqc_score', 0)}/10**")
                        st.markdown(f"_{db.get('qaqc_rationale', '')}_")
                        st.code(db.get('text', ''), language='text')
            
            if failed_files:
                with st.expander(f"⚠️ {len(failed_files)} file(s) could not be processed", expanded=False):
                    for failed_file in failed_files:
                        st.markdown(f"- `{failed_file}`")
            
            st.session_state.history.append({
                'type': 'user',
                'content': f"Uploaded {len(uploaded_files)} documents for analysis",
                'files': [f.name for f in uploaded_files],
                'failed_files': failed_files,
                'drill_databases': len(drill_databases),
                'timestamp': datetime.now()
            })
        
            with st.spinner("🤖 AI analyzing project data..."):
                analysis = MiningProjectAnalyzer.analyze_documents(extracted_docs)
            
                if analysis.get('error'):
                    st.error(f"❌ {analysis['error']}")
                    if analysis.get('extraction_errors'):
                        st.error(f"Failed files: {', '.join(analysis['extraction_errors'])}")
                    st.session_state.analysis_result = None
                else:
                    # Get weights from selected template or use defaults
                    custom_weights = None
                    template_id = None
                    if selected_template and selected_template.get('id'):
                        custom_weights = TemplateManager.get_weights_dict(selected_template)
                        template_id = selected_template['id']
                
                    scoring = ScoringEngine.calculate_investment_score(
                        analysis.get('categories', {}),
                        custom_weights=custom_weights
                    )
                    recommendations = MiningProjectAnalyzer.generate_recommendations(analysis, scoring['total_score'])
                    
                    with st.spinner("🌱 Analyzing sustainability & ESG performance..."):
                        sustainability_analysis = MiningProjectAnalyzer.analyze_sustainability(extracted_docs)
                        
                        if sustainability_analysis.get('error'):
                            st.warning(f"⚠️ Sustainability analysis partial: {sustainability_analysis['error']}")
                            sustainability_scoring = None
                        else:
                            sustainability_scoring = ScoringEngine.calculate_sustainability_score(
                                sustainability_analysis.get('sustainability_categories', {})
                            )
                    
                    with st.spinner("📝 Generating executive summary and strategic recommendations..."):
                        narrative = MiningProjectAnalyzer.generate_executive_narrative(
                            extracted_docs,
                            analysis,
                            scoring['total_score']
                        )
                
                    project = ProjectManager.create_project(
                        user_id=current_user['id'],
                        name=st.session_state.get('project_name_input', 'Untitled Project'),
                        description=st.session_state.get('project_description_input', ''),
                        location=None,
                        commodity=None
                    )
                
                    saved_analysis = ProjectManager.save_analysis(
                        project_id=project['id'],
                        analysis_data=analysis,
                        scoring_data=scoring,
                        recommendations=recommendations,
                        scoring_template_id=template_id,
                        narrative_data=narrative,
                        sustainability_data=sustainability_analysis if not sustainability_analysis.get('error') else None,
                        sustainability_scoring=sustainability_scoring,
                        analysis_type='light_ai'
                    )
                
                    ProjectManager.save_documents(project['id'], extracted_docs)
                    
                    with st.spinner("🔍 Finding comparable projects for benchmarking..."):
                        from comparables_matcher import ComparablesMatchingService
                        comparables = ComparablesMatchingService.find_top_comparables(
                            analysis_id=saved_analysis['id'],
                            analysis_data=analysis,
                            top_n=3
                        )
                
                    st.session_state.analysis_result = {
                        'analysis': analysis,
                        'scoring': scoring,
                        'recommendations': recommendations,
                        'narrative': narrative,
                        'comparables': comparables,
                        'sustainability_analysis': sustainability_analysis if not sustainability_analysis.get('error') else None,
                        'sustainability_scoring': sustainability_scoring,
                        'project_id': project['id'],
                        'analysis_id': saved_analysis['id']
                    }
                
                    project_name = project['name']
                    st.session_state.history.append({
                        'type': 'agent',
                        'content': f'Analysis complete and saved to project "{project_name}"',
                        'timestamp': datetime.now()
                    })
                
                    st.success(f"✅ Project '{project_name}' created and analysis saved!")
        
            st.rerun()
    
        if st.session_state.analysis_result:
            if st.button("📄 Download PDF Report", use_container_width=True):
                result = st.session_state.analysis_result
                project_name = result['analysis'].get('project_name', 'Mining Project')
            
                pdf_bytes = ReportGenerator.generate_pdf_report(
                    project_name=project_name,
                    analysis=result['analysis'],
                    scoring_result=result['scoring'],
                    uploaded_files=[f.name for f in uploaded_files] if uploaded_files else [],
                    recommendations=result['recommendations'],
                    narrative=result.get('narrative'),
                    comparables=result.get('comparables', []),
                    sustainability_analysis=result.get('sustainability_analysis'),
                    sustainability_scoring=result.get('sustainability_scoring')
                )
            
                st.download_button(
                    label="⬇️ Download Report",
                    data=pdf_bytes,
                    file_name=f"mining_dd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
        if st.button("🔄 Clear Session", use_container_width=True):
            st.session_state.history = []
            st.session_state.uploaded_files_data = []
            st.session_state.analysis_result = None
            st.rerun()

    st.markdown("---")

    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        scoring = result['scoring']
        analysis = result['analysis']
        sustainability_scoring = result.get('sustainability_scoring')
    
        st.markdown("### 📊 Dual Scoring Analysis Results")
        
        col_inv, col_sust = st.columns(2)
        
        with col_inv:
            st.markdown("#### 💰 Investment Score")
            score_color = "#00FF88" if scoring['total_score'] >= 70 else "#FFB800" if scoring['total_score'] >= 50 else "#FF4444"
            
            st.markdown(f"""
            <div class="score-display">
                <div style="color: {score_color};">{scoring['total_score']}/100</div>
                <div style="font-size: 1.2rem; color: #888; margin-top: 0.5rem;">{scoring['risk_band']}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">Probability of Success: {scoring['probability_of_success']*100:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Recommendation:** {scoring['recommendation']}")
        
        with col_sust:
            if sustainability_scoring:
                st.markdown("#### 🌱 Sustainability Score")
                sust_score = sustainability_scoring['sustainability_score']
                sust_color = "#00FF88" if sust_score >= 80 else "#7FD8BE" if sust_score >= 65 else "#FFB800" if sust_score >= 50 else "#FF4444"
                
                st.markdown(f"""
                <div class="score-display">
                    <div style="color: {sust_color};">{sust_score}/100</div>
                    <div style="font-size: 1.2rem; color: #888; margin-top: 0.5rem;">{sustainability_scoring['rating']}</div>
                    <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">{sustainability_scoring['description']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Sustainability analysis not available for this project")
    
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📈 Investment Categories", "🌱 Sustainability Categories"])
        
        with tab1:
            st.markdown("### Investment Category Breakdown")
            
            category_names = {
                "geology_prospectivity": "⛰️ Geology / Prospectivity",
                "resource_potential": "💎 Resource Potential",
                "economics": "💰 Economics",
                "legal_title": "⚖️ Legal & Title",
                "permitting_esg": "🌿 Permitting & ESG",
                "data_quality": "📊 Data Quality"
            }
        
            for cat_key, cat_contrib in scoring['category_contributions'].items():
                cat_name = category_names.get(cat_key, cat_key)
                cat_data = analysis.get('categories', {}).get(cat_key, {})
            
                with st.expander(f"{cat_name} - Score: {cat_contrib['raw_score']}/10 (Contribution: {cat_contrib['contribution']})", expanded=False):
                    st.markdown(f"**Weight:** {cat_contrib['weight']}%")
                
                    if cat_data.get('rationale'):
                        st.markdown(f"**Rationale:** {cat_data['rationale']}")
                
                    if cat_data.get('facts_found'):
                        st.markdown("**✓ Evidence Found:**")
                        for fact in cat_data['facts_found']:
                            st.markdown(f"- {fact}")
                
                    if cat_data.get('missing_info'):
                        st.markdown("**⚠️ Missing Information:**")
                        for missing in cat_data['missing_info']:
                            st.markdown(f"- {missing}")
        
        with tab2:
            if sustainability_scoring:
                st.markdown("### Sustainability Category Breakdown")
                
                sustainability_analysis = result.get('sustainability_analysis', {})
                sust_categories = sustainability_analysis.get('sustainability_categories', {})
                sust_contributions = sustainability_scoring.get('category_contributions', {})
                
                sustainability_names = {
                    "environmental": "🌍 Environmental Performance",
                    "social": "👥 Social Performance",
                    "governance": "⚖️ Governance",
                    "climate": "☀️ Climate & Energy"
                }
                
                for cat_key, cat_contrib in sust_contributions.items():
                    cat_name = sustainability_names.get(cat_key, cat_key)
                    cat_data = sust_categories.get(cat_key, {})
                
                    with st.expander(f"{cat_name} - Score: {cat_contrib['raw_score']}/10 (Contribution: {cat_contrib['contribution']})", expanded=False):
                        st.markdown(f"**Weight:** {cat_contrib['weight']}%")
                    
                        if cat_data.get('rationale'):
                            st.markdown(f"**Rationale:** {cat_data['rationale']}")
                    
                        if cat_data.get('facts_found'):
                            st.markdown("**✓ Evidence Found:**")
                            for fact in cat_data['facts_found']:
                                st.markdown(f"- {fact}")
                    
                        if cat_data.get('missing_info'):
                            st.markdown("**⚠️ Missing Information:**")
                            for missing in cat_data['missing_info']:
                                st.markdown(f"- {missing}")
                
                if sustainability_analysis.get('overall_sustainability_notes'):
                    st.markdown("---")
                    st.markdown("### 📝 Overall Sustainability Assessment")
                    st.markdown(sustainability_analysis['overall_sustainability_notes'])
            else:
                st.info("Sustainability analysis not available for this project. Upload documents with ESG/sustainability information for comprehensive analysis.")
    
        st.markdown("---")
        st.markdown("### 💡 Recommendations")
        for rec in result['recommendations']:
            st.markdown(f"- {rec}")
    
        if analysis.get('overall_observations'):
            st.markdown("---")
            st.markdown("### 📝 Overall Observations")
            st.markdown(analysis['overall_observations'])
        
        # Benchmarking against comparables
        st.markdown("---")
        st.markdown("### 🌍 Global Benchmarking")
        
        commodity = analysis.get('project_commodity', '')
        if commodity:
            db = SessionLocal()
            try:
                comparables = ComparablesManager.get_similar_comparables(db, commodity, limit=10)
                
                if comparables:
                    # Convert scoring result to analysis dict format for comparison
                    current_analysis_data = {
                        'total_score': scoring['total_score'],
                        'geology_score': scoring['category_contributions'].get('geology_prospectivity', {}).get('raw_score', 0),
                        'resource_score': scoring['category_contributions'].get('resource_potential', {}).get('raw_score', 0),
                        'economics_score': scoring['category_contributions'].get('economics', {}).get('raw_score', 0),
                        'legal_score': scoring['category_contributions'].get('legal_title', {}).get('raw_score', 0),
                        'permitting_score': scoring['category_contributions'].get('permitting_esg', {}).get('raw_score', 0),
                        'data_quality_score': scoring['category_contributions'].get('data_quality', {}).get('raw_score', 0),
                    }
                    
                    comparison = ComparablesManager.compare_project_to_benchmarks(current_analysis_data, comparables)
                    
                    if comparison.get('comparison_available'):
                        st.markdown(f"**Compared against {comparison['comparables_count']} similar {commodity} projects**")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Overall Score Percentile",
                                f"{comparison['percentiles']['overall']}%" if comparison['percentiles']['overall'] else "N/A",
                                help="Higher percentile means better performance relative to peers"
                            )
                        
                        with col2:
                            benchmark_avg = comparison['benchmarks']['overall_avg']
                            current_score = scoring['total_score'] / 10  # Convert to 0-10 scale
                            delta = current_score - benchmark_avg
                            st.metric(
                                "vs Industry Average",
                                f"{current_score:.1f}/10",
                                f"{delta:+.1f}",
                                help=f"Industry average: {benchmark_avg:.1f}/10"
                            )
                        
                        with col3:
                            if comparison['percentiles']['overall']:
                                if comparison['percentiles']['overall'] >= 75:
                                    performance = "Top Quartile 🌟"
                                elif comparison['percentiles']['overall'] >= 50:
                                    performance = "Above Average ✓"
                                elif comparison['percentiles']['overall'] >= 25:
                                    performance = "Below Average"
                                else:
                                    performance = "Bottom Quartile"
                                st.metric("Performance", performance)
                        
                        with st.expander("📊 Detailed Benchmarking Analysis", expanded=False):
                            st.markdown("**Category-by-Category Comparison**")
                            
                            categories = [
                                ('geology', '⛰️ Geology'),
                                ('resource', '💎 Resource'),
                                ('economics', '💰 Economics'),
                                ('legal', '⚖️ Legal'),
                                ('permitting', '🌿 Permitting'),
                                ('data_quality', '📊 Data Quality')
                            ]
                            
                            for cat_key, cat_name in categories:
                                percentile = comparison['percentiles'].get(cat_key)
                                current = comparison['current_scores'].get(f'{cat_key}_score')
                                benchmark = comparison['benchmarks'].get(f'{cat_key}_avg')
                                
                                if percentile and current and benchmark:
                                    col_a, col_b, col_c = st.columns([2, 1, 1])
                                    with col_a:
                                        st.markdown(f"**{cat_name}**")
                                    with col_b:
                                        st.markdown(f"{current:.1f}/10 (Avg: {benchmark:.1f})")
                                    with col_c:
                                        st.markdown(f"**{percentile}th percentile**")
                else:
                    st.info(f"No comparable {commodity} projects found in database for benchmarking.")
            finally:
                db.close()
        else:
            st.info("Commodity information not available for benchmarking. Add commodity details to enable comparison.")
        
        st.markdown("---")
        st.markdown("### 💬 Discuss Analysis with Oreplot AI")
        st.markdown("Have questions about the analysis? Need to point out corrections? Chat with Oreplot AI below.")
        
        set_context("light_ai_chat", {
            "uploaded_files": [],
            "project_name": result.get('analysis', {}).get('project_name', 'Mining Project'),
            "extracted_text": result.get('analysis', {}).get('overall_observations', ''),
            "analysis_result": result
        })
        
        render_chat_interface(
            chat_key="light_ai_chat",
            ai_tier="light",
            placeholder_text="Ask questions about the analysis or point out corrections...",
            height=250
        )

    elif st.session_state.ai_tier_mode == 'light_ai' and st.session_state.view_mode == 'template_manager':
        st.markdown("### ⚙️ Scoring Template Manager")
        st.markdown("Create and manage custom scoring templates with different category weights.")
        st.markdown("---")
    
        # Display existing templates
        user_templates = TemplateManager.get_user_templates(current_user['id'])
    
        tab1, tab2 = st.tabs(["📋 My Templates", "➕ Create New Template"])
    
        with tab1:
            if not user_templates:
                st.info("No custom templates yet. Create your first template in the 'Create New Template' tab!")
            else:
                for template in user_templates:
                    with st.expander(f"{'⭐ ' if template['is_default'] else ''}{template['name']}", expanded=False):
                        st.markdown(f"**Description:** {template.get('description', 'No description')}")
                        st.markdown(f"**Created:** {template['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                        st.markdown("**Category Weights:**")
                        weights = template['weights']
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"- ⛰️ Geology: **{weights['geology_prospectivity']}%**")
                            st.markdown(f"- 💎 Resource: **{weights['resource_potential']}%**")
                            st.markdown(f"- 💰 Economics: **{weights['economics']}%**")
                        with col2:
                            st.markdown(f"- ⚖️ Legal: **{weights['legal_title']}%**")
                            st.markdown(f"- 🌿 Permitting: **{weights['permitting_esg']}%**")
                            st.markdown(f"- 📊 Data Quality: **{weights['data_quality']}%**")
                    
                        st.markdown("---")
                    
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if not template['is_default']:
                                if st.button(f"⭐ Set as Default", key=f"default_{template['id']}"):
                                    TemplateManager.update_template(template['id'], is_default=True)
                                    st.success("Template set as default!")
                                    st.rerun()
                        with col_b:
                            if st.button(f"✏️ Edit", key=f"edit_{template['id']}"):
                                st.session_state.editing_template = template
                                st.rerun()
                        with col_c:
                            if st.button(f"🗑️ Delete", key=f"delete_{template['id']}"):
                                result = TemplateManager.delete_template(template['id'])
                                if result['success']:
                                    st.success(result['message'])
                                    st.rerun()
                                else:
                                    st.error(result['message'])
    
        with tab2:
            # Check if we're editing an existing template
            editing = st.session_state.get('editing_template')
        
            if editing:
                st.info(f"Editing template: {editing['name']}")
                template_name = st.text_input("Template Name *", value=editing['name'])
                template_description = st.text_area("Description", value=editing.get('description', ''))
            
                weights = editing['weights']
            else:
                template_name = st.text_input("Template Name *")
                template_description = st.text_area("Description")
                weights = TemplateManager.DEFAULT_WEIGHTS.copy()
        
            st.markdown("**Adjust Category Weights (must sum to 100%)**")
        
            col1, col2 = st.columns(2)
            with col1:
                geology_weight = st.slider("⛰️ Geology & Prospectivity", 0, 100, int(weights.get('geology_prospectivity', 35)), key="geo_weight")
                resource_weight = st.slider("💎 Resource Potential", 0, 100, int(weights.get('resource_potential', 20)), key="res_weight")
                economics_weight = st.slider("💰 Economics", 0, 100, int(weights.get('economics', 15)), key="econ_weight")
            with col2:
                legal_weight = st.slider("⚖️ Legal & Title", 0, 100, int(weights.get('legal_title', 10)), key="legal_weight")
                permitting_weight = st.slider("🌿 Permitting & ESG", 0, 100, int(weights.get('permitting_esg', 10)), key="perm_weight")
                data_quality_weight = st.slider("📊 Data Quality", 0, 100, int(weights.get('data_quality', 10)), key="data_weight")
        
            total_weight = geology_weight + resource_weight + economics_weight + legal_weight + permitting_weight + data_quality_weight
        
            if total_weight != 100:
                st.error(f"⚠️ Weights must sum to 100%. Current sum: {total_weight}%")
            else:
                st.success(f"✓ Weights sum to 100%")
        
            is_default = st.checkbox("Set as default template", value=editing.get('is_default', False) if editing else False)
        
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Save Template", use_container_width=True, disabled=(total_weight != 100 or not template_name)):
                    try:
                        new_weights = {
                            'geology_prospectivity': geology_weight,
                            'resource_potential': resource_weight,
                            'economics': economics_weight,
                            'legal_title': legal_weight,
                            'permitting_esg': permitting_weight,
                            'data_quality': data_quality_weight
                        }
                    
                        if editing:
                            TemplateManager.update_template(
                                editing['id'],
                                name=template_name,
                                description=template_description,
                                weights=new_weights,
                                is_default=is_default
                            )
                            st.success("Template updated successfully!")
                        else:
                            TemplateManager.create_template(
                                user_id=current_user['id'],
                                name=template_name,
                                description=template_description,
                                weights=new_weights,
                                is_default=is_default
                            )
                            st.success("Template created successfully!")
                    
                        if 'editing_template' in st.session_state:
                            del st.session_state.editing_template
                        st.rerun()
                    except ValueError as e:
                        st.error(f"Error: {e}")
        
            with col_cancel:
                if editing and st.button("❌ Cancel", use_container_width=True):
                    del st.session_state.editing_template
                    st.rerun()

    elif st.session_state.ai_tier_mode == 'light_ai' and st.session_state.view_mode == 'comparables':
        from page_modules.comparables_page import render_browse_comparables, render_benchmark_stats, render_about_section
        
        st.markdown("### 🌍 Global Comparables Database")
        st.markdown("Benchmark your mining projects against real-world analogues")
        st.markdown("---")
        
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

    if st.session_state.ai_tier_mode == 'light_ai':
        st.markdown("---")
        st.markdown("### 💬 Session History")

        if not st.session_state.history:
            st.markdown('<div class="chat-message agent-message">', unsafe_allow_html=True)
            st.markdown("👋 **AI Agent**: Welcome! Upload your mining project documents to begin the due diligence analysis.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            for item in st.session_state.history:
                if item['type'] == 'user':
                    st.markdown('<div class="chat-message user-message">', unsafe_allow_html=True)
                    st.markdown(f"**You**: {item['content']}")
                    if item.get('files'):
                        st.markdown("Files: " + ", ".join([f"`{f}`" for f in item['files']]))
                    st.markdown(f"<small>{item['timestamp'].strftime('%H:%M:%S')}</small>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="chat-message agent-message">', unsafe_allow_html=True)
                    st.markdown(f"**AI Agent**: {item['content']}")
                    st.markdown(f"<small>{item['timestamp'].strftime('%H:%M:%S')}</small>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<small>©2025 Copyright Oreplot. All rights reserved.</small>", unsafe_allow_html=True)
