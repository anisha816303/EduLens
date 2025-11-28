import streamlit as st
import sys
import os


# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from frontend.pages.utils.session_manager import init_session_state

# Page configuration
st.set_page_config(
    page_title="Academic Evaluation System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# Custom CSS - Hide sidebar and page navigation
st.markdown("""
<style>
    /* Hide the entire sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Hide page navigation */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-bottom: 3rem;
    }
    .feature-box {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main app
def main():
    st.markdown('<h1 class="main-header">📚 Academic Evaluation System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Grading & Rubric Management</p>', unsafe_allow_html=True)
    
    # Check if user is logged in
    if st.session_state.get('logged_in', False):
        user_type = st.session_state.get('user_type')
        user_id = st.session_state.get('user_id')
        
        st.success(f"✅ Welcome back, **{user_id}** ({user_type})!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if user_type == 'student':
                if st.button("📊 Go to Student Dashboard", use_container_width=True):
                    st.switch_page("pages/3_👨‍🎓_Student_Dashboard.py")
            else:
                if st.button("📊 Go to Teacher Dashboard", use_container_width=True):
                    st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    else:
        # Not logged in - show welcome screen
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### 🔐 Get Started")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🔑 Login", use_container_width=True, type="primary"):
                    st.switch_page("pages/1_🔐_Login.py")
            
            with col_b:
                if st.button("📝 Register", use_container_width=True):
                    st.switch_page("pages/2_📝_Register.py")
        
        st.markdown("---")
        
        # Features section
        st.markdown("### ✨ Key Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-box">
                <h4>👨‍🏫 For Teachers</h4>
                <ul>
                    <li>Upload rubrics in PDF format</li>
                    <li>Set deadlines & max attempts</li>
                    <li>AI-powered rubric extraction</li>
                    <li>Bluebook marks extraction</li>
                    <li>View all student submissions</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-box">
                <h4>👨‍🎓 For Students</h4>
                <ul>
                    <li>Submit reports for grading</li>
                    <li>Get instant AI feedback</li>
                    <li>Track submission attempts</li>
                    <li>View detailed rubric scores</li>
                    <li>Download grading history</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
