import streamlit as st
from datetime import datetime
from project_manager import ProjectManager

def render_projects_page(current_user):
    """Render the projects page with list view and management"""
    
    st.title("📁 Projects")
    st.markdown("### Manage Your Mining Assets")
    
    # Get user projects
    user_projects = ProjectManager.get_user_projects(current_user['id'])
    
    # Search and filter bar
    col_search, col_filter, col_sort = st.columns([3, 1, 1])
    
    with col_search:
        search_query = st.text_input("🔍 Search projects", placeholder="Enter project name or commodity...")
    
    with col_filter:
        filter_option = st.selectbox("Filter by", ["All Projects", "High Risk", "Moderate Risk", "Low Risk"])
    
    with col_sort:
        sort_option = st.selectbox("Sort by", ["Recent", "Name A-Z", "Score High-Low"])
    
    # Filter projects based on search
    filtered_projects = user_projects
    if search_query:
        filtered_projects = [
            p for p in user_projects 
            if search_query.lower() in p['name'].lower() or 
            (p.get('commodity') and search_query.lower() in p['commodity'].lower())
        ]
    
    # Sort projects
    if sort_option == "Name A-Z":
        filtered_projects.sort(key=lambda x: x['name'])
    elif sort_option == "Recent":
        filtered_projects.sort(key=lambda x: x.get('updated_at', x.get('created_at')), reverse=True)
    
    st.markdown(f"**{len(filtered_projects)} projects** found")
    st.markdown("---")
    
    # Display projects in grid layout
    if filtered_projects:
        for i in range(0, len(filtered_projects), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(filtered_projects):
                    project = filtered_projects[i + j]
                    
                    with col:
                        # Get latest analysis for this project
                        analyses = ProjectManager.get_project_analyses(project['id'])
                        latest_analysis = analyses[0] if analyses else None
                        
                        # Determine status color
                        if latest_analysis:
                            score = latest_analysis['total_score']
                            if score >= 70:
                                status_color = "#10B981"
                                status_text = "LOW RISK"
                            elif score >= 50:
                                status_color = "#F59E0B"
                                status_text = "MODERATE"
                            else:
                                status_color = "#EF4444"
                                status_text = "HIGH RISK"
                            
                            # Determine analysis type
                            analysis_type = latest_analysis.get('analysis_type', 'light_ai')
                            if analysis_type == 'advanced_ai':
                                ai_type_badge = '<span style="background: #8B5CF6; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; margin-left: 8px;">Oreplot Advanced</span>'
                            else:
                                ai_type_badge = '<span style="background: #3B82F6; color: white; padding: 2px 8px; border-radius: 999px; font-size: 0.7rem; margin-left: 8px;">Oreplot Light</span>'
                        else:
                            status_color = "#94A3B8"
                            status_text = "NO ANALYSIS"
                            ai_type_badge = ""
                        
                        # Safely format project data
                        project_name = str(project.get('name', 'Unnamed')).replace('"', '&quot;').replace("'", '&#39;')
                        description = str(project.get('description') or 'No description').replace('"', '&quot;').replace("'", '&#39;')[:100]
                        location = str(project.get('location') or 'N/A').replace('"', '&quot;').replace("'", '&#39;')
                        commodity = str(project.get('commodity') or 'N/A').replace('"', '&quot;').replace("'", '&#39;')
                        analysis_count = project.get('analysis_count', 0)
                        
                        updated_at = project.get('updated_at', project.get('created_at'))
                        if hasattr(updated_at, 'strftime'):
                            updated_str = updated_at.strftime('%b %d')
                        else:
                            updated_str = 'Recent'
                        
                        card_html = f"""
                        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E5E7EB; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                                <div style="font-weight: 700; font-size: 1.125rem; color: #0F172A;">{project_name}{ai_type_badge}</div>
                                <div style="background: {status_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600;">{status_text}</div>
                            </div>
                            <div style="color: #64748B; font-size: 0.875rem; margin-bottom: 1rem; min-height: 2.5rem;">{description}</div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.875rem;">
                                <div><span style="color: #94A3B8;">📍 Location:</span> {location}</div>
                                <div><span style="color: #94A3B8;">⚒️ Commodity:</span> {commodity}</div>
                                <div><span style="color: #94A3B8;">📊 Analyses:</span> {analysis_count}</div>
                                <div><span style="color: #94A3B8;">📅 Updated:</span> {updated_str}</div>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            if st.button("📊 View", key=f"view_{project['id']}", use_container_width=True):
                                st.session_state.current_project = project
                                st.session_state.view_mode = 'view_project'
                                st.session_state.current_page = 'ai_agent'
                                st.rerun()
                        
                        with col_b:
                            if st.button("➕ Analyze", key=f"analyze_{project['id']}", use_container_width=True):
                                st.session_state.current_page = 'ai_agent'
                                st.session_state.view_mode = 'new_analysis'
                                st.rerun()
                        
                        with col_c:
                            if st.button("🗑️ Delete", key=f"delete_{project['id']}", use_container_width=True, type="secondary"):
                                st.session_state[f'confirm_delete_{project["id"]}'] = True
                                st.rerun()
                        
                        # Confirmation dialog
                        if st.session_state.get(f'confirm_delete_{project["id"]}', False):
                            st.warning(f"⚠️ Are you sure you want to delete '{project['name']}'? This will also delete all associated analyses and documents.")
                            col_yes, col_no = st.columns(2)
                            with col_yes:
                                if st.button("Yes, Delete", key=f"confirm_yes_{project['id']}", type="primary"):
                                    from database import get_db_session
                                    from models import Project
                                    with get_db_session() as db:
                                        proj_to_delete = db.query(Project).filter(Project.id == project['id']).first()
                                        if proj_to_delete:
                                            db.delete(proj_to_delete)
                                            db.commit()
                                    st.session_state[f'confirm_delete_{project["id"]}'] = False
                                    st.success("Project deleted successfully!")
                                    st.rerun()
                            with col_no:
                                if st.button("Cancel", key=f"confirm_no_{project['id']}"):
                                    st.session_state[f'confirm_delete_{project["id"]}'] = False
                                    st.rerun()
    else:
        st.info("No projects found. Create your first project to get started!")
        
        if st.button("➕ Create New Project", type="primary"):
            st.session_state.current_page = 'ai_agent'
            st.session_state.view_mode = 'new_analysis'
            st.rerun()
