import streamlit as st
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from frontend.pages.utils.session_manager import check_authentication

st.set_page_config(page_title="Teacher Dashboard", page_icon="👨‍🏫", layout="wide")

# Check authentication
check_authentication('teacher')

# Hide the default Streamlit page navigation sidebar
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

st.title("👨‍🏫 Teacher Dashboard")
st.markdown(f"**Welcome, {st.session_state.user_name}!**")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    
    st.markdown("### 📚 Features")

    if st.button("📸 Bluebook Marks Extraction", use_container_width=True, key="sidebar_bluebook"):
        st.switch_page("pages/5_📸_Bluebook_Extraction.py")
    if st.button("📝 Report Evaluation", use_container_width=True, key="sidebar_report"):
        st.switch_page("pages/6_📝_Report_Evaluation.py")
    
    st.markdown("---")
    
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("EduLens.py")

# Main content - Two main options
st.markdown("---")
st.markdown("### 🎯 What would you like to do?")
st.markdown("")

# Create two columns for the main options
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div style="
            padding: 2rem;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        ">
            <h2 style="color: white; margin: 0;">📸 Bluebook Marks</h2>
            <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">
                Extract marks from bluebook images using AI-powered YOLO + Gemini detection
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("📸 Open Bluebook Marks Extraction", use_container_width=True, type="primary", key="bluebook_btn"):
        st.switch_page("pages/5_📸_Bluebook_Extraction.py")

with col2:
    st.markdown("""
        <div style="
            padding: 2rem;
            border-radius: 10px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            text-align: center;
            margin-bottom: 1rem;
        ">
            <h2 style="color: white; margin: 0;">📝 Report Evaluation</h2>
            <p style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">
                Create rubrics and manage student report submissions and grading
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("📝 Open Report Evaluation", use_container_width=True, type="primary", key="report_btn"):
        st.switch_page("pages/6_📝_Report_Evaluation.py")

st.markdown("---")
st.info("💡 **Tip**: Choose an option above to get started. You can always return to this dashboard using the sidebar.")
