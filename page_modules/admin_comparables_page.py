"""
Admin page for managing comparables database
Only accessible to admin users (cokhaligzada@gmail.com)
"""

import streamlit as st
from datetime import datetime
from comparables_ingestion import ComparablesIngestionService
from comparables_scheduler import get_scheduler_status, trigger_manual_update, start_scheduler

def render_admin_comparables_page(current_user):
    """Render the admin comparables management page"""
    
    # Check if user is admin
    if current_user['email'] != 'cokhaligzada@gmail.com':
        st.error("⛔ Access Denied - Admin privileges required")
        st.info("This page is only accessible to system administrators.")
        return
    
    st.title("🔧 Comparables Database Management")
    st.markdown("*Admin panel for managing the global comparables database*")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📋 Pending Approvals", "⏰ Scheduler Status", "📊 Ingestion History"])
    
    with tab1:
        render_pending_approvals()
    
    with tab2:
        render_scheduler_status()
    
    with tab3:
        render_ingestion_history()

def render_pending_approvals():
    """Render pending project approvals"""
    st.subheader("Pending Project Approvals")
    st.markdown("Review and approve new comparable projects before they appear in the public database.")
    
    # Get pending projects
    pending_projects = ComparablesIngestionService.get_pending_projects(limit=50)
    
    if not pending_projects:
        st.info("✅ No projects pending approval")
        return
    
    st.markdown(f"**{len(pending_projects)} projects awaiting review**")
    
    # Display each pending project
    for project in pending_projects:
        with st.expander(f"📁 {project.name} - {project.commodity} ({project.country})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Basic Information**")
                st.write(f"**Company:** {project.company or 'N/A'}")
                st.write(f"**Location:** {project.location or 'N/A'}")
                st.write(f"**Country:** {project.country or 'N/A'}")
                st.write(f"**Commodity:** {project.commodity or 'N/A'}")
                st.write(f"**Commodity Group:** {project.commodity_group or 'N/A'}")
                st.write(f"**Project Stage:** {project.project_stage or 'N/A'}")
                st.write(f"**Development Stage:** {project.development_stage_detail or 'N/A'}")
                st.write(f"**Deposit Style:** {project.deposit_style or 'N/A'}")
            
            with col2:
                st.markdown("**Technical Data**")
                if project.total_resource_mt:
                    st.write(f"**Resource:** {project.total_resource_mt:.2f} Mt")
                if project.grade and project.grade_unit:
                    st.write(f"**Grade:** {project.grade:.2f} {project.grade_unit}")
                if project.capex_millions_usd:
                    st.write(f"**CAPEX:** ${project.capex_millions_usd:.1f}M")
                if project.npv_millions_usd:
                    st.write(f"**NPV:** ${project.npv_millions_usd:.1f}M")
                if project.irr_percent:
                    st.write(f"**IRR:** {project.irr_percent:.1f}%")
                if project.jurisdiction_risk_band:
                    st.write(f"**Jurisdiction Risk:** {project.jurisdiction_risk_band}")
                if project.overall_score:
                    st.write(f"**Overall Score:** {project.overall_score:.0f}/100")
            
            st.markdown("---")
            st.write(f"**Data Source:** {project.data_source or 'Unknown'}")
            st.write(f"**Created:** {project.created_at.strftime('%Y-%m-%d %H:%M') if project.created_at else 'N/A'}")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 3])
            
            with col1:
                if st.button("✅ Approve", key=f"approve_{project.id}", use_container_width=True):
                    if ComparablesIngestionService.approve_project(project.id):
                        st.success(f"✅ {project.name} approved!")
                        st.rerun()
                    else:
                        st.error("Failed to approve project")
            
            with col2:
                if st.button("❌ Reject", key=f"reject_{project.id}", use_container_width=True):
                    if ComparablesIngestionService.reject_project(project.id):
                        st.success(f"🗑️ {project.name} rejected and deleted")
                        st.rerun()
                    else:
                        st.error("Failed to reject project")

def render_scheduler_status():
    """Render scheduler status and controls"""
    st.subheader("⏰ Weekly Update Scheduler")
    st.markdown("Automatic weekly ingestion of new comparable projects.")
    
    # Start scheduler if not running
    try:
        start_scheduler()
    except Exception as e:
        st.warning(f"Note: Scheduler initialization - {str(e)}")
    
    # Get status
    status = get_scheduler_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if status['running']:
            st.success("✅ Scheduler Active")
        else:
            st.error("❌ Scheduler Inactive")
    
    with col2:
        if status.get('next_run'):
            st.info(f"⏰ Next Run: {status['next_run']}")
        else:
            st.info("⏰ Next Run: Not scheduled")
    
    st.markdown("---")
    
    # Scheduler configuration
    st.markdown("**Schedule Configuration**")
    st.write("- **Frequency:** Weekly (Every Sunday)")
    st.write("- **Time:** 2:00 AM UTC")
    st.write("- **Action:** Fetch and add new comparable projects for admin review")
    
    st.markdown("---")
    
    # Manual trigger
    st.markdown("**Manual Controls**")
    
    if st.button("▶️ Run Update Now", use_container_width=True):
        with st.spinner("Running manual update..."):
            try:
                trigger_manual_update()
                st.success("✅ Manual update completed! Check Ingestion History for results.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update failed: {str(e)}")

def render_ingestion_history():
    """Render ingestion job history"""
    st.subheader("📊 Ingestion History")
    st.markdown("Recent database update jobs and their results.")
    
    # Get history
    jobs = ComparablesIngestionService.get_ingestion_history(limit=20)
    
    if not jobs:
        st.info("No ingestion jobs found")
        return
    
    # Display as table
    for job in jobs:
        with st.expander(
            f"{'✅' if job.status == 'completed' else '❌' if job.status == 'failed' else '⏳'} "
            f"Job #{job.id} - {job.status.upper()} - {job.started_at.strftime('%Y-%m-%d %H:%M')}"
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", job.total_records or 0)
            
            with col2:
                st.metric("Successful", job.successful_records or 0)
            
            with col3:
                st.metric("Failed", job.failed_records or 0)
            
            if job.completed_at:
                duration = (job.completed_at - job.started_at).total_seconds()
                st.write(f"**Duration:** {duration:.1f} seconds")
            
            if job.error_log:
                st.error(f"**Error Log:**\n{job.error_log}")
