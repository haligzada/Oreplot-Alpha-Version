import streamlit as st
from database import get_db_session
from models import User
import secrets

def render_account_settings_page(current_user):
    """Render account settings page for email, password, MFA, API key management"""
    
    st.title("⚙️ Account Settings")
    st.markdown("### Manage Security and Access")
    
    # current_user is already a dictionary with all user data
    # Security Settings
    st.markdown("#### 🔐 Security Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Email Address**")
        st.text_input("Current Email", value=current_user.get('email', ''), disabled=True)
        st.caption("Contact support to change your email address")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("**Password**")
        if st.button("🔑 Change Password", use_container_width=True):
            st.info("Password change functionality coming soon!")
    
    with col2:
        st.markdown("**Multi-Factor Authentication (MFA)**")
        mfa_enabled = st.checkbox("Enable MFA", value=current_user.get('mfa_enabled') or False)
        
        if mfa_enabled != current_user.get('mfa_enabled'):
            with get_db_session() as db:
                user_to_update = db.query(User).filter(User.id == current_user['id']).first()
                user_to_update.mfa_enabled = mfa_enabled
                if mfa_enabled and not user_to_update.mfa_secret:
                    user_to_update.mfa_secret = secrets.token_urlsafe(32)
                db.commit()
            
            st.success(f"✅ MFA {'enabled' if mfa_enabled else 'disabled'} successfully!")
            st.rerun()
        
        if mfa_enabled:
            st.success("✅ MFA is currently enabled")
        else:
            st.warning("⚠️ Enable MFA for enhanced security")
    
    st.markdown("---")
    
    # API Key Management
    st.markdown("#### 🔑 API Key Management")
    st.caption("Use API keys to integrate Oreplot with other applications")
    
    if current_user.get('api_key'):
        col_key, col_actions = st.columns([3, 1])
        
        with col_key:
            st.text_input("Your API Key", value=current_user.get('api_key', ''), type="password", disabled=True)
        
        with col_actions:
            if st.button("🗑️ Revoke", use_container_width=True):
                with get_db_session() as db:
                    user_to_update = db.query(User).filter(User.id == current_user['id']).first()
                    user_to_update.api_key = None
                    db.commit()
                st.success("API key revoked!")
                st.rerun()
    else:
        if st.button("➕ Generate New API Key", type="primary"):
            new_api_key = f"ore_{secrets.token_urlsafe(32)}"
            
            with get_db_session() as db:
                user_to_update = db.query(User).filter(User.id == current_user['id']).first()
                user_to_update.api_key = new_api_key
                db.commit()
            
            st.success(f"✅ New API key generated: `{new_api_key}`")
            st.warning("⚠️ Copy this key now. You won't be able to see it again!")
            st.rerun()
    
    st.markdown("---")
    
    # Session Management
    st.markdown("#### 🔒 Session Management")
    
    col_session1, col_session2 = st.columns(2)
    
    with col_session1:
        st.markdown("**Active Sessions**")
        st.info("1 active session (this device)")
    
    with col_session2:
        if st.button("🚪 Sign Out All Devices", use_container_width=True):
            st.info("Sign out from all devices functionality coming soon!")
    
    st.markdown("---")
    
    # Danger Zone
    st.markdown("#### ⚠️ Danger Zone")
    
    with st.expander("Delete Account"):
        st.warning("⚠️ **Warning:** This action is irreversible. All your projects and data will be permanently deleted.")
        st.text_input("Type 'DELETE' to confirm", key="delete_confirm")
        
        if st.button("🗑️ Permanently Delete Account", type="secondary"):
            if st.session_state.get('delete_confirm') == 'DELETE':
                st.error("Account deletion is not yet implemented. Please contact support.")
            else:
                st.error("Please type 'DELETE' to confirm")
