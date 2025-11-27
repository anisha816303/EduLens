import streamlit as st

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_type' not in st.session_state:
        st.session_state.user_type = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None

def check_authentication(required_role=None):
    """Check if user is authenticated and has the required role"""
    if not st.session_state.get('logged_in', False):
        st.error("🔒 Please login to access this page")
        if st.button("Go to Login"):
            st.switch_page("pages/1_🔐_Login.py")
        st.stop()
    
    if required_role and st.session_state.get('user_type') != required_role:
        st.error(f"⛔ Access denied. This page is for {required_role}s only.")
        st.stop()
