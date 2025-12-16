import streamlit as st
from database import get_db_session
from models import Team, TeamMember, User
from datetime import datetime

def render_team_page(current_user):
    """Render team/members page for managing access and roles"""
    
    st.title("👥 Team & Members")
    st.markdown("### Collaborate with Your Team")
    
    # Get user's teams (owned and member of) - eagerly load members
    with get_db_session() as db:
        owned_teams_query = db.query(Team).filter(Team.owner_id == current_user['id']).all()
        member_teams_query = db.query(Team).join(TeamMember).filter(TeamMember.user_id == current_user['id']).all()
        
        # Convert to dicts with all needed data while session is open
        owned_teams = []
        for team in owned_teams_query:
            team_dict = {
                'id': team.id,
                'name': team.name,
                'description': team.description,
                'owner_id': team.owner_id,
                'created_at': team.created_at,
                'members': []
            }
            for member in team.members:
                member_user = db.query(User).filter(User.id == member.user_id).first()
                team_dict['members'].append({
                    'id': member.id,
                    'user_id': member.user_id,
                    'username': member_user.username if member_user else 'Unknown',
                    'email': member_user.email if member_user else '',
                    'role': member.role,
                    'status': member.status
                })
            owned_teams.append(team_dict)
        
        member_teams = []
        for team in member_teams_query:
            if team.id not in [t['id'] for t in owned_teams]:  # Avoid duplicates
                team_dict = {
                    'id': team.id,
                    'name': team.name,
                    'description': team.description,
                    'owner_id': team.owner_id,
                    'created_at': team.created_at,
                    'members': []
                }
                for member in team.members:
                    member_user = db.query(User).filter(User.id == member.user_id).first()
                    team_dict['members'].append({
                        'id': member.id,
                        'user_id': member.user_id,
                        'username': member_user.username if member_user else 'Unknown',
                        'email': member_user.email if member_user else '',
                        'role': member.role,
                        'status': member.status
                    })
                member_teams.append(team_dict)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["My Teams", "Create Team", "Invitations"])
    
    with tab1:
        st.markdown("#### Your Teams")
        
        all_teams = owned_teams + member_teams
        
        if all_teams:
            for team in all_teams:
                is_owner = team['owner_id'] == current_user['id']
                
                with st.expander(f"{'👑' if is_owner else '👤'} {team['name']} ({len(team['members'])} members)"):
                    st.markdown(f"**Description:** {team['description'] or 'No description'}")
                    st.markdown(f"**Created:** {team['created_at'].strftime('%B %d, %Y') if hasattr(team['created_at'], 'strftime') else 'Recently'}")
                    
                    if is_owner:
                        st.success("✓ You are the owner of this team")
                    
                    st.markdown("---")
                    st.markdown("**Team Members:**")
                    
                    # Display team members
                    for member in team['members']:
                        col_member, col_role, col_actions = st.columns([3, 1, 1])
                        
                        with col_member:
                            owner_badge = " 👑" if member['user_id'] == team['owner_id'] else ""
                            st.markdown(f"**{member['username']}**{owner_badge}")
                            st.caption(member['email'])
                        
                        with col_role:
                            st.markdown(f"**{member['role'].upper()}**")
                        
                        with col_actions:
                            if is_owner and member['user_id'] != team['owner_id']:
                                if st.button("Remove", key=f"remove_{member['id']}", use_container_width=True):
                                    with get_db_session() as db:
                                        member_to_remove = db.query(TeamMember).filter(TeamMember.id == member['id']).first()
                                        db.delete(member_to_remove)
                                        db.commit()
                                    st.success(f"Removed {member['username']} from team")
                                    st.rerun()
                    
                    if is_owner:
                        st.markdown("---")
                        st.markdown("**Invite New Member:**")
                        
                        col_email, col_role, col_invite = st.columns([3, 1, 1])
                        
                        with col_email:
                            invite_email = st.text_input("Email", key=f"invite_email_{team['id']}", placeholder="colleague@example.com")
                        
                        with col_role:
                            invite_role = st.selectbox("Role", options=["member", "admin"], key=f"invite_role_{team['id']}")
                        
                        with col_invite:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("📧 Send Invite", key=f"send_invite_{team['id']}", use_container_width=True):
                                if invite_email:
                                    with get_db_session() as db:
                                        invited_user = db.query(User).filter(User.email == invite_email).first()
                                        
                                        if invited_user:
                                            existing_member = db.query(TeamMember).filter(
                                                TeamMember.team_id == team['id'],
                                                TeamMember.user_id == invited_user.id
                                            ).first()
                                            
                                            if not existing_member:
                                                new_member = TeamMember(
                                                    team_id=team['id'],
                                                    user_id=invited_user.id,
                                                    role=invite_role,
                                                    status='invited'
                                                )
                                                db.add(new_member)
                                                db.commit()
                                                st.success(f"✅ Invitation sent to {invite_email}!")
                                                st.rerun()
                                            else:
                                                st.warning("User is already a team member")
                                        else:
                                            st.error("User not found. They need to create an account first.")
                                else:
                                    st.error("Please enter an email address")
        else:
            st.info("You're not part of any teams yet. Create your first team to collaborate!")
    
    with tab2:
        st.markdown("#### Create a New Team")
        
        with st.form("create_team_form"):
            team_name = st.text_input("Team Name", placeholder="Exploration Team Alpha")
            team_description = st.text_area("Description", placeholder="Describe the purpose of this team...")
            
            submitted = st.form_submit_button("➕ Create Team", type="primary")
            
            if submitted:
                if team_name:
                    with get_db_session() as db:
                        new_team = Team(
                            name=team_name,
                            description=team_description,
                            owner_id=current_user['id']
                        )
                        db.add(new_team)
                        db.flush()
                        
                        # Add owner as first member
                        owner_member = TeamMember(
                            team_id=new_team.id,
                            user_id=current_user['id'],
                            role='owner',
                            status='active',
                            joined_at=datetime.utcnow()
                        )
                        db.add(owner_member)
                        db.commit()
                    
                    st.success(f"✅ Team '{team_name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a team name")
    
    with tab3:
        st.markdown("#### Pending Invitations")
        
        # Get pending invitations for current user - convert to dicts
        with get_db_session() as db:
            pending_invites_query = db.query(TeamMember).filter(
                TeamMember.user_id == current_user['id'],
                TeamMember.status == 'invited'
            ).all()
            
            pending_invites = []
            for invite in pending_invites_query:
                team = db.query(Team).filter(Team.id == invite.team_id).first()
                owner = db.query(User).filter(User.id == team.owner_id).first() if team else None
                
                pending_invites.append({
                    'id': invite.id,
                    'team_id': invite.team_id,
                    'role': invite.role,
                    'team_name': team.name if team else 'Unknown',
                    'owner_username': owner.username if owner else 'Unknown',
                    'owner_email': owner.email if owner else ''
                })
        
        if pending_invites:
            for invite in pending_invites:
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #E5E7EB;">
                        <div style="font-weight: 600; font-size: 1.125rem; margin-bottom: 0.5rem;">{invite['team_name']}</div>
                        <div style="font-size: 0.875rem; color: #64748B;">
                            Invited by: {invite['owner_username']} ({invite['owner_email']})<br>
                            Role: {invite['role'].upper()}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_actions:
                    col_accept, col_decline = st.columns(2)
                    
                    with col_accept:
                        if st.button("✅ Accept", key=f"accept_{invite['id']}", use_container_width=True):
                            with get_db_session() as db:
                                member_to_update = db.query(TeamMember).filter(TeamMember.id == invite['id']).first()
                                member_to_update.status = 'active'
                                member_to_update.joined_at = datetime.utcnow()
                                db.commit()
                            st.success("Invitation accepted!")
                            st.rerun()
                    
                    with col_decline:
                        if st.button("❌ Decline", key=f"decline_{invite['id']}", use_container_width=True):
                            with get_db_session() as db:
                                member_to_delete = db.query(TeamMember).filter(TeamMember.id == invite['id']).first()
                                db.delete(member_to_delete)
                                db.commit()
                            st.info("Invitation declined")
                            st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No pending invitations")
    
    st.markdown("---")
    
    # Team Benefits
    st.markdown("### ✨ Team Features")
    
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    
    with col_feat1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem;">🤝</div>
            <div style="font-weight: 600; margin-top: 0.5rem;">Collaborate</div>
            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem;">Work together on projects</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_feat2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem;">🔒</div>
            <div style="font-weight: 600; margin-top: 0.5rem;">Role-Based Access</div>
            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem;">Control permissions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_feat3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem;">📊</div>
            <div style="font-weight: 600; margin-top: 0.5rem;">Shared Insights</div>
            <div style="font-size: 0.875rem; color: #64748B; margin-top: 0.25rem;">Share analyses</div>
        </div>
        """, unsafe_allow_html=True)
