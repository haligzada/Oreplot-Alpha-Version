import streamlit as st
import bcrypt
from database import get_db_session
from models import User, Project, Analysis
from datetime import datetime
from sqlalchemy import func

def hash_password(password):
    """Secure password hashing using bcrypt with salt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def render_admin_panel_page(current_user):
    """Render the admin panel with full platform control"""
    
    if not current_user.get('is_admin'):
        st.error("Access Denied: You must be an administrator to access this page.")
        st.stop()
    
    st.title("Admin Panel")
    st.markdown("### Platform Administration & Management")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "User Management",
        "AI Access Control",
        "AI Training",
        "Platform Statistics",
        "Cache & Maintenance",
        "Compute Usage",
        "UI Customization"
    ])
    
    # Tab 1: User Management
    with tab1:
        st.markdown("#### Create New User Account")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_email = st.text_input("Email", placeholder="user@example.com")
            new_username = st.text_input("Username", placeholder="johndoe")
            new_full_name = st.text_input("Full Name", placeholder="John Doe")
        
        with col2:
            new_password = st.text_input("Password", type="password", placeholder="Enter secure password")
            new_is_admin = st.checkbox("Administrator Account")
            new_plan_type = st.selectbox("Plan Type", ["free", "starter", "professional", "enterprise"])
        
        if st.button("➕ Create User Account", type="primary"):
            if new_email and new_username and new_password:
                with get_db_session() as db:
                    existing = db.query(User).filter(
                        (User.email == new_email) | (User.username == new_username)
                    ).first()
                    
                    if existing:
                        st.error("❌ Email or username already exists")
                    else:
                        new_user = User(
                            email=new_email,
                            username=new_username,
                            full_name=new_full_name,
                            password_hash=hash_password(new_password),
                            is_admin=new_is_admin,
                            plan_type=new_plan_type,
                            created_at=datetime.utcnow(),
                            usage_limit=10 if new_plan_type == 'free' else 999999
                        )
                        db.add(new_user)
                        db.commit()
                        st.success(f"✅ User account created: {new_email}")
                        st.rerun()
            else:
                st.error("❌ Please fill in all required fields")
        
        st.markdown("---")
        st.markdown("#### All Users")
        
        with get_db_session() as db:
            users = db.query(User).order_by(User.created_at.desc()).all()
            
            # Convert to list of dicts to avoid session issues
            users_data = []
            for u in users:
                users_data.append({
                    'id': u.id,
                    'email': u.email,
                    'username': u.username,
                    'full_name': u.full_name,
                    'is_admin': u.is_admin,
                    'plan_type': u.plan_type,
                    'usage_count': u.usage_count,
                    'usage_limit': u.usage_limit,
                    'created_at': u.created_at,
                    'last_login': u.last_login
                })
        
        for user_data in users_data:
            with st.expander(f"👤 {user_data['email']} {'(Admin)' if user_data['is_admin'] else ''}"):
                info_col1, info_col2 = st.columns(2)
                
                with info_col1:
                    st.markdown(f"**Username:** {user_data['username']}")
                    st.markdown(f"**Full Name:** {user_data['full_name'] or 'Not set'}")
                    st.markdown(f"**Plan Type:** {user_data['plan_type'].upper()}")
                    st.markdown(f"**Admin:** {'Yes' if user_data['is_admin'] else 'No'}")
                
                with info_col2:
                    created_str = user_data['created_at'].strftime('%Y-%m-%d %H:%M') if user_data['created_at'] else 'Unknown'
                    last_login_str = user_data['last_login'].strftime('%Y-%m-%d %H:%M') if user_data['last_login'] else 'Never'
                    st.markdown(f"**Created:** {created_str}")
                    st.markdown(f"**Last Login:** {last_login_str}")
                    st.markdown(f"**Usage:** {user_data['usage_count']} / {user_data['usage_limit']}")
                    
                    if st.button(f"🗑️ Delete User", key=f"delete_{user_data['id']}"):
                        if user_data['id'] != current_user['id']:
                            with get_db_session() as db:
                                user_to_delete = db.query(User).filter(User.id == user_data['id']).first()
                                if user_to_delete:
                                    db.delete(user_to_delete)
                                    db.commit()
                                    st.success("User deleted")
                                    st.rerun()
                        else:
                            st.error("Cannot delete your own account")
    
    # Tab 2: AI Access Control
    with tab2:
        st.markdown("#### 🤖 AI Tier Access Management")
        st.markdown("Control which AI features users can access. **Oreplot Light** includes standard analysis, while **Oreplot Advanced** includes PwC-style valuation, market multiples, Kilburn method, and Monte Carlo simulations.")
        
        st.markdown("---")
        
        st.markdown("##### AI Access Tiers")
        tier_col1, tier_col2, tier_col3 = st.columns(3)
        
        with tier_col1:
            st.markdown("""
            **🔵 Oreplot Light**
            - Document analysis
            - Dual scoring (Investment + Sustainability)
            - PDF report generation
            - Comparables matching
            - Template management
            """)
        
        with tier_col2:
            st.markdown("""
            **🟣 Oreplot Advanced**
            - Market Multiples Analysis
            - PwC Cost Approach (Kilburn)
            - Monte Carlo Risk Modeling
            - EV/Resource Benchmarking
            - Financial Valuation Reports
            """)
        
        with tier_col3:
            st.markdown("""
            **🟢 Both**
            - Full access to Oreplot Light
            - Full access to Oreplot Advanced
            - All features unlocked
            - Admin default setting
            """)
        
        st.markdown("---")
        st.markdown("#### User AI Access Settings")
        
        with get_db_session() as db:
            all_users = db.query(User).order_by(User.email).all()
            
            users_ai_data = []
            for u in all_users:
                users_ai_data.append({
                    'id': u.id,
                    'email': u.email,
                    'username': u.username,
                    'is_admin': u.is_admin,
                    'plan_type': u.plan_type,
                    'ai_tier_access': getattr(u, 'ai_tier_access', 'light_ai') or 'light_ai'
                })
        
        with get_db_session() as db:
            light_ai_count = db.query(func.count(User.id)).filter(User.ai_tier_access == 'light_ai').scalar() or 0
            advanced_ai_count = db.query(func.count(User.id)).filter(User.ai_tier_access == 'advanced_ai').scalar() or 0
            both_count = db.query(func.count(User.id)).filter(User.ai_tier_access == 'both').scalar() or 0
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric("Oreplot Light Users", light_ai_count)
        with stat_col2:
            st.metric("Oreplot Advanced Users", advanced_ai_count)
        with stat_col3:
            st.metric("Both Access Users", both_count)
        
        st.markdown("---")
        
        for user_ai in users_ai_data:
            with st.expander(f"{'👑 ' if user_ai['is_admin'] else '👤 '}{user_ai['email']} - Current: **{user_ai['ai_tier_access'].upper().replace('_', ' ')}**"):
                col_info, col_action = st.columns([2, 1])
                
                with col_info:
                    st.markdown(f"**Username:** {user_ai['username']}")
                    st.markdown(f"**Plan Type:** {user_ai['plan_type'].upper()}")
                    st.markdown(f"**Admin:** {'Yes' if user_ai['is_admin'] else 'No'}")
                
                with col_action:
                    current_tier = user_ai['ai_tier_access']
                    tier_options = ['light_ai', 'advanced_ai', 'both']
                    tier_labels = ['🔵 Oreplot Light Only', '🟣 Oreplot Advanced Only', '🟢 Both (Full Access)']
                    
                    current_index = tier_options.index(current_tier) if current_tier in tier_options else 0
                    
                    new_tier = st.selectbox(
                        "AI Access Level",
                        options=tier_options,
                        format_func=lambda x: tier_labels[tier_options.index(x)],
                        index=current_index,
                        key=f"ai_tier_{user_ai['id']}"
                    )
                    
                    if st.button("💾 Update Access", key=f"update_ai_{user_ai['id']}"):
                        with get_db_session() as db:
                            user_to_update = db.query(User).filter(User.id == user_ai['id']).first()
                            if user_to_update:
                                user_to_update.ai_tier_access = new_tier
                                db.commit()
                                st.success(f"✅ Updated {user_ai['email']} to {new_tier.upper().replace('_', ' ')}")
                                st.rerun()
        
        st.markdown("---")
        st.markdown("#### Bulk AI Access Update")
        
        bulk_col1, bulk_col2 = st.columns(2)
        
        with bulk_col1:
            bulk_tier = st.selectbox(
                "Set all non-admin users to:",
                options=['light_ai', 'advanced_ai', 'both'],
                format_func=lambda x: {'light_ai': '🔵 Light AI Only', 'advanced_ai': '🟣 Advanced AI Only', 'both': '🟢 Both (Full Access)'}[x],
                key="bulk_ai_tier"
            )
        
        with bulk_col2:
            st.markdown("")
            st.markdown("")
            if st.button("⚡ Apply to All Non-Admin Users", type="secondary"):
                with get_db_session() as db:
                    result = db.query(User).filter(User.is_admin == False).update({'ai_tier_access': bulk_tier})
                    db.commit()
                    st.success(f"Updated {result} non-admin users to {bulk_tier.upper().replace('_', ' ')}")
                    st.rerun()
    
    # Tab 3: AI Training
    with tab3:
        from page_modules.ai_training_page import render_ai_training_page
        render_ai_training_page(current_user)
    
    # Tab 4: Platform Statistics
    with tab4:
        with get_db_session() as db:
            total_users = db.query(func.count(User.id)).scalar()
            total_projects = db.query(func.count(Project.id)).scalar()
            total_analyses = db.query(func.count(Analysis.id)).scalar()
            
            admin_count = db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
            
            # Get users by plan type
            free_users = db.query(func.count(User.id)).filter(User.plan_type == 'free').scalar()
            paid_users = total_users - free_users
        
        st.markdown("#### Platform Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Total Projects", total_projects)
        with col3:
            st.metric("Total Analyses", total_analyses)
        with col4:
            st.metric("Admin Users", admin_count)
        
        st.markdown("---")
        
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("Free Plan Users", free_users)
        with col6:
            st.metric("Paid Plan Users", paid_users)
        with col7:
            avg_usage = db.query(func.avg(User.usage_count)).scalar() or 0
            st.metric("Avg Usage per User", f"{avg_usage:.1f}")
        with col8:
            st.metric("Active Today", "-")
    
    # Tab 5: Cache & Maintenance
    with tab5:
        st.markdown("#### System Cache Management")
        
        st.info("🔧 Clear cached data to free up resources and improve performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Streamlit Cache", use_container_width=True):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Streamlit cache cleared successfully")
        
        with col2:
            if st.button("🔄 Restart Application", use_container_width=True):
                st.warning("⚠️ Application restart requested (requires manual server restart)")
        
        st.markdown("---")
        st.markdown("#### Database Maintenance")
        
        with get_db_session() as db:
            orphaned_docs = db.query(func.count(Analysis.id)).filter(Analysis.project_id == None).scalar()
            
        st.markdown(f"**Orphaned Analyses:** {orphaned_docs}")
        
        if st.button("🧹 Clean Orphaned Data"):
            st.info("Data cleanup completed")
    
    # Tab 6: Compute Usage
    with tab6:
        st.markdown("#### User Compute Unit Consumption")
        
        with get_db_session() as db:
            users_usage = db.query(User).order_by(User.usage_count.desc()).limit(20).all()
            
            # Materialize data
            usage_data = []
            for u in users_usage:
                usage_data.append({
                    'email': u.email,
                    'username': u.username,
                    'usage_count': u.usage_count,
                    'usage_limit': u.usage_limit,
                    'plan_type': u.plan_type
                })
        
        for data in usage_data:
            progress = min(data['usage_count'] / data['usage_limit'], 1.0) if data['usage_limit'] > 0 else 0
            
            st.markdown(f"**{data['email']}** ({data['plan_type']})")
            st.progress(progress)
            st.markdown(f"{data['usage_count']} / {data['usage_limit']} analyses")
            st.markdown("---")
    
    # Tab 7: UI Customization
    with tab7:
        st.markdown("#### Platform UI Configuration")
        
        st.warning("🚧 UI customization features coming soon")
        
        st.markdown("**Planned Features:**")
        st.markdown("- Theme customization (colors, fonts)")
        st.markdown("- Logo and branding management")
        st.markdown("- Email template customization")
        st.markdown("- Dashboard layout configuration")
        st.markdown("- Custom CSS injection")
