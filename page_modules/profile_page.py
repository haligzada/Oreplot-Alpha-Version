import streamlit as st
from database import get_db_session
from models import User

def render_profile_page(current_user):
    """Render user profile page for viewing/editing profile information"""
    
    st.title("👤 Profile")
    st.markdown("### Manage Your Personal Information")
    
    # current_user is already a dictionary with all user data
    # Profile editing form
    st.markdown("#### Basic Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name", value=current_user.get('full_name') or "", placeholder="John Doe")
        email = st.text_input("Email Address", value=current_user.get('email') or "", placeholder="user@example.com")
        st.caption("You can change your email address")
    
    with col2:
        company = st.text_input("Company", value=current_user.get('company') or "", placeholder="Mining Corp Inc.")
        role = st.text_input("Role / Position", value=current_user.get('role') or "", placeholder="Senior Geologist")
    
    phone = st.text_input("Phone Number", value=current_user.get('phone') or "", placeholder="+1 (555) 123-4567")
    
    st.markdown("---")
    
    # Save button
    col_save, col_cancel = st.columns([1, 4])
    
    with col_save:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            with get_db_session() as db:
                # Check if email is being changed and if new email already exists
                email_changed = email != current_user.get('email')
                if email_changed:
                    existing_user = db.query(User).filter(User.email == email, User.id != current_user['id']).first()
                    if existing_user:
                        st.error("❌ This email address is already in use by another account.")
                        st.stop()
                
                user_to_update = db.query(User).filter(User.id == current_user['id']).first()
                user_to_update.full_name = full_name
                user_to_update.email = email
                user_to_update.company = company
                user_to_update.role = role
                user_to_update.phone = phone
                db.commit()
                
                # Update session state with all fields
                st.session_state.current_user = {
                    'id': user_to_update.id,
                    'email': user_to_update.email,
                    'username': user_to_update.username,
                    'created_at': user_to_update.created_at,
                    'last_login': user_to_update.last_login,
                    'password_hash': user_to_update.password_hash,
                    'full_name': user_to_update.full_name,
                    'company': user_to_update.company,
                    'role': user_to_update.role,
                    'phone': user_to_update.phone,
                    'avatar_url': user_to_update.avatar_url,
                    'api_key': user_to_update.api_key,
                    'mfa_enabled': user_to_update.mfa_enabled,
                    'mfa_secret': user_to_update.mfa_secret,
                    'theme': user_to_update.theme,
                    'notifications_enabled': user_to_update.notifications_enabled,
                    'ai_behavior_settings': user_to_update.ai_behavior_settings,
                    'plan_type': user_to_update.plan_type,
                    'usage_count': user_to_update.usage_count,
                    'usage_limit': user_to_update.usage_limit,
                    'billing_status': user_to_update.billing_status
                }
                st.session_state.user_email = email
            
            st.success("✅ Profile updated successfully!")
            st.rerun()
    
    # Account Information
    st.markdown("---")
    st.markdown("#### Account Information")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.markdown(f"""
        <div style="background: #F8F9FB; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <div style="font-size: 0.875rem; color: #64748B; margin-bottom: 0.25rem;">Username</div>
            <div style="font-weight: 600; color: #0F172A;">{current_user.get('username', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        created_at = current_user.get('created_at')
        created_at_str = created_at.strftime('%B %d, %Y') if hasattr(created_at, 'strftime') else 'Recently'
        st.markdown(f"""
        <div style="background: #F8F9FB; padding: 1rem; border-radius: 8px;">
            <div style="font-size: 0.875rem; color: #64748B; margin-bottom: 0.25rem;">Member Since</div>
            <div style="font-weight: 600; color: #0F172A;">{created_at_str}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with info_col2:
        plan_type = current_user.get('plan_type', 'free')
        st.markdown(f"""
        <div style="background: #F8F9FB; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            <div style="font-size: 0.875rem; color: #64748B; margin-bottom: 0.25rem;">Account Type</div>
            <div style="font-weight: 600; color: #0F172A;">{plan_type.upper()}</div>
        </div>
        """, unsafe_allow_html=True)
        
        last_login = current_user.get('last_login')
        last_login_str = last_login.strftime('%B %d, %Y %H:%M') if last_login and hasattr(last_login, 'strftime') else 'N/A'
        st.markdown(f"""
        <div style="background: #F8F9FB; padding: 1rem; border-radius: 8px;">
            <div style="font-size: 0.875rem; color: #64748B; margin-bottom: 0.25rem;">Last Login</div>
            <div style="font-weight: 600; color: #0F172A;">{last_login_str}</div>
        </div>
        """, unsafe_allow_html=True)
