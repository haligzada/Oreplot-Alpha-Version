import streamlit as st
from database import get_db_session
from models import User
import json

def render_app_settings_page(current_user):
    """Render app settings page for AI behavior, notifications, theme configuration"""
    
    st.title("🎨 App Settings")
    st.markdown("### Customize Your Experience")
    
    # current_user is already a dictionary with all user data
    # Appearance Settings
    st.markdown("#### 🎨 Appearance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            options=["light", "dark", "auto"],
            index=["light", "dark", "auto"].index(current_user.get('theme') or "light"),
            format_func=lambda x: {"light": "☀️ Light", "dark": "🌙 Dark", "auto": "🔄 Auto"}.get(x, x)
        )
        
        if theme != current_user.get('theme'):
            with get_db_session() as db:
                user_to_update = db.query(User).filter(User.id == current_user['id']).first()
                user_to_update.theme = theme
                db.commit()
            st.success(f"Theme changed to {theme}")
            st.rerun()
    
    with col2:
        st.info("Theme settings will be applied on next login")
    
    st.markdown("---")
    
    # Notification Settings
    st.markdown("#### 🔔 Notifications")
    
    notifications_enabled = st.checkbox(
        "Enable Notifications",
        value=current_user.get('notifications_enabled') if current_user.get('notifications_enabled') is not None else True
    )
    
    if notifications_enabled != current_user.get('notifications_enabled'):
        with get_db_session() as db:
            user_to_update = db.query(User).filter(User.id == current_user['id']).first()
            user_to_update.notifications_enabled = notifications_enabled
            db.commit()
        st.success(f"Notifications {'enabled' if notifications_enabled else 'disabled'}")
        st.rerun()
    
    if notifications_enabled:
        st.markdown("**Notify me when:**")
        notify_col1, notify_col2 = st.columns(2)
        
        with notify_col1:
            st.checkbox("Analysis is complete", value=True)
            st.checkbox("High-risk project detected", value=True)
        
        with notify_col2:
            st.checkbox("Usage limit reached", value=True)
            st.checkbox("New team member joins", value=False)
    
    st.markdown("---")
    
    # AI Behavior Settings
    st.markdown("#### 🤖 AI Analysis Settings")
    st.caption("Customize how the AI analyzes your mining projects")
    
    # Load current AI settings
    ai_settings = current_user.get('ai_behavior_settings') or {}
    if isinstance(ai_settings, str):
        try:
            ai_settings = json.loads(ai_settings)
        except:
            ai_settings = {}
    
    analysis_depth = st.select_slider(
        "Analysis Depth",
        options=["Quick", "Standard", "Detailed", "Comprehensive"],
        value=ai_settings.get('analysis_depth', 'Standard')
    )
    
    risk_sensitivity = st.slider(
        "Risk Sensitivity",
        min_value=1,
        max_value=10,
        value=ai_settings.get('risk_sensitivity', 5),
        help="Higher values make the AI more conservative in risk assessment"
    )
    
    focus_areas = st.multiselect(
        "Primary Focus Areas",
        options=["Geology", "Resources", "Economics", "Legal", "Environment", "Data Quality"],
        default=ai_settings.get('focus_areas', ["Geology", "Resources", "Economics"])
    )
    
    include_recommendations = st.checkbox(
        "Include Detailed Recommendations",
        value=ai_settings.get('include_recommendations', True)
    )
    
    # Save AI settings button
    if st.button("💾 Save AI Settings", type="primary"):
        new_ai_settings = {
            'analysis_depth': analysis_depth,
            'risk_sensitivity': risk_sensitivity,
            'focus_areas': focus_areas,
            'include_recommendations': include_recommendations
        }
        
        with get_db_session() as db:
            user_to_update = db.query(User).filter(User.id == current_user['id']).first()
            user_to_update.ai_behavior_settings = json.dumps(new_ai_settings)
            db.commit()
        
        st.success("✅ AI settings saved successfully!")
        st.rerun()
    
    st.markdown("---")
    
    # Data & Privacy
    st.markdown("#### 🔒 Data & Privacy")
    
    col_privacy1, col_privacy2 = st.columns(2)
    
    with col_privacy1:
        st.checkbox("Allow analytics for product improvement", value=True)
        st.checkbox("Share anonymous usage data", value=False)
    
    with col_privacy2:
        if st.button("📥 Export My Data", use_container_width=True):
            st.info("Data export functionality coming soon!")
        
        if st.button("🗑️ Clear Analysis History", use_container_width=True):
            st.warning("This will delete all your analysis history. This action cannot be undone!")
