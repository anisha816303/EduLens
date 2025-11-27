import streamlit as st
import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from app.api.frontend_api import (
    list_rubric_sets,
    extract_and_save_rubric_from_pdf,
    list_submissions_for_rubric,
    extract_bluebook
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
        st.switch_page("app.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# Main tabs
tab1, tab2, tab3 = st.tabs(["📝 Create Rubric", "📊 View Rubrics & Submissions", "📸 Bluebook Extraction"])

# TAB 1: Create Rubric
with tab1:
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
                # Save uploaded file
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_rubric.getbuffer())
                    temp_path = tmp_file.name
                
                # Prepare deadline
                deadline_iso = None
                if deadline_date:
                    try:
                        deadline_dt = datetime.combine(deadline_date, deadline_time)
                        deadline_dt = deadline_dt.replace(tzinfo=get_ist_timezone())
                        deadline_iso = deadline_dt.isoformat()
                    except:
                        pass
                
                # Prepare max attempts
                final_max_attempts = None if unlimited else max_attempts
                
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
                            st.success("✅ Rubric created successfully!")
                            st.balloons()
                            
                            rubric_set_id = result['rubric_set_id']
                            parsed_rubrics = result['parsed_rubrics']
                            
                            st.markdown(f"### 🎯 Rubric Set ID: `{rubric_set_id}`")
                            st.warning("⚠️ Share this ID with your students so they can submit reports!")
                            
                            st.markdown("### 📋 Extracted Rubric Criteria:")
                            st.json(parsed_rubrics, expanded=True)
                        
                        # Cleanup
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        st.error(f"❌ Failed to create rubric: {str(e)}")
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)

# TAB 2: View Rubrics & Submissions
with tab2:
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
                st.markdown("**📋 Rubric Details:**")
                st.json(parsed_rubrics, expanded=False)
                
                st.markdown("---")
                st.markdown("**📊 Student Submissions:**")
                
                submissions = list_submissions_for_rubric(rubric_id)
                
                if not submissions:
                    st.info("📭 No submissions yet for this rubric.")
                else:
                    for sub in submissions:
                        student_id = sub.get('student_id', 'N/A')
                        attempt = sub.get('attempt_number', 1)
                        score = sub.get('result', {}).get('total_score', 0)
                        timestamp = sub.get('timestamp', 'N/A')
                        
                        st.markdown(f"- **Student:** {student_id} | **Attempt:** {attempt} | **Score:** {score} | **Date:** {timestamp}")

# TAB 3: Bluebook Extraction
with tab3:
    st.header("📸 Bluebook Marks Extraction")
    
    st.info("ℹ️ Upload an image of a bluebook cover page to extract student information and marks using AI.")
    
    uploaded_image = st.file_uploader(
        "Upload Bluebook Image",
        type=['jpg', 'jpeg', 'png'],
        help="Take a clear photo of the bluebook cover page"
    )
    
    if uploaded_image:
        # Display uploaded image
        st.image(uploaded_image, caption="Uploaded Bluebook Image", use_container_width=True)
        
        if st.button("🧠 Extract Data", use_container_width=True, type="primary"):
            # Save image temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_image.name)[1]) as tmp_file:
                tmp_file.write(uploaded_image.getbuffer())
                temp_img_path = tmp_file.name
            
            with st.spinner("🧠 AI is extracting data from bluebook... Please wait..."):
                try:
                    extracted_data = extract_bluebook(temp_img_path)
                    
                    if extracted_data.get('error'):
                        st.error(f"❌ Extraction failed: {extracted_data['error']}")
                    else:
                        st.success("✅ Data extracted successfully!")
                        st.balloons()
                        
                        st.markdown("### 📋 Extracted Information:")
                        st.json(extracted_data, expanded=True)
                    
                    # Cleanup
                    os.unlink(temp_img_path)
                    
                except Exception as e:
                    st.error(f"❌ Extraction error: {str(e)}")
                    if os.path.exists(temp_img_path):
                        os.unlink(temp_img_path)
