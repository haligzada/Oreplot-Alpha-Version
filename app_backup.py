import streamlit as st
from datetime import datetime
from document_extractor import DocumentExtractor
from ai_analyzer import MiningProjectAnalyzer
from scoring_engine import ScoringEngine
from report_generator import ReportGenerator
from auth import require_auth, render_user_info
from project_manager import ProjectManager
from template_manager import TemplateManager

st.set_page_config(
    page_title="Oreplot - AI Mining Due Diligence",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

current_user = require_auth()
render_user_info()

st.sidebar.markdown("## 📂 Navigation")

col_a, col_b = st.sidebar.columns(2)
with col_a:
    if st.button("➕ New Analysis", use_container_width=True):
        st.session_state.view_mode = 'new_analysis'
        st.session_state.current_project = None
        st.session_state.analysis_result = None
        st.rerun()
with col_b:
    if st.button("⚙️ Templates", use_container_width=True):
        st.session_state.view_mode = 'template_manager'
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

col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("attached_assets/plot_1761767561805.png", width=200)
with col_title:
    st.markdown('<div class="oreplot-subtitle" style="margin-top: 2rem;">AI-Powered Mining Due Diligence Platform</div>', unsafe_allow_html=True)
st.markdown("---")

if st.session_state.view_mode == 'view_project' and st.session_state.current_project:
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
                        'project_id': full_analysis['project_id'],
                        'analysis_id': full_analysis['id']
                    }
                    st.rerun()

elif st.session_state.view_mode == 'new_analysis':
    st.markdown("### 📝 New Project Analysis")
    
    with st.expander("🏔️ Project Information", expanded=True):
        project_name = st.text_input("Project Name *", value=st.session_state.get('project_name', ''), key="project_name_input")
        project_description = st.text_area("Description", value=st.session_state.get('project_description', ''), placeholder="To make proper analysis, please provide as much detail about the project as possible.", key="project_description_input")

if st.session_state.view_mode == 'new_analysis':
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="file-upload-section">', unsafe_allow_html=True)
        st.markdown("#### 📁 Upload Project Documents")
        st.markdown("Accepted formats: PDF, DOCX, XLSX, CSV, TXT, JPEG, PNG")
        
        uploaded_files = st.file_uploader(
            "Drag and drop files here",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'csv', 'txt', 'jpg', 'jpeg', 'png'],
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) uploaded:**")
            for file in uploaded_files:
                st.markdown(f"- `{file.name}` ({file.size / 1024:.1f} KB)")

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
    
    if st.button("🚀 Generate Analysis", use_container_width=True, disabled=not can_generate):
        with st.spinner("🔍 Processing documents..."):
            extracted_docs = []
            failed_files = []
            for file in uploaded_files:
                file_bytes = file.read()
                result = DocumentExtractor.extract_text(file.name, file_bytes)
                extracted_docs.append(result)
                if not result.get('success', False):
                    failed_files.append(file.name)
                file.seek(0)
            
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
                st.warning(f"⚠️ Could not extract text from {len(failed_files)} file(s): {', '.join(failed_files)}")
            
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
                    scoring_template_id=template_id
                )
                
                ProjectManager.save_documents(project['id'], extracted_docs)
                
                st.session_state.analysis_result = {
                    'analysis': analysis,
                    'scoring': scoring,
                    'recommendations': recommendations,
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
                recommendations=result['recommendations']
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
    
    st.markdown("### 📊 Investment Analysis Results")
    
    score_color = "#00FF88" if scoring['total_score'] >= 70 else "#FFB800" if scoring['total_score'] >= 50 else "#FF4444"
    
    st.markdown(f"""
    <div class="score-display">
        <div style="color: {score_color};">{scoring['total_score']}/100</div>
        <div style="font-size: 1.2rem; color: #888; margin-top: 0.5rem;">{scoring['risk_band']}</div>
        <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">Probability of Success: {scoring['probability_of_success']*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"**Recommendation:** {scoring['recommendation']}")
    
    st.markdown("---")
    st.markdown("### 📈 Category Breakdown")
    
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
    
    st.markdown("---")
    st.markdown("### 💡 Recommendations")
    for rec in result['recommendations']:
        st.markdown(f"- {rec}")
    
    if analysis.get('overall_observations'):
        st.markdown("---")
        st.markdown("### 📝 Overall Observations")
        st.markdown(analysis['overall_observations'])

elif st.session_state.view_mode == 'template_manager':
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
st.markdown("<small>Powered by Replit AI Integrations • GPT-5 Analysis Engine</small>", unsafe_allow_html=True)
