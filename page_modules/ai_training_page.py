"""
AI Training Page - Enhanced RAG System
Simplified interface for uploading training documents that automatically improve AI accuracy.
"""

import streamlit as st
import os
from datetime import datetime

from training_rag import (
    process_training_document,
    get_training_statistics,
    get_training_documents,
    delete_training_document,
    delete_all_training
)

# Hard safety limits
MAX_FILES_PER_UPLOAD = 80
BATCH_SIZE = 10

TRAINING_CATEGORIES = [
    {"name": "30_geoscience_data", "display_name": "30-Geoscience Data", "description": "Geoscience data and reports"},
    {"name": "40_spatial_data", "display_name": "40-Spatial Data", "description": "Spatial and mapping data"},
    {"name": "50_3d_analysis", "display_name": "50-3D and Analysis", "description": "3D modeling and analysis reports"},
    {"name": "60_reporting", "display_name": "60-Reporting", "description": "Reporting and summary documents"},
    {"name": "70_literature", "display_name": "70-Literature", "description": "Literature and reference materials"},
    {"name": "2024_environmental_ishkoday", "display_name": "2024 Environmental Report on Ishkoday", "description": "2024 Environmental Report on Ishkoday"},
    {"name": "geoscience_data", "display_name": "Geoscience Data", "description": "Geoscience data and findings"},
    {"name": "metallurgical_data", "display_name": "Metallurgical Data", "description": "Metallurgical test data and results"},
    {"name": "technical_reports", "display_name": "Technical Reports", "description": "Technical reports and studies"},
]

COMMODITIES = ["All", "Gold", "Silver", "Copper", "Lithium", "Nickel", "Zinc", "Iron Ore", "Uranium", "Coal", "Platinum Group", "Rare Earths", "Other"]


def render_ai_training_page(current_user):
    """Render the AI Training management page for admins"""
    
    if not current_user.get('is_admin'):
        st.error("Access Denied: Administrator privileges required.")
        return
    
    st.title("AI Training Center")
    st.markdown("Upload mining documents to train the AI. The system automatically learns from your files to improve extraction accuracy for both Oreplot Light and Advanced.")
    
    tab1, tab2, tab3 = st.tabs([
        "Upload & Train",
        "Training Library",
        "Statistics"
    ])
    
    with tab1:
        render_upload_section(current_user)
    
    with tab2:
        render_library_section(current_user)
    
    with tab3:
        render_stats_section(current_user)


def render_upload_section(current_user):
    """Render the simplified document upload section"""
    
    st.markdown("### Upload Training Documents")
    st.markdown("Upload high-quality mining technical reports. The AI will automatically learn from these documents to improve its accuracy.")
    
    with st.container():
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: white;">How Training Works</h4>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                1. Upload your best mining reports (NI 43-101, feasibility studies, etc.)<br>
                2. The AI automatically processes and learns from them<br>
                3. When analyzing new documents, the AI uses your training data as reference<br>
                4. Better training data = more accurate extractions
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        category = st.selectbox(
            "Document Category",
            options=[c["name"] for c in TRAINING_CATEGORIES],
            format_func=lambda x: next((c["display_name"] for c in TRAINING_CATEGORIES if c["name"] == x), x),
            help="Select the primary type of data in this document"
        )
    
    with col2:
        commodity = st.selectbox(
            "Commodity Focus",
            options=COMMODITIES,
            help="Select the primary commodity covered in this document"
        )
    
    st.markdown("---")
    
    st.markdown("**Supported formats:** PDF, DOCX, XLSX, XLS, CSV, TIF, XML, PNG, JPG, JPEG | **Max files per upload:** 80 | **Max size per file:** 10 GB")
    
    uploaded_files = st.file_uploader(
        "Select training documents",
        type=["pdf", "docx", "xlsx", "xls", "csv", "tif", "xml", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
        help="Upload high-quality mining technical reports for AI training"
    )
    
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files)
        st.markdown(f"**Selected:** {len(uploaded_files)} file(s) ({total_size / (1024*1024):.1f} MB)")
        
        if len(uploaded_files) > 80:
            st.error("⚠️ Maximum 80 files per upload. Please select fewer files and try again.")
            uploaded_files = None
        else:
            with st.expander("View selected files", expanded=False):
                for f in uploaded_files:
                    st.markdown(f"- {f.name} ({f.size / (1024*1024):.1f} MB)")
    
    if st.button("Start Training", type="primary", disabled=not uploaded_files, use_container_width=True):
        if uploaded_files:
            total_files = len(uploaded_files)
            
            # HARD LIMIT - Prevent crash with 240+ files
            if total_files > MAX_FILES_PER_UPLOAD:
                st.error(f"❌ Maximum {MAX_FILES_PER_UPLOAD} files allowed per upload. You selected {total_files} files.")
                st.stop()
            
            progress_container = st.container()
            
            with progress_container:
                overall_progress = st.progress(0)
                status_text = st.empty()
                file_status = st.empty()
                
                successful = 0
                failed = 0
                
                # Process in batches to avoid timeouts
                for batch_num in range(0, total_files, BATCH_SIZE):
                    batch_end = min(batch_num + BATCH_SIZE, total_files)
                    batch_files = uploaded_files[batch_num:batch_end]
                    
                    status_text.markdown(f"**Processing batch {(batch_num // BATCH_SIZE) + 1}** (files {batch_num + 1}-{batch_end})")
                    
                    for i, uploaded_file in enumerate(batch_files):
                        file_index = batch_num + i
                        status_text.markdown(f"**Processing file {file_index+1} of {total_files}:** {uploaded_file.name}")
                        
                        try:
                            file_bytes = uploaded_file.read()
                            file_type = uploaded_file.name.split('.')[-1].lower()
                            
                            def update_progress(progress, message):
                                file_status.text(message)
                                file_progress = (file_index + progress) / total_files
                                overall_progress.progress(min(file_progress, 0.99))
                            
                            result = process_training_document(
                                file_bytes=file_bytes,
                                file_name=uploaded_file.name,
                                file_type=file_type,
                                category=category,
                                commodity=commodity if commodity != "All" else "general",
                                user_id=current_user['id'],
                                progress_callback=update_progress
                            )
                            
                            if result['success']:
                                successful += 1
                                file_status.success(f"✓ {result['chunks_created']} chunks from {uploaded_file.name}")
                            else:
                                failed += 1
                                file_status.error(f"✗ {uploaded_file.name}: {result.get('error', 'Unknown error')}")
                        except Exception as e:
                            failed += 1
                            file_status.error(f"✗ {uploaded_file.name}: {str(e)}")
                
                overall_progress.progress(1.0)
                status_text.empty()
                
                if successful > 0:
                    st.success(f"✓ Successfully trained on {successful} document(s)!")
                if failed > 0:
                    st.warning(f"⚠ {failed} document(s) failed to process.")
                
                st.info("The AI will now use these documents as reference when analyzing similar content.")
                st.rerun()


def render_library_section(current_user):
    """Render the training library showing all uploaded documents"""
    
    st.markdown("### Training Library")
    st.markdown("View and manage all documents used for AI training.")
    
    documents = get_training_documents()
    
    if not documents:
        st.info("No training documents uploaded yet. Go to the 'Upload & Train' tab to add documents.")
        return
    
    st.markdown(f"**Total Documents:** {len(documents)}")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Clear All Training Data", type="secondary"):
            st.session_state.confirm_delete_all = True
    
    if st.session_state.get('confirm_delete_all'):
        st.warning("Are you sure you want to delete ALL training data? This cannot be undone.")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("Yes, Delete All", type="primary"):
                if delete_all_training():
                    st.success("All training data deleted.")
                    st.session_state.confirm_delete_all = False
                    st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.confirm_delete_all = False
                st.rerun()
    
    st.markdown("---")
    
    for doc in documents:
        category_display = next((c["display_name"] for c in TRAINING_CATEGORIES if c["name"] == doc['category']), doc['category'])
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{doc['file_name']}**")
                st.caption(f"{category_display} | {doc['commodity']}")
            
            with col2:
                st.metric("Chunks", doc['chunks'])
            
            with col3:
                st.metric("Size", f"{doc['size_mb']} MB")
            
            with col4:
                if st.button("Delete", key=f"del_{doc['file_name']}", type="secondary"):
                    if delete_training_document(doc['file_name']):
                        st.success(f"Deleted {doc['file_name']}")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")
            
            st.markdown("---")


def render_stats_section(current_user):
    """Render training statistics"""
    
    st.markdown("### Training Statistics")
    st.markdown("Overview of your AI training data.")
    
    stats = get_training_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", stats['total_documents'])
    
    with col2:
        st.metric("Total Chunks", stats['total_chunks'])
    
    with col3:
        st.metric("Total Tokens", f"{stats['total_tokens']:,}")
    
    with col4:
        st.metric("Total Size", f"{stats['total_size_mb']} MB")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Categories")
        if stats['categories']:
            for cat, count in stats['categories'].items():
                cat_display = next((c["display_name"] for c in TRAINING_CATEGORIES if c["name"] == cat), cat)
                st.markdown(f"- **{cat_display}:** {count} chunks")
        else:
            st.info("No category data yet")
    
    with col2:
        st.markdown("#### Commodities")
        if stats['commodities']:
            for com, count in stats['commodities'].items():
                st.markdown(f"- **{com}:** {count} chunks")
        else:
            st.info("No commodity data yet")
    
    st.markdown("---")
    
    st.markdown("#### Activity")
    col1, col2 = st.columns(2)
    
    with col1:
        if stats['last_upload']:
            st.markdown(f"**Last Upload:** {stats['last_upload'][:10]}")
        else:
            st.markdown("**Last Upload:** Never")
    
    with col2:
        if stats['last_used']:
            st.markdown(f"**Last Used in Analysis:** {stats['last_used'][:10]}")
        else:
            st.markdown("**Last Used in Analysis:** Never")
    
    st.markdown("---")
    
    st.markdown("#### How Training Improves Accuracy")
    st.markdown("""
    When you analyze documents with Oreplot Light or Advanced:
    
    1. The AI searches your training data for similar content
    2. It retrieves the most relevant examples
    3. These examples guide the AI to extract data more accurately
    4. The more quality training data you add, the better the results
    
    **Tips for best results:**
    - Upload complete, high-quality NI 43-101 reports
    - Include documents with clear resource/reserve tables
    - Add documents for each commodity type you analyze
    - More diverse training data = better generalization
    """)
