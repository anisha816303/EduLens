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
    list_rubric_sets,
    extract_and_save_rubric_from_pdf,
    list_submissions_for_rubric,
    extract_bluebook,
    save_bluebook_results,
    get_bluebook_history
)
from app.core.config import get_ist_timezone
from frontend.pages.utils.session_manager import check_authentication

st.set_page_config(page_title="Teacher Dashboard", page_icon="👨‍🏫", layout="wide")

# Check authentication
check_authentication('teacher')

st.title("👨‍🏫 Teacher Dashboard")
st.markdown(f"**Welcome, {st.session_state.user_name}!**")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("EduLens.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("EduLens.py")

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
                        for test in ['T1', 'T2']:
                            test_data = cie_marks.get(test, {})
                            for q_num in ['Q1', 'Q2', 'Q3']:
                                q_data = test_data.get(q_num, {})
                                for part in ['a', 'b', 'c', 'd']:
                                    col_name = f"{test}_{q_num}_{part}"
                                    row[col_name] = q_data.get(part, '')
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

# Main tabs
tab1, tab2, tab3 = st.tabs(["📸 Bluebook Extraction", "📝 Create Rubric", "📊 View Rubrics & Submissions"])

# TAB 1: Bluebook Extraction (UPDATED)
with tab1:
    st.header("📸 Bluebook Marks Extraction")
    
    st.info("ℹ️ Upload an image of bluebook answer sheets. Our AI system will detect and extract marks automatically using YOLO + Gemini.")
    
    extraction_tab, history_tab = st.tabs(["🔍 Extract Marks", "📋 Extraction History"])
    
    with extraction_tab:
        # Create sub-tabs for Upload vs Camera Capture
        upload_method, camera_method = st.tabs(["📁 Upload Images", "📷 Capture Photos"])
        
        # --- METHOD 1: File Upload ---
        with upload_method:
            st.markdown("### 📁 Upload Bluebook Images")
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
        with camera_method:
            st.markdown("### 📷 Capture Bluebook Photos")
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

# TAB 2: Create Rubric
with tab2:
    st.header("📝 Create New Rubric Set")
    
    st.info("ℹ️ Upload a PDF containing your grading rubric. AI will extract the criteria automatically.")
    
    with st.form("rubric_upload_form"):
        uploaded_rubric = st.file_uploader(
            "Upload Rubric PDF",
            type=['pdf'],
            help="Select a PDF file containing your rubric"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            deadline_date = st.date_input("Submission Deadline (Optional)")
            deadline_time = st.time_input("Deadline Time (IST)")
        
        with col2:
            max_attempts = st.number_input(
                "Max Attempts per Student",
                min_value=1,
                max_value=10,
                value=3,
                help="Leave blank for unlimited"
            )
            unlimited = st.checkbox("Unlimited Attempts")
        
        submitted = st.form_submit_button("🚀 Create Rubric Set", use_container_width=True, type="primary")
        
        if submitted:
            if not uploaded_rubric:
                st.error("⚠️ Please upload a rubric PDF file")
            else:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_rubric.getbuffer())
                    temp_path = tmp_file.name
                
                deadline_iso = None
                deadline_display_str = "None (Unlimited)"
                if deadline_date:
                    try:
                        deadline_dt = datetime.combine(deadline_date, deadline_time)
                        deadline_dt = deadline_dt.replace(tzinfo=get_ist_timezone())
                        deadline_iso = deadline_dt.isoformat()
                        deadline_display_str = deadline_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
                    except:
                        pass
                
                final_max_attempts = None if unlimited else max_attempts
                attempts_str = "Unlimited" if unlimited else str(max_attempts)
                
                with st.spinner("🧠 AI is extracting rubric criteria... Please wait..."):
                    try:
                        result = extract_and_save_rubric_from_pdf(
                            temp_path,
                            st.session_state.user_id,
                            deadline_iso,
                            final_max_attempts
                        )
                        
                        if result.get('error'):
                            st.error(f"❌ Error: {result['error']}")
                        else:
                            st.success("✅ Rubric setup complete.")
                            st.balloons()
                            
                            rubric_set_id = result['rubric_set_id']
                            parsed_rubrics = result['parsed_rubrics']
                            
                            # --- LOGIC PARITY: Display exact same confirmation info as main.py ---
                            st.markdown("### 📝 Rubric Setup Summary")
                            st.info(f"""
                            **Rubric Set ID:** `{rubric_set_id}`
                            
                            **Deadline (IST):** {deadline_display_str}
                            
                            **Max Attempts:** {attempts_str}
                            
                            **Parsed Criteria:** {len(parsed_rubrics)} criteria
                            """)
                            st.warning("📌 Share this Rubric Set ID with students so they can submit against it.")
                            
                            st.markdown("### 🧠 Extracted Logic (Raw JSON):")
                            st.json(parsed_rubrics, expanded=True)
                        
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create rubric: {str(e)}")
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

# TAB 3: View Rubrics & Submissions
with tab3:
    st.header("📊 All Rubric Sets & Submissions")
    
    rubrics = list_rubric_sets()
    
    if not rubrics:
        st.info("📭 No rubrics created yet. Create your first rubric in the 'Create Rubric' tab!")
    else:
        for rubric in rubrics:
            rubric_id = rubric.get('rubric_set_id', 'N/A')
            
            with st.expander(f"📋 Rubric ID: {rubric_id[:20]}...", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    deadline = rubric.get('deadline', 'None')
                    if deadline and deadline != 'None':
                        try:
                            dt = datetime.fromisoformat(deadline)
                            st.markdown(f"**⏰ Deadline:** {dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.markdown(f"**⏰ Deadline:** {deadline}")
                    else:
                        st.markdown("**⏰ Deadline:** No deadline")
                
                with col2:
                    max_att = rubric.get('max_attempts')
                    st.markdown(f"**🔁 Max Attempts:** {max_att if max_att else 'Unlimited'}")
                
                with col3:
                    parsed_rubrics = rubric.get('parsed_rubrics', [])
                    st.markdown(f"**📝 Criteria Count:** {len(parsed_rubrics)}")
                
                st.markdown("---")
                st.markdown("### 📋 Rubric Criteria")
                
                if parsed_rubrics:
                    for i, criterion in enumerate(parsed_rubrics, 1):
                        title = criterion.get('title', 'Untitled')
                        desc = criterion.get('description', 'No description')
                        score = criterion.get('max_score', 10)
                        
                        with st.container():
                            st.markdown(f"**{i}. {title}** (Max Score: {score})")
                            st.caption(desc)
                else:
                    st.warning("⚠️ No criteria found for this rubric.")
                
                st.markdown("---")
                st.markdown("### 📊 Student Submissions")
                
                submissions = list_submissions_for_rubric(rubric_id)
                
                if not submissions:
                    st.info("📭 No submissions yet for this rubric.")
                else:
                    sub_data = []
                    for sub in submissions:
                        sub_data.append({
                            "Student ID": sub.get('student_id', 'N/A'),
                            "Attempt": sub.get('attempt_number', 1),
                            "Score": sub.get('result', {}).get('total_score', 0),
                            "Date": sub.get('timestamp', 'N/A')[:16].replace('T', ' ')
                        })
                    
                    st.dataframe(pd.DataFrame(sub_data), use_container_width=True)

