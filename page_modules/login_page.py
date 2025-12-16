import streamlit as st
import bcrypt
from database import get_db_session
from models import User
from datetime import datetime

def verify_password(password, hashed_password):
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(password.encode(), hashed_password.encode())
    except:
        return False

def render_login_page():
    """Render the login page with email/password authentication"""
    
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 4rem auto;
            padding: 2rem;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-logo {
            max-width: 60px;
            margin: 0 auto 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## Welcome to Oreplot")
        st.markdown("### Mining Due Diligence Platform")
        st.markdown("---")
        
        email = st.text_input("📧 Email Address", placeholder="Enter your email")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col_login, col_space = st.columns([1, 1])
        
        with col_login:
            if st.button("🔐 Sign In", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    with get_db_session() as db:
                        user = db.query(User).filter(User.email == email).first()
                        
                        if user and user.password_hash and verify_password(password, user.password_hash):
                            # Update last login
                            user.last_login = datetime.utcnow()
                            db.commit()
                            
                            # Store user in session state
                            st.session_state.current_user = {
                                'id': user.id,
                                'email': user.email,
                                'username': user.username,
                                'created_at': user.created_at,
                                'last_login': user.last_login,
                                'password_hash': user.password_hash,
                                'is_admin': user.is_admin,
                                'full_name': user.full_name,
                                'company': user.company,
                                'role': user.role,
                                'phone': user.phone,
                                'avatar_url': user.avatar_url,
                                'api_key': user.api_key,
                                'mfa_enabled': user.mfa_enabled,
                                'mfa_secret': user.mfa_secret,
                                'theme': user.theme,
                                'notifications_enabled': user.notifications_enabled,
                                'ai_behavior_settings': user.ai_behavior_settings,
                                'plan_type': user.plan_type,
                                'usage_count': user.usage_count,
                                'usage_limit': user.usage_limit,
                                'billing_status': user.billing_status
                            }
                            st.session_state.user_id = user.id
                            st.session_state.user_email = user.email
                            st.session_state.username = user.username
                            st.session_state.authenticated = True
                            
                            # Session persistence enabled - user stays logged in until manual logout
                            
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password")
        
        st.markdown("---")
        st.markdown("<small>Don't have an account? Contact your administrator.</small>", unsafe_allow_html=True)
        st.markdown("<small>©2025 Copyright Oreplot. All rights reserved.</small>", unsafe_allow_html=True)
