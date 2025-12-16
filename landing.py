import streamlit as st

st.set_page_config(
    page_title="Oreplot - AI Mining Due Diligence",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background-color: #FFFFFF;
    }
    .stApp {
        background-color: #FFFFFF;
    }
    
    [data-testid="stSidebar"] {
        display: none;
    }
    
    .landing-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.25rem 3rem;
        background-color: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    
    .logo-text {
        font-size: 1.75rem;
        font-weight: 900;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.05em;
    }
    
    .nav-links {
        display: flex;
        gap: 2.5rem;
        align-items: center;
    }
    
    .nav-link {
        color: #334155;
        font-weight: 500;
        font-size: 0.95rem;
        text-decoration: none;
        transition: color 0.2s;
        cursor: pointer;
    }
    
    .nav-link:hover {
        color: #3B82F6;
    }
    
    .auth-buttons {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .btn-signin {
        color: #334155;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.5rem 1.25rem;
        border-radius: 8px;
        transition: background-color 0.2s;
        cursor: pointer;
        background-color: transparent;
        border: none;
    }
    
    .btn-signin:hover {
        background-color: #F1F5F9;
    }
    
    .btn-signup {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        color: #FFFFFF;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0.5rem 1.5rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
    }
    
    .btn-signup:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 12px -1px rgba(59, 130, 246, 0.3);
    }
    
    .hero-section {
        text-align: center;
        padding: 5rem 2rem;
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 900;
        color: #0F172A;
        line-height: 1.1;
        letter-spacing: -0.03em;
        margin-bottom: 1.5rem;
    }
    
    .hero-gradient {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        font-size: 1.35rem;
        color: #64748B;
        font-weight: 400;
        margin-bottom: 3rem;
        line-height: 1.6;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .hero-cta-buttons {
        display: flex;
        gap: 1.25rem;
        justify-content: center;
        align-items: center;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        color: #FFFFFF;
        font-weight: 600;
        font-size: 1.05rem;
        padding: 0.875rem 2.25rem;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.3);
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -4px rgba(59, 130, 246, 0.4);
    }
    
    .btn-secondary {
        background: #FFFFFF;
        color: #334155;
        font-weight: 600;
        font-size: 1.05rem;
        padding: 0.875rem 2.25rem;
        border-radius: 10px;
        border: 2px solid #CBD5E1;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .btn-secondary:hover {
        border-color: #3B82F6;
        background-color: #F0F9FF;
    }
    
    .features-section {
        padding: 5rem 3rem;
        background-color: #FFFFFF;
    }
    
    .section-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #0F172A;
        text-align: center;
        margin-bottom: 1rem;
        letter-spacing: -0.02em;
    }
    
    .section-subtitle {
        font-size: 1.15rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 4rem;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    }
    
    .feature-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 2rem;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.12);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 0.75rem;
    }
    
    .feature-description {
        color: #64748B;
        line-height: 1.7;
        font-size: 1rem;
    }
    
    .cta-section {
        padding: 5rem 3rem;
        background: linear-gradient(135deg, #3B82F6, #8B5CF6);
        text-align: center;
    }
    
    .cta-title {
        font-size: 2.75rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 1.25rem;
        letter-spacing: -0.02em;
    }
    
    .cta-subtitle {
        font-size: 1.2rem;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 2.5rem;
    }
    
    .btn-white {
        background: #FFFFFF;
        color: #3B82F6;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 1rem 2.5rem;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.2);
    }
    
    .btn-white:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -4px rgba(0, 0, 0, 0.3);
    }
    
    .footer {
        padding: 3rem;
        background-color: #F8F9FB;
        border-top: 1px solid #E5E7EB;
    }
    
    .footer-text {
        text-align: center;
        color: #64748B;
        font-size: 0.9rem;
    }
    
    .stButton>button {
        width: auto !important;
    }
</style>
""", unsafe_allow_html=True)

col_header1, col_header2, col_header3 = st.columns([2, 3, 2])
with col_header1:
    st.image("attached_assets/plot_1761767561805.png", width=150)
with col_header2:
    st.markdown("""
    <div style="display: flex; gap: 2rem; align-items: center; justify-content: center; margin-top: 1.5rem;">
        <a class="nav-link" href="#platform">Platform</a>
        <a class="nav-link" href="#solutions">Solutions</a>
        <a class="nav-link" href="#blog">Blog</a>
        <a class="nav-link" href="#contact">Contact</a>
    </div>
    """, unsafe_allow_html=True)
with col_header3:
    col_space, col_signin, col_signup = st.columns([6, 1, 1])
    with col_signin:
        if st.button("Sign In", key="header_signin", use_container_width=True):
            st.session_state.show_app = True
            st.rerun()
    with col_signup:
        if st.button("Get Started", key="header_signup", use_container_width=True, type="primary"):
            st.session_state.show_app = True
            st.rerun()
st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #E5E7EB;'>", unsafe_allow_html=True)

st.markdown("""
<div class="hero-section">
    <div class="hero-title">
        Transform Mining Due Diligence<br>
        with <span class="hero-gradient">AI Intelligence</span>
    </div>
    <div class="hero-subtitle">
        Oreplot analyzes mining projects, validates drill databases, and generates comprehensive 
        investment risk scores in minutes—powered by advanced AI and industry-standard QAQC protocols.
    </div>
</div>
""", unsafe_allow_html=True)

col_cta1, col_cta2, col_cta3, col_cta4, col_cta5 = st.columns([2, 1, 1, 1, 2])
with col_cta2:
    if st.button("📧 Contact Sales", key="hero_contact", use_container_width=True):
        st.info("📧 Contact us at: cokhaligzada@gmail.com")
with col_cta3:
    if st.button("📅 Book Demo", key="hero_demo", use_container_width=True):
        st.info("📅 Contact us to schedule a demo: cokhaligzada@gmail.com")
with col_cta4:
    if st.button("🚀 Get Started", key="hero_start", use_container_width=True, type="primary"):
        st.session_state.show_app = True
        st.rerun()

st.markdown("")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📄</div>
        <div class="feature-title">Multi-Format Document Processing</div>
        <div class="feature-description">
            Upload PDF, DOCX, XLSX, and drill databases. Our AI extracts technical facts 
            from geological reports, assay certificates, and regulatory filings.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">Industry-Standard QAQC</div>
        <div class="feature-description">
            Automated validation of drill databases including collar surveys, sample intervals, 
            duplicate analysis, outlier detection, and statistical quality control.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Customizable Scoring Templates</div>
        <div class="feature-description">
            Create custom scoring templates with adjustable weights for geology, economics, 
            legal, ESG, and data quality to match your investment strategy.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a id="platform"></a>', unsafe_allow_html=True)
st.markdown("""
<div class="features-section">
    <div class="section-title">Platform Features</div>
    <div class="section-subtitle">
        Everything you need for comprehensive mining due diligence in one platform
    </div>
</div>
""", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🤖</div>
        <div class="feature-title">AI-Powered Analysis</div>
        <div class="feature-description">
            Advanced natural language processing analyzes your documents against NI-43-101 
            and JORC standards to provide transparent, repeatable assessments.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📈</div>
        <div class="feature-title">Investment Risk Scoring</div>
        <div class="feature-description">
            Compute weighted scores (0-100) across six categories with clear risk banding: 
            Fast-track (≥70), Deeper DD (50-69), or Reject/Restructure (<50).
        </div>
    </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📑</div>
        <div class="feature-title">Professional PDF Reports</div>
        <div class="feature-description">
            Generate stakeholder-ready due diligence reports with detailed analysis, 
            scores, recommendations, and QAQC findings in portable PDF format.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a id="solutions"></a>', unsafe_allow_html=True)
st.markdown("""
<div class="features-section">
    <div class="section-title">Solutions for Every Stage</div>
    <div class="section-subtitle">
        From early-stage exploration to near-production assets
    </div>
</div>
""", unsafe_allow_html=True)

sol_col1, sol_col2, sol_col3 = st.columns(3)

with sol_col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔬</div>
        <div class="feature-title">Early-Stage Exploration</div>
        <div class="feature-description">
            Emphasize geology and prospectivity scoring with custom templates 
            optimized for greenfield projects and conceptual resources.
        </div>
    </div>
    """, unsafe_allow_html=True)

with sol_col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚒️</div>
        <div class="feature-title">Resource Development</div>
        <div class="feature-description">
            Balance resource potential, data quality, and permitting considerations 
            for advancing projects through feasibility studies.
        </div>
    </div>
    """, unsafe_allow_html=True)

with sol_col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🏭</div>
        <div class="feature-title">Near-Production Assets</div>
        <div class="feature-description">
            Focus on economics, legal compliance, and operational readiness 
            for projects approaching construction or production.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a id="blog"></a>', unsafe_allow_html=True)
st.markdown("""
<div class="features-section">
    <div class="section-title">Latest Insights</div>
    <div class="section-subtitle">
        Industry trends, best practices, and mining due diligence expertise
    </div>
</div>
""", unsafe_allow_html=True)

blog_col1, blog_col2, blog_col3 = st.columns(3)

with blog_col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📝</div>
        <div class="feature-title">The Future of Mining DD</div>
        <div class="feature-description">
            How AI and automation are transforming traditional due diligence 
            processes in the mining sector.
        </div>
    </div>
    """, unsafe_allow_html=True)

with blog_col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">QAQC Best Practices</div>
        <div class="feature-description">
            Industry-standard quality control protocols for drill databases 
            and assay data validation.
        </div>
    </div>
    """, unsafe_allow_html=True)

with blog_col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">💡</div>
        <div class="feature-title">Risk Scoring Methodology</div>
        <div class="feature-description">
            Understanding weighted category scoring and how to customize 
            templates for your investment strategy.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<a id="demo"></a><a id="contact"></a>', unsafe_allow_html=True)
st.markdown("""
<div class="cta-section">
    <div class="cta-title">Ready to Transform Your Mining Investment Process?</div>
    <div class="cta-subtitle">
        Join leading mining investors using AI-powered due diligence to make faster, 
        more informed investment decisions.
    </div>
</div>
""", unsafe_allow_html=True)

col_final1, col_final2, col_final3 = st.columns([2, 1, 2])
with col_final2:
    if st.button("🚀 Get Started Free", key="cta_final", use_container_width=True, type="primary"):
        st.session_state.show_app = True
        st.rerun()

st.markdown("")

st.markdown("""
<div class="footer">
    <div class="footer-text">
        © 2025 Oreplot. All rights reserved. | Privacy Policy | Terms of Service
    </div>
</div>
""", unsafe_allow_html=True)
