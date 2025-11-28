import streamlit as st
import sys
import os


# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from frontend.pages.utils.session_manager import init_session_state

# Page configuration
st.set_page_config(
    page_title="EduLens - Academic Evaluation",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# Load external CSS
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), 'styles', 'edulens.css')
    try:
        with open(css_file, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. Using default styling.")

load_css()

# Main app
def main():
    # Check if user is logged in
    if st.session_state.get('logged_in', False):
        user_type = st.session_state.get('user_type')
        user_id = st.session_state.get('user_id')
        
        # Welcome message for logged-in users
        col1, col2, col3 = st.columns([2, 3, 2])
        with col1:
            st.markdown("### 🎓 EduLens")
        with col2:
            st.success(f"✅ Welcome back, **{user_id}** ({user_type})!")
        with col3:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        
        st.markdown("---")
        
        # Dashboard button
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if user_type == 'student':
                if st.button("📊 Go to Student Dashboard", use_container_width=True, type="primary"):
                    st.switch_page("pages/3_👨‍🎓_Student_Dashboard.py")
            else:
                if st.button("📊 Go to Teacher Dashboard", use_container_width=True, type="primary"):
                    st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
    else:
        # Hero Section with embedded Login/Sign Up buttons
        st.markdown("""
            <div class="hero-section">
                <div class="logo-container">
                    <h1 class="logo-text">🎓 EduLens</h1>
                </div>
                <h2 class="hero-title">AI-Powered Academic Evaluation System</h2>
                <p class="hero-subtitle">Transforming Education Through Intelligent Assessment</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login/Sign Up buttons right after hero - better centered
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([2, 1, 0.5, 1, 2])
        
        with col2:
            if st.button("🔑 Login", key="hero_login", use_container_width=True):
                st.switch_page("pages/1_🔐_Login.py")
        
        with col4:
            if st.button("📝 Sign Up", key="hero_signup", use_container_width=True, type="primary"):
                st.switch_page("pages/2_📝_Register.py")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Not logged in - show features
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Feature cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <span class="feature-icon">👨‍🏫</span>
                <h3 class="feature-title">For Teachers</h3>
                <ul class="feature-list">
                    <li>✅ Upload rubrics in PDF format</li>
                    <li>✅ AI-powered rubric extraction</li>
                    <li>✅ Automated bluebook marks extraction</li>
                    <li>✅ Set deadlines & attempt limits</li>
                    <li>✅ Real-time submission tracking</li>
                    <li>✅ Comprehensive grading analytics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <span class="feature-icon">👨‍🎓</span>
                <h3 class="feature-title">For Students</h3>
                <ul class="feature-list">
                    <li>✅ Submit reports for instant grading</li>
                    <li>✅ Get detailed AI feedback</li>
                    <li>✅ Track submission attempts</li>
                    <li>✅ View rubric-based scores</li>
                    <li>✅ Download grading history</li>
                    <li>✅ Monitor academic progress</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Info section
        st.markdown("""
        <div class="info-section">
            <h3 class="info-title">🚀 Powered by Advanced AI Technology</h3>
            <p class="info-text">
                EduLens combines cutting-edge artificial intelligence with intuitive design to revolutionize 
                academic evaluation. Our platform uses YOLO for precise bluebook detection and Gemini AI for 
                intelligent assessment, providing instant, accurate feedback that helps both educators and 
                students achieve excellence.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Additional features showcase
        st.markdown("---")
        st.markdown("### ✨ Why Choose EduLens?")
        st.markdown("")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">⚡</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">Lightning Fast</div>
                    <div style="color: #64748b; font-size: 0.9rem;">Instant results in seconds</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">🎯</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">Precision Grading</div>
                    <div style="color: #64748b; font-size: 0.9rem;">99% accuracy guaranteed</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">🤖</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">AI-Powered</div>
                    <div style="color: #64748b; font-size: 0.9rem;">Advanced machine learning</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
                <div style="text-align: center; padding: 1.5rem;">
                    <div style="font-size: 3rem; margin-bottom: 0.5rem;">📊</div>
                    <div style="font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">Smart Analytics</div>
                    <div style="color: #64748b; font-size: 0.9rem;">Comprehensive insights</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

