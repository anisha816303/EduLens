import streamlit as st
import sys
import os
import json
from datetime import datetime

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from app.api.frontend_api import (
    list_submissions_for_student, 
    get_rubric_meta,
    grade_student_submission
)
from app.core.config import get_ist_timezone, now_utc
from app.core.database import db_client
from frontend.pages.utils.session_manager import check_authentication

st.set_page_config(page_title="Student Dashboard", page_icon="👨‍🎓", layout="wide")

# Check authentication
check_authentication('student')

st.title("👨‍🎓 Student Dashboard")
st.markdown(f"**Welcome, {st.session_state.user_name}!**")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

# Main content tabs
tab1, tab2 = st.tabs(["📤 Submit Report", "📊 My Submissions"])

# TAB 1: Submit Report
with tab1:
    st.header("📤 Submit New Report")
    
    rubric_set_id = st.text_input(
        "Rubric Set ID",
        placeholder="Enter the Rubric Set ID provided by your teacher",
        help="Your teacher should have shared this ID with you"
    )
    
    if rubric_set_id:
        # Fetch rubric metadata
        rubric_meta = get_rubric_meta(rubric_set_id)
        
        if rubric_meta:
            st.success("✅ Rubric found!")
            
            # Display rubric info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                deadline = rubric_meta.get('deadline')
                if deadline:
                    try:
                        from datetime import timezone
                        deadline_dt = datetime.fromisoformat(deadline)
                        if deadline_dt.tzinfo is None:
                            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
                        deadline_ist = deadline_dt.astimezone(get_ist_timezone())
                        st.info(f"⏰ **Deadline:** {deadline_ist.strftime('%Y-%m-%d %H:%M IST')}")
                    except:
                        st.info("⏰ **Deadline:** Not set")
                else:
                    st.info("⏰ **Deadline:** No deadline")
            
            with col2:
                max_attempts = rubric_meta.get('max_attempts')
                st.info(f"🔁 **Max Attempts:** {max_attempts if max_attempts else 'Unlimited'}")
            
            with col3:
                # Get current attempts
                record = db_client.get_submission_record(st.session_state.user_id, rubric_set_id)
                used_attempts = record.get('attempt_number', 0) if record else 0
                st.info(f"📝 **Used Attempts:** {used_attempts}")
            
            # Check if submission is allowed
            can_submit = True
            error_msg = ""
            
            # Check deadline
            if deadline:
                try:
                    from datetime import timezone
                    deadline_dt = datetime.fromisoformat(deadline)
                    if deadline_dt.tzinfo is None:
                        deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
                    if now_utc() > deadline_dt:
                        can_submit = False
                        error_msg = "⛔ Submission deadline has passed!"
                except:
                    pass
            
            # Check attempts
            if max_attempts and used_attempts >= max_attempts:
                can_submit = False
                error_msg = f"⛔ Maximum attempts ({max_attempts}) reached!"
            
            if not can_submit:
                st.error(error_msg)
            else:
                # File upload
                st.markdown("---")
                uploaded_file = st.file_uploader(
                    "Upload your report (PDF only)",
                    type=['pdf'],
                    help="Select the PDF file of your project report"
                )
                
                if uploaded_file:
                    # Save uploaded file temporarily
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getbuffer())
                        temp_path = tmp_file.name
                    
                    st.success(f"✅ File uploaded: {uploaded_file.name}")
                    
                    if st.button("🚀 Submit for Grading", type="primary", use_container_width=True):
                        with st.spinner("🧠 AI is grading your submission... This may take a minute..."):
                            try:
                                result = grade_student_submission(
                                    st.session_state.user_id,
                                    temp_path,
                                    rubric_set_id
                                )
                                
                                st.success("✅ Grading Complete!")
                                st.balloons()
                                
                                parsed_result = result['result']
                                
                                # Display score
                                total_score = parsed_result.get('total_score', 0)
                                parsed_rubrics = rubric_meta.get('parsed_rubrics', [])
                                max_score = len(parsed_rubrics) * 10
                                
                                st.markdown(f"### 🎯 Your Score: **{total_score} / {max_score}**")
                                
                                # Display detailed feedback
                                st.markdown("### 📝 Detailed Feedback")
                                
                                evaluations = parsed_result.get('evaluations', [])
                                for i, eval_item in enumerate(evaluations, 1):
                                    with st.expander(f"Criterion {i}: {eval_item.get('criterion', 'N/A')}", expanded=True):
                                        st.markdown(f"**Score:** {eval_item.get('score', 0)} / 10")
                                        st.markdown(f"**Feedback:** {eval_item.get('feedback', 'No feedback')}")
                                
                                # Overall feedback
                                if parsed_result.get('feedback'):
                                    st.markdown("### 💬 Overall Feedback")
                                    st.info(parsed_result.get('feedback'))
                                
                                # Cleanup
                                os.unlink(temp_path)
                                
                            except Exception as e:
                                st.error(f"❌ Grading failed: {str(e)}")
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)
        else:
            st.error("❌ Invalid Rubric Set ID. Please check with your teacher.")

# TAB 2: My Submissions
with tab2:
    st.header("📊 My Submission History")
    
    submissions = list_submissions_for_student(st.session_state.user_id)
    
    if not submissions:
        st.info("📭 No submissions yet. Submit your first report to get started!")
    else:
        for submission in submissions:
            with st.expander(
                f"🗂️ Rubric: {submission.get('rubric_set_id', 'N/A')[:16]}... | "
                f"Attempt: {submission.get('attempt_number', 1)} | "
                f"Score: {submission.get('result', {}).get('total_score', 0)}"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**📅 Submitted:** {submission.get('timestamp', 'N/A')}")
                    st.markdown(f"**📁 File:** {submission.get('filename', 'N/A')}")
                
                with col2:
                    result = submission.get('result', {})
                    total_score = result.get('total_score', 0)
                    rubrics = submission.get('rubrics', [])
                    max_score = len(rubrics) * 10
                    st.markdown(f"**🎯 Score:** {total_score} / {max_score}")
                    st.markdown(f"**🔢 Attempt:** {submission.get('attempt_number', 1)}")
                
                st.markdown("---")
                st.markdown("**📝 Detailed Results:**")
                st.json(result, expanded=False)
