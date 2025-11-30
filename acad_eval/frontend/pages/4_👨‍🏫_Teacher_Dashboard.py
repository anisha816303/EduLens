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
    
    /* Card styling */
    .element-container div[data-testid="stMarkdownContainer"] div[style*="background"] {
        border: 2px solid #c41e3a !important;
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
    <div style="background: linear-gradient(135deg, #c41e3a 0%, #d42e4a 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #2d3e50;">
        <h2 style="color: white; margin-bottom: 1rem;">📸 Bluebook Extraction</h2>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.05rem; line-height: 1.6;">
            Extract marks from bluebook images using AI-powered YOLO + Gemini detection
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    if st.button("📸 Go to Bluebook Extraction", use_container_width=True, type="primary", key="main_bluebook"):
        st.switch_page("pages/5_📸_Bluebook_Extraction.py")

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #c41e3a 0%, #d42e4a 100%); 
                padding: 2rem; border-radius: 15px; text-align: center; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid #2d3e50;">
        <h2 style="color: white; margin-bottom: 1rem;">📝 Report Evaluation</h2>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.05rem; line-height: 1.6;">
            Create rubrics and manage student report submissions and grading
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    if st.button("📝 Go to Report Evaluation", use_container_width=True, type="primary", key="main_report"):
        st.switch_page("pages/6_📝_Report_Evaluation.py")
