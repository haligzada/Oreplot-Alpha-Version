import streamlit as st
import streamlit.components.v1 as components
from models import User
from database import get_db_session
from datetime import datetime

def get_replit_auth_user():
    """
    Get authenticated user information from Replit Auth headers or environment.
    Returns user info dict if authenticated, None otherwise.
    """
    import os
    
    try:
        user_id = st.context.headers.get('X-Replit-User-Id')
        username = st.context.headers.get('X-Replit-User-Name')
        email = st.context.headers.get('X-Replit-User-Email')
    except:
        user_id = None
        username = None
        email = None
    
    if not user_id or not username:
        user_id = os.environ.get('REPL_OWNER_ID', 'dev_user_1')
        username = os.environ.get('REPL_OWNER', 'dev_user')
        email = f"{username}@mining-dd.local"
    
    if user_id and username:
        return {
            'id': user_id,
            'username': username,
            'email': email or f"{username}@replit.user"
        }
    
    return None

def get_or_create_user(auth_info):
    """
    Get existing user or create new user in database based on Replit Auth info.
    Returns a dict representation of the user.
    """
    from sqlalchemy import or_
    from sqlalchemy.exc import OperationalError
    import time
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with get_db_session() as session:
                user = session.query(User).filter(
                    or_(User.email == auth_info['email'], User.username == auth_info['username'])
                ).first()
                
                if not user:
                    user = User(
                        email=auth_info['email'],
                        username=auth_info['username'],
                        created_at=datetime.utcnow(),
                        last_login=datetime.utcnow()
                    )
                    session.add(user)
                    session.flush()
                else:
                    user.last_login = datetime.utcnow()
                    session.flush()
                
                # Return full user data as dictionary
                return {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'created_at': user.created_at,
                    'last_login': user.last_login,
                    'password_hash': user.password_hash,
                    'is_admin': user.is_admin or False,
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
        except OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                raise

def render_login_button():
    """
    Render the Replit Auth login button as a Streamlit component.
    """
    components.html("""
        <div style="text-align: center; padding: 2rem;">
            <h2>🔐 Please Log In</h2>
            <p>This application requires authentication to access.</p>
            <script authed="location.reload()" src="https://auth.util.repl.co/script.js"></script>
        </div>
    """, height=200)

def require_auth():
    """
    Require authentication for the app. Returns authenticated user or shows login screen.
    """
    # Check if user is already authenticated in session
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        return st.session_state.current_user
    
    # Otherwise, they need to go through login page
    # This will be handled by app.py showing the login page
    return None

def render_user_info():
    """
    Render user information in the sidebar.
    """
    if 'username' in st.session_state:
        st.sidebar.markdown(f"👤 **{st.session_state.username}**")
        st.sidebar.markdown(f"📧 {st.session_state.user_email}")
        st.sidebar.markdown("---")
