import streamlit as st
import sys
import os


# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# Now import from app.api
from app.api.frontend_api import verify_student_password, verify_teacher_password, get_student, get_teacher
from frontend.pages.utils.session_manager import init_session_state

st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

init_session_state()

# Hide sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
        button[kind="header"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🔐 Login")

# User type selection
user_type = st.radio("Select your role:", ["Student", "Teacher"], horizontal=True)

with st.form("login_form"):
    if user_type == "Student":
        user_id = st.text_input("Student ID", placeholder="e.g., S12345")
    else:
        user_id = st.text_input("Teacher ID", placeholder="e.g., t_john_doe_abc123")
    
    password = st.text_input("Password", type="password")
    
    submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
    
    if submitted:
        if not user_id or not password:
            st.error("⚠️ Please fill in all fields")
        else:
            with st.spinner("Authenticating..."):
                # Verify credentials
                if user_type == "Student":
                    if verify_student_password(user_id, password):
                        user_data = get_student(user_id)
                        st.session_state.logged_in = True
                        st.session_state.user_type = 'student'
                        st.session_state.user_id = user_id
                        st.session_state.user_name = user_data.get('name', user_id)
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.switch_page("pages/3_👨‍🎓_Student_Dashboard.py")
                    else:
                        st.error("❌ Invalid credentials")
                else:
                    if verify_teacher_password(user_id, password):
                        user_data = get_teacher(user_id)
                        st.session_state.logged_in = True
                        st.session_state.user_type = 'teacher'
                        st.session_state.user_id = user_id
                        st.session_state.user_name = user_data.get('name', user_id)
                        st.success("✅ Login successful!")
                        st.balloons()
                        st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
                    else:
                        st.error("❌ Invalid credentials")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("← Back to Home"):
        st.switch_page("EduLens.py")
with col2:
    if st.button("📝 Don't have an account? Register"):
        st.switch_page("pages/2_📝_Register.py")
