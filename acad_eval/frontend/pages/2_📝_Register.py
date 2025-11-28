import streamlit as st
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from app.api.frontend_api import register_student, register_teacher
from frontend.pages.utils.session_manager import init_session_state

st.set_page_config(page_title="Register", page_icon="📝", layout="centered")

init_session_state()

st.title("📝 Register New Account")

user_type = st.radio("Select your role:", ["Student", "Teacher"], horizontal=True)

# Registration form
with st.form("register_form"):
    name = st.text_input("Full Name", placeholder="John Doe")
    
    if user_type == "Student":
        user_id = st.text_input("Student ID", placeholder="e.g., S12345", 
                                help="Enter your university-assigned student ID")
    else:
        user_id = None  # Will be auto-generated for teachers
        st.info("ℹ️ Teacher ID will be auto-generated based on your name")
    
    password = st.text_input("Password", type="password", 
                            help="Minimum 6 characters")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    submitted = st.form_submit_button("Register", use_container_width=True, type="primary")

# Handle form submission OUTSIDE the form
if submitted:
    # Validation
    if not name or not password:
        st.error("⚠️ Please fill in all required fields")
    elif user_type == "Student" and not user_id:
        st.error("⚠️ Student ID is required")
    elif len(password) < 6:
        st.error("⚠️ Password must be at least 6 characters")
    elif password != confirm_password:
        st.error("⚠️ Passwords do not match")
    else:
        with st.spinner("Creating account..."):
            if user_type == "Student":
                success = register_student(user_id, name, password)
                if success:
                    st.success(f"✅ Student account created successfully!")
                    st.info(f"Your Student ID: **{user_id}**")
                    st.balloons()
                    
                    # Store registration success in session state
                    st.session_state.registration_success = True
                    st.session_state.registered_user_id = user_id
                    st.session_state.registered_user_type = "student"
                else:
                    st.error("❌ Registration failed. Student ID may already exist.")
            else:
                teacher_id = register_teacher(name, password)
                if teacher_id:
                    st.success(f"✅ Teacher account created successfully!")
                    st.info(f"Your Teacher ID: **{teacher_id}**")
                    st.warning("⚠️ Please save this ID - you'll need it to login!")
                    st.balloons()
                    
                    # Store registration success in session state
                    st.session_state.registration_success = True
                    st.session_state.registered_user_id = teacher_id
                    st.session_state.registered_user_type = "teacher"
                else:
                    st.error("❌ Registration failed. Please try again.")

# Show navigation buttons if registration was successful
if st.session_state.get('registration_success', False):
    st.markdown("---")
    st.markdown("### 🎉 Registration Complete!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Go to Login", use_container_width=True, type="primary"):
            # Clear registration success flag
            st.session_state.registration_success = False
            st.switch_page("pages/1_🔐_Login.py")
    with col2:
        if st.button("🏠 Go to Home", use_container_width=True):
            st.session_state.registration_success = False
            st.switch_page("EduLens.py")

# Show regular navigation at the bottom
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("← Back to Home", key="back_home"):
        st.switch_page("EduLens.py")
with col2:
    if st.button("🔑 Already have an account? Login", key="go_login"):
        st.switch_page("pages/1_🔐_Login.py")
