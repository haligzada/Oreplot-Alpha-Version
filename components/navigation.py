import streamlit as st

def render_top_navigation():
    """Render the top navigation bar with main menu items"""
    
    st.markdown("""
    <style>
        .top-nav {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
        }
        .nav-brand {
            font-size: 1.5rem;
            font-weight: 800;
            color: white;
            text-decoration: none;
        }
        .nav-menu {
            display: flex;
            gap: 2rem;
            list-style: none;
            margin: 0;
            padding: 0;
        }
        .nav-item {
            color: white;
            cursor: pointer;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        .nav-item:hover {
            background: rgba(255,255,255,0.2);
        }
        .nav-item.active {
            background: rgba(255,255,255,0.3);
        }
        .user-menu-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .user-menu-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        /* Responsive navigation - prevent text squeezing */
        .stButton button {
            height: auto !important;
            min-height: 2.5rem !important;
        }
        div[data-testid="column"] button {
            white-space: nowrap !important;
            min-width: fit-content !important;
            padding: 0.5rem 0.4rem !important;
            font-size: 0.85rem !important;
        }
        div[data-testid="column"] button div {
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        div[data-testid="column"] button p {
            white-space: nowrap !important;
            font-size: inherit !important;
            margin: 0 !important;
            line-height: 1.3 !important;
            overflow: visible !important;
        }
        /* When sidebar is open, make navigation more compact */
        [data-testid="stSidebar"][aria-expanded="true"] ~ [data-testid="stMainBlockContainer"] div[data-testid="column"] button {
            font-size: 0.75rem !important;
            padding: 0.5rem 0.3rem !important;
        }
        /* Responsive breakpoints with better handling */
        @media (max-width: 1400px) {
            div[data-testid="column"] button {
                font-size: 0.8rem !important;
                padding: 0.5rem 0.35rem !important;
            }
        }
        @media (max-width: 1200px) {
            div[data-testid="column"] button {
                font-size: 0.75rem !important;
                padding: 0.5rem 0.3rem !important;
            }
        }
        @media (max-width: 1000px) {
            div[data-testid="column"] button {
                font-size: 0.7rem !important;
                padding: 0.4rem 0.25rem !important;
            }
        }
        .logo-container img {
            max-height: 40px;
            width: auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    
    # Create navigation bar with better proportions
    col1, col2, col3, col4, col5, col6, col_spacer = st.columns([1.0, 1.2, 1.0, 1.0, 1.2, 1.2, 1.2])
    
    with col1:
        st.image("attached_assets/plot_1761827661787.png", width=90)
    
    with col2:
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.current_page = 'dashboard'
            st.rerun()
    
    with col3:
        if st.button("📁 Projects", use_container_width=True, key="nav_projects"):
            st.session_state.current_page = 'projects'
            st.rerun()
    
    with col4:
        if st.button("📄 Reports", use_container_width=True, key="nav_reports"):
            st.session_state.current_page = 'reports'
            st.rerun()
    
    with col5:
        if st.button("💰 Financials", use_container_width=True, key="nav_financials"):
            st.session_state.current_page = 'financials'
            st.rerun()
    
    with col6:
        if st.button("🤖 AI Agent", use_container_width=True, key="nav_ai_agent"):
            st.session_state.current_page = 'ai_agent'
            st.rerun()
    
    with col_spacer:
        # User menu button will be rendered separately
        pass
    
    return st.session_state.current_page


def render_user_menu_dropdown(current_user):
    """Render user dropdown menu with profile, settings, etc."""
    
    st.markdown("""
    <style>
        .user-menu-container {
            position: relative;
        }
        .user-info-box {
            background: #F8F9FB;
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #E5E7EB;
            margin-bottom: 1rem;
        }
        .user-email {
            color: #64748B;
            font-size: 0.875rem;
        }
        .menu-section {
            margin-top: 1rem;
        }
        .menu-section-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### 👤 {current_user.get('username', 'User')}")
        st.markdown(f"<div class='user-email'>{current_user.get('email', '')}</div>", unsafe_allow_html=True)
        
        st.markdown("#### User Menu")
        
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.current_page = 'profile'
            st.rerun()
        
        if st.button("⚙️ Account Settings", use_container_width=True):
            st.session_state.current_page = 'account_settings'
            st.rerun()
        
        if st.button("🎨 App Settings", use_container_width=True):
            st.session_state.current_page = 'app_settings'
            st.rerun()
        
        if st.button("📊 Usage", use_container_width=True):
            st.session_state.current_page = 'billing'
            st.rerun()
        
        if st.button("👥 Team / Members", use_container_width=True):
            st.session_state.current_page = 'team'
            st.rerun()
        
        # Admin Panel - show for all admin users
        if current_user.get('is_admin'):
            st.markdown("---")
            st.markdown("#### Administration")
            if st.button("Admin Panel", use_container_width=True, type="secondary"):
                st.session_state.current_page = 'admin_panel'
                st.rerun()
            if st.button("Comparables Admin", use_container_width=True, type="secondary"):
                st.session_state.current_page = 'admin_comparables'
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
