import streamlit as st
import sys
import os
import json
import pandas as pd
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from app.api.frontend_api import (
    extract_bluebook,
    save_bluebook_results,
    get_bluebook_history
)

from frontend.pages.utils.session_manager import check_authentication

st.set_page_config(page_title="Bluebook Extraction", page_icon="📸", layout="wide")

# Check authentication
check_authentication('teacher')

# MSRIT Color Scheme
st.markdown("""
<style>
    /* MSRIT Color Theme */
    .stApp {
        background-color: #f5f5f5;
    }
    
    /* Primary buttons - Red */
    .stButton > button[kind="primary"] {
        background-color: #c41e3a !important;
        color: white !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #a01830 !important;
    }
    
    /* Secondary buttons - Navy */
    .stButton > button[kind="secondary"] {
        background-color: #2d3e50 !important;
        color: white !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #1f2d3d !important;
    }
    
    /* Regular buttons - Navy */
    .stButton > button {
        background-color: #2d3e50 !important;
        color: white !important;
    }
    
    .stButton > button:hover {
        background-color: #1f2d3d !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #2d3e50 !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #2d3e50 !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #2d3e50;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #c41e3a !important;
    }
    
    /* Radio buttons */
    .stRadio > label {
        color: #2d3e50 !important;
        font-weight: 600 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #c41e3a !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background-color: #2d3e50 !important;
        color: white !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: #c41e3a !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📸 Bluebook Marks Extraction")
st.markdown(f"**Welcome, {st.session_state.user_name}!**")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    st.markdown("### 📚 Features")
    st.info("📸 **Bluebook Marks Extraction**\n\n*You are here*")
    if st.button("📝 Report Evaluation", use_container_width=True, key="sidebar_report"):
        st.switch_page("pages/6_📝_Report_Evaluation.py")
    
    st.markdown("---")
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("EduLens.py")

def compute_best_two_total(test_marks):
    """
    test_marks = {
        "Q1": {"a": 5, "b": 5, "c": 5},
        "Q2": {"a": 5, "b": 3, "c": 2},
        "Q3": {"a": 1, "b": 1, "c": 1}
    }
    Computes sum of parts per question, then takes the best 2 questions.
    Handles string/numeric inputs robustly.
    """
    if not test_marks:
        return 0

    totals = []
    for q, parts in test_marks.items():
        q_total = 0
        for v in parts.values():
            try:
                # Convert to float to handle strings like "5", "4.5"
                # If v is None or non-numeric string, it will be skipped
                if v is not None:
                    q_total += float(v)
            except (ValueError, TypeError):
                continue
        totals.append(q_total)

    # Pick the highest two question totals
    best_two = sorted(totals, reverse=True)[:2]
    return sum(best_two)


# Helper function for processing extraction and displaying results
def _process_and_display_extraction(temp_paths, source_name):
    """Common processing and display logic for extraction from uploaded or captured images."""
    with st.spinner(f"🔍 Processing {len(temp_paths)} images... YOLO detecting... Gemini extracting..."):
        try:
            extracted_data = extract_bluebook(temp_paths)
            
            if extracted_data.get('error'):
                st.error(f"❌ Extraction failed: {extracted_data['error']}")
            else:
                st.success(f"✅ Extracted data from {len(temp_paths)} images successfully!")
                st.balloons()
                
                # Save results
                save_bluebook_results(
                    st.session_state.user_id,
                    extracted_data,
                    source_name
                )
                
                # --- Display raw result ---
                st.markdown("### 📝 Extraction Results (Raw)")
                st.json(extracted_data, expanded=False)
                
                # Display summary
                total_bluebooks = extracted_data.get('total_bluebooks', 0)
                st.markdown(f"### 📊 Extraction Summary")
                st.metric("Total Bluebooks Detected", total_bluebooks)
                
                # Display detailed results
                bluebooks = extracted_data.get('bluebooks', [])
                
                if bluebooks:
                    st.markdown("### 📋 Extracted Bluebook Data")
                    
                    for idx, bluebook in enumerate(bluebooks, 1):
                        with st.expander(f"📘 Bluebook {idx}: USN {bluebook.get('usn', 'N/A')}", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**USN:** {bluebook.get('usn', 'N/A')}")
                                st.markdown(f"**Subject Code:** {bluebook.get('subject_code', 'N/A')}")
                            
                            with col2:
                                cie_marks = bluebook.get('cie_marks', {})
                                t1_marks = cie_marks.get('T1', {})
                                t2_marks = cie_marks.get('T2', {})
                                st.markdown("**CIE Marks Structure:**")
                                st.markdown(f"- T1: {len(t1_marks)} questions")
                                st.markdown(f"- T2: {len(t2_marks)} questions")
                            
                            st.markdown("---")
                            st.markdown("### 📊 Detailed Marks Grid")
                            
                            cie_marks = bluebook.get('cie_marks', {})
                            
                            # Create two columns for T1 and T2
                            t1_col, t2_col = st.columns(2)
                            
                            with t1_col:
                                st.markdown("#### 📝 Test 1 (T1)")
                                t1_data = cie_marks.get('T1', {})
                                if t1_data:
                                    rows = []
                                    for q_num, parts in t1_data.items():
                                        row = {"Question": q_num}
                                        for part in sorted(parts.keys()):
                                            val = parts[part]
                                            row[f"Part ({part})"] = val if val is not None else "-"
                                        rows.append(row)
                                    
                                    if rows:
                                        st.dataframe(pd.DataFrame(rows).set_index("Question"), use_container_width=True)
                                    else:
                                        st.info("No marks found for T1")
                                else:
                                    st.info("No T1 data available")
                            
                            with t2_col:
                                st.markdown("#### 📝 Test 2 (T2)")
                                t2_data = cie_marks.get('T2', {})
                                if t2_data:
                                    rows = []
                                    for q_num, parts in t2_data.items():
                                        row = {"Question": q_num}
                                        for part in sorted(parts.keys()):
                                            val = parts[part]
                                            row[f"Part ({part})"] = val if val is not None else "-"
                                        rows.append(row)
                                    
                                    if rows:
                                        st.dataframe(pd.DataFrame(rows).set_index("Question"), use_container_width=True)
                                    else:
                                        st.info("No marks found for T2")
                                else:
                                    st.info("No T2 data available")
                    
                    # Create downloadable CSV
                    st.markdown("---")
                    st.markdown("### 💾 Download Results")
                    
                    csv_data = []
                    for bluebook in bluebooks:
                        row = {
                            'USN': bluebook.get('usn', ''),
                            'Subject_Code': bluebook.get('subject_code', ''),
                        }
                        
                        cie_marks = bluebook.get('cie_marks', {})

                        # ------------------------------
                        # Add T1 and T2 question parts to CSV
                        # ------------------------------
                        for test in ['T1', 'T2']:
                            test_data = cie_marks.get(test, {})
                            for q_num in ['Q1', 'Q2', 'Q3']:
                                q_data = test_data.get(q_num, {})
                                for part in ['a', 'b', 'c', 'd']:
                                    col_name = f"{test}_{q_num}_{part}"
                                    row[col_name] = q_data.get(part, '')

                        # ------------------------------
                        # Compute TOTAL based on the rules
                        # ------------------------------
                        t1_total = compute_best_two_total(cie_marks.get("T1", {}))
                        t2_total = compute_best_two_total(cie_marks.get("T2", {}))

                        # Final TOTAL = T1 best two + T2 best two
                        row["T1_TOTAL"] = t1_total
                        row["T2_TOTAL"] = t2_total
                        row["TOTAL"] = t1_total + t2_total

                        csv_data.append(row)

                    
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"bluebook_marks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    json_str = json.dumps(extracted_data, indent=2)
                    st.download_button(
                        label="📥 Download as JSON",
                        data=json_str,
                        file_name=f"bluebook_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
            
            # Cleanup temp files
            for p in temp_paths:
                if os.path.exists(p):
                    os.unlink(p)
                    
        except Exception as e:
            st.error(f"❌ Extraction error: {str(e)}")
            import traceback
            with st.expander("🔍 View Error Details"):
                st.code(traceback.format_exc())
            
            # Cleanup on error
            for p in temp_paths:
                if os.path.exists(p):
                    os.unlink(p)

# Main content
st.info("ℹ️ Upload or capture images of bluebook answer sheets. Our AI system will detect and extract marks automatically using YOLO + Gemini.")

extraction_tab, history_tab = st.tabs(["🔍 Extract Marks", "📋 Extraction History"])

with extraction_tab:
    # Use radio buttons instead of nested tabs for cleaner UI
    st.markdown("### 📤 Choose Upload Method")
    upload_method = st.radio(
        "How would you like to provide bluebook images?",
        ["📁 Upload from Files", "📷 Capture with Camera"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # --- METHOD 1: File Upload ---
    if upload_method == "📁 Upload from Files":
        uploaded_images = st.file_uploader(
            "Upload Bluebook Image(s)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload one or more clear images of bluebook answer sheets",
            key="bluebook_uploader",
            accept_multiple_files=True
        )
        
        if uploaded_images:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(uploaded_images[0], caption=f"First Image: {uploaded_images[0].name}", use_container_width=True)
                if len(uploaded_images) > 1:
                    st.caption(f"...and {len(uploaded_images)-1} more image(s)")
            
            with col2:
                st.markdown("### 📋 Upload Info")
                st.markdown(f"**Files:** {len(uploaded_images)}")
                total_size = sum(f.size for f in uploaded_images)
                st.markdown(f"**Total Size:** {total_size / 1024:.2f} KB")
            
            if st.button("🧠 Extract Bluebook Data", use_container_width=True, type="primary", key="extract_upload_btn"):
                import tempfile
                temp_paths = []
                
                # Save all uploaded files to temp
                for uploaded_file in uploaded_images:
                    suffix = os.path.splitext(uploaded_file.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        temp_paths.append(tmp_file.name)
                
                _process_and_display_extraction(temp_paths, f"{uploaded_images[0].name} (+{len(uploaded_images)-1} others)" if len(uploaded_images) > 1 else uploaded_images[0].name)
    
    # --- METHOD 2: Camera Capture ---
    else:  # Camera Capture method
        st.info("💡 Take photos of bluebooks one at a time using your device camera. Click 'Add to Batch' after each photo.")
        
        # Initialize session state for captured images
        if 'captured_images' not in st.session_state:
            st.session_state.captured_images = []
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            camera_photo = st.camera_input("📸 Capture Bluebook Photo", key="camera_input")
        
        with col2:
            st.markdown("### 📊 Capture Stats")
            st.metric("Photos Captured", len(st.session_state.captured_images))
            
            if camera_photo is not None:
                if st.button("➕ Add to Batch", use_container_width=True, type="secondary"):
                    st.session_state.captured_images.append(camera_photo.getvalue())
                    st.success("✅ Photo added to batch!")
                    st.rerun()
            
            if len(st.session_state.captured_images) > 0:
                if st.button("🗑️ Clear All", use_container_width=True):
                    st.session_state.captured_images = []
                    st.rerun()
        
        # Display captured images
        if len(st.session_state.captured_images) > 0:
            st.markdown("---")
            st.markdown(f"### 📸 Captured Images ({len(st.session_state.captured_images)})")
            
            # Show thumbnails in a grid
            cols = st.columns(min(4, len(st.session_state.captured_images)))
            for idx, img_bytes in enumerate(st.session_state.captured_images):
                with cols[idx % 4]:
                    st.image(img_bytes, caption=f"Photo {idx+1}", use_container_width=True)
            
            st.markdown("---")
            if st.button("🧠 Extract from All Captured Photos", use_container_width=True, type="primary", key="extract_camera_btn"):
                import tempfile
                temp_paths = []
                
                # Save all captured images to temp files
                for idx, img_bytes in enumerate(st.session_state.captured_images):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(img_bytes)
                        temp_paths.append(tmp_file.name)
                
                _process_and_display_extraction(temp_paths, f"Camera Capture ({len(temp_paths)} photos)")
                
                # Clear captured images after processing
                st.session_state.captured_images = []

with history_tab:
    st.markdown("### 📋 Previous Extractions")
    
    history = get_bluebook_history(st.session_state.user_id)
    
    if not history:
        st.info("📭 No extraction history yet. Extract your first bluebook to see results here!")
    else:
        for idx, record in enumerate(history, 1):
            with st.expander(
                f"📸 {record.get('image_filename', 'Unknown')} | "
                f"{record.get('total_bluebooks', 0)} bluebook(s) | "
                f"{record.get('extraction_date', 'N/A')[:10]}"
            ):
                st.markdown(f"**Extraction Date:** {record.get('extraction_date', 'N/A')}")
                st.markdown(f"**Total Bluebooks:** {record.get('total_bluebooks', 0)}")
                st.markdown(f"**Image:** {record.get('image_filename', 'N/A')}")
                st.markdown("---")
                st.markdown("**📊 Extracted Data:**")
                st.json(record.get('bluebooks', []), expanded=False)
