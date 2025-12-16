import streamlit as st
from datetime import datetime, timedelta
from project_manager import ProjectManager

def render_dashboard(current_user):
    """Render the main dashboard with project overview, summaries, and alerts"""
    
    st.title("📊 Dashboard")
    st.markdown("### Overview of Your Mining Projects")
    
    # Get user projects and analyses
    user_projects = ProjectManager.get_user_projects(current_user['id'])
    
    # Calculate statistics
    total_projects = len(user_projects)
    total_analyses = sum(p.get('analysis_count', 0) for p in user_projects)
    
    # Get recent analyses
    recent_analyses = []
    for project in user_projects:
        analyses = ProjectManager.get_project_analyses(project['id'])
        for analysis in analyses:
            recent_analyses.append({
                'project_name': project['name'],
                'analysis_id': analysis['id'],
                'score': analysis['total_score'],
                'risk': analysis['risk_category'],
                'date': analysis['created_at']
            })
    
    recent_analyses.sort(key=lambda x: x['date'], reverse=True)
    recent_analyses = recent_analyses[:5]
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{}</div>
            <div style="font-size: 0.875rem; opacity: 0.9;">Total Projects</div>
        </div>
        """.format(total_projects), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%); padding: 1.5rem; border-radius: 12px; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{}</div>
            <div style="font-size: 0.875rem; opacity: 0.9;">Analyses Run</div>
        </div>
        """.format(total_analyses), unsafe_allow_html=True)
    
    # Calculate average score
    avg_score = sum(a['score'] for a in recent_analyses) / len(recent_analyses) if recent_analyses else 0
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 1.5rem; border-radius: 12px; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{:.1f}</div>
            <div style="font-size: 0.875rem; opacity: 0.9;">Avg Score</div>
        </div>
        """.format(avg_score), unsafe_allow_html=True)
    
    # Count high-risk projects
    high_risk_count = sum(1 for a in recent_analyses if a['score'] < 50)
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); padding: 1.5rem; border-radius: 12px; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{}</div>
            <div style="font-size: 0.875rem; opacity: 0.9;">High Risk</div>
        </div>
        """.format(high_risk_count), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent Analyses Section
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📈 Recent Analyses")
        
        if recent_analyses:
            for analysis in recent_analyses:
                # Determine color based on score
                if analysis['score'] >= 70:
                    color = "#10B981"
                    icon = "✅"
                elif analysis['score'] >= 50:
                    color = "#F59E0B"
                    icon = "⚠️"
                else:
                    color = "#EF4444"
                    icon = "❌"
                
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 600; color: #0F172A;">{icon} {analysis['project_name']}</div>
                            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem;">
                                {analysis['risk']} • Score: {analysis['score']:.1f}/100
                            </div>
                        </div>
                        <div style="font-size: 0.75rem; color: #94A3B8;">
                            {analysis['date'].strftime('%b %d, %Y') if hasattr(analysis['date'], 'strftime') else 'Recent'}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No analyses yet. Create your first project to get started!")
    
    with col_right:
        st.markdown("### 🔔 Alerts & Notifications")
        
        # Generate smart alerts based on data
        alerts = []
        
        # Alert for high-risk projects
        if high_risk_count > 0:
            alerts.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'High Risk Projects',
                'message': f'{high_risk_count} project(s) require attention'
            })
        
        # Alert for usage limit
        usage_percent = (current_user.get('usage_count', 0) / current_user.get('usage_limit', 10)) * 100
        if usage_percent > 80:
            alerts.append({
                'type': 'info',
                'icon': '📊',
                'title': 'Usage Limit',
                'message': f'{usage_percent:.0f}% of monthly limit used'
            })
        
        # Welcome message if new user
        if total_analyses == 0:
            alerts.append({
                'type': 'success',
                'icon': '👋',
                'title': 'Welcome to Oreplot!',
                'message': 'Start your first analysis to unlock AI-powered insights'
            })
        
        if alerts:
            for alert in alerts:
                bg_color = {
                    'warning': '#FEF3C7',
                    'info': '#DBEAFE',
                    'success': '#D1FAE5'
                }.get(alert['type'], '#F3F4F6')
                
                text_color = {
                    'warning': '#92400E',
                    'info': '#1E40AF',
                    'success': '#065F46'
                }.get(alert['type'], '#1F2937')
                
                st.markdown(f"""
                <div style="background: {bg_color}; padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem;">
                    <div style="font-weight: 600; color: {text_color};">{alert['icon']} {alert['title']}</div>
                    <div style="font-size: 0.875rem; color: {text_color}; margin-top: 0.25rem; opacity: 0.9;">
                        {alert['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("All systems normal! No alerts at this time.")
    
    # Quick Actions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### ⚡ Quick Actions")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("➕ New Analysis", use_container_width=True, type="primary"):
            st.session_state.current_page = 'ai_agent'
            st.rerun()
    
    with col_b:
        if st.button("📁 View All Projects", use_container_width=True):
            st.session_state.current_page = 'projects'
            st.rerun()
    
    with col_c:
        if st.button("📄 Generate Reports", use_container_width=True):
            st.session_state.current_page = 'reports'
            st.rerun()
