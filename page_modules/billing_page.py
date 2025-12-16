import streamlit as st
from database import get_db_session
from models import Analysis
from datetime import datetime
from sqlalchemy import func, extract

def render_billing_page(current_user):
    """Render usage page showing monthly AI analysis usage metrics"""
    
    st.title("📊 Usage")
    st.markdown("### Monthly AI Analysis Usage Metrics")
    
    # Get current month and year
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate usage statistics from database
    with get_db_session() as session:
        # Get analyses for current month
        month_analyses_orm = session.query(Analysis).join(
            Analysis.project
        ).filter(
            Analysis.project.has(user_id=current_user['id']),
            extract('month', Analysis.created_at) == current_month,
            extract('year', Analysis.created_at) == current_year
        ).all()
        
        # Materialize to dictionaries to avoid DetachedInstanceError
        month_analyses = []
        for analysis in month_analyses_orm:
            month_analyses.append({
                'id': analysis.id,
                'project_name': analysis.project.name if analysis.project else 'Unknown Project',
                'total_score': analysis.total_score,
                'created_at': analysis.created_at
            })
        
        # Get total analyses count
        total_analyses = session.query(func.count(Analysis.id)).join(
            Analysis.project
        ).filter(
            Analysis.project.has(user_id=current_user['id'])
        ).scalar()
        
        # Get analyses by risk category this month
        low_risk = len([a for a in month_analyses if a['total_score'] >= 70])
        moderate_risk = len([a for a in month_analyses if 50 <= a['total_score'] < 70])
        high_risk = len([a for a in month_analyses if a['total_score'] < 50])
    
    # Display current month usage
    st.markdown(f"### 📅 {current_date.strftime('%B %Y')} Usage")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 2.5rem; font-weight: 800; color: #3B82F6; margin-bottom: 0.5rem;">
                {len(month_analyses)}
            </div>
            <div style="color: #64748B; font-size: 0.875rem; font-weight: 600;">
                ANALYSES THIS MONTH
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 2.5rem; font-weight: 800; color: #10B981; margin-bottom: 0.5rem;">
                {low_risk}
            </div>
            <div style="color: #64748B; font-size: 0.875rem; font-weight: 600;">
                LOW RISK
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 2.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 0.5rem;">
                {moderate_risk}
            </div>
            <div style="color: #64748B; font-size: 0.875rem; font-weight: 600;">
                MODERATE RISK
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 2.5rem; font-weight: 800; color: #EF4444; margin-bottom: 0.5rem;">
                {high_risk}
            </div>
            <div style="color: #64748B; font-size: 0.875rem; font-weight: 600;">
                HIGH RISK
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # All-time usage statistics
    st.markdown("### 📊 All-Time Statistics")
    
    col_all1, col_all2 = st.columns(2)
    
    with col_all1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%); padding: 2rem; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="font-size: 3.5rem; font-weight: 800; margin-bottom: 0.5rem;">
                {total_analyses}
            </div>
            <div style="font-size: 1.25rem; opacity: 0.9;">
                Total Analyses Completed
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_all2:
        avg_score = (sum(a['total_score'] for a in month_analyses) / len(month_analyses)) if month_analyses else 0
        
        st.markdown(f"""
        <div style="background: white; padding: 2rem; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 3.5rem; font-weight: 800; color: #3B82F6; margin-bottom: 0.5rem;">
                {avg_score:.1f}
            </div>
            <div style="font-size: 1.25rem; color: #64748B;">
                Average Score This Month
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Monthly breakdown
    st.markdown("### 📈 Recent Activity")
    
    if month_analyses:
        st.markdown("**Recent analyses this month:**")
        
        for analysis in sorted(month_analyses, key=lambda x: x['created_at'], reverse=True)[:10]:
            # Determine risk color
            if analysis['total_score'] >= 70:
                risk_color = "#10B981"
                risk_label = "LOW RISK"
            elif analysis['total_score'] >= 50:
                risk_color = "#F59E0B"
                risk_label = "MODERATE"
            else:
                risk_color = "#EF4444"
                risk_label = "HIGH RISK"
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 8px; border-left: 4px solid {risk_color}; margin-bottom: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; color: #0F172A;">{analysis['project_name']}</div>
                        <div style="font-size: 0.875rem; color: #64748B;">{analysis['created_at'].strftime('%b %d, %Y at %I:%M %p')}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: 700; color: {risk_color};">{analysis['total_score']:.1f}</div>
                        <div style="background: {risk_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600;">
                            {risk_label}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No analyses completed this month yet. Start a new analysis to see your usage statistics!")
