import streamlit as st
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from app.api.frontend_api import verify_student_password, verify_teacher_password, get_student, get_teacher
from frontend.pages.utils.session_manager import init_session_state

# Page configuration
st.set_page_config(
    page_title="EduLens - Login",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# Check if already logged in
if st.session_state.get('logged_in', False):
    user_type = st.session_state.get('user_type')
    if user_type == 'student':
        st.switch_page("pages/3_👨‍🎓_Student_Dashboard.py")
    else:
        st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")

# Enhanced CSS with animations and better styling
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu, header, footer {visibility: hidden !important;}
    
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Split background with subtle gradient */
    .stApp {
        background: linear-gradient(to right, 
            #2d3e50 0%, #2d3e50 50%, 
            #c41e3a 50%, #c41e3a 100%) !important;
    }
    
    [data-testid="column"] {
        background: transparent !important;
    }
    
    [data-testid="column"]:first-child {
        padding: 3rem !important;
        min-height: 100vh !important;
    }
    
    [data-testid="column"]:last-child {
        padding: 4rem 3rem !important;
        min-height: 100vh !important;
    }
    
    /* Force white text on right column */
    [data-testid="column"]:last-child * {
        color: white !important;
    }
    
    [data-testid="column"]:last-child label {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.3px !important;
    }
    
    /* Enhanced input fields */
    input {
        background-color: white !important;
        color: #2d3e50 !important;
        border: 2px solid rgba(255,255,255,0.4) !important;
        padding: 0.85rem !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        border-radius: 8px !important;
    }
    
    input:focus {
        border-color: white !important;
        box-shadow: 0 0 0 3px rgba(255,255,255,0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    input::placeholder {
        color: rgba(45,62,80,0.5) !important;
    }
    
    /* Enhanced button with animation */
    .stButton > button {
        background-color: white !important;
        color: #c41e3a !important;
        font-weight: 700 !important;
        width: 100% !important;
        border: none !important;
        padding: 1rem !important;
        font-size: 1.1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }
    
    .stButton > button:hover {
        background-color: #f8f9fa !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Radio button styling */
    .stRadio > div {
        gap: 2rem !important;
    }
    
    /* Feature card animation */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .feature-card {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Smooth transitions */
    * {
        transition: color 0.2s ease, background-color 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# Create two columns
col1, col2 = st.columns([1, 1], gap="small")

# LEFT COLUMN
with col1:
    # Header with logo - enhanced
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 3rem; border-bottom: 3px solid rgba(255,255,255,0.3); padding-bottom: 2rem;">
        <span style="font-size: 4.5rem; margin-right: 1.5rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">🎓</span>
        <div>
            <h1 style="margin: 0; font-size: 2.5rem; font-weight: 800; color: white; letter-spacing: -0.5px;">EduLens</h1>
            <p style="margin: 0; font-size: 1.15rem; color: rgba(255,255,255,0.9); font-weight: 500; letter-spacing: 0.3px;">Ramaiah Institute of Technology</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Welcome heading - enhanced
    st.markdown('<h2 style="color: white; font-size: 2.2rem; margin-bottom: 1.5rem; font-weight: 700; letter-spacing: -0.3px;">Welcome to EduLens</h2>', unsafe_allow_html=True)
    
    # Paragraph 1 - enhanced typography
    st.markdown("""
    <p style="color: rgba(255,255,255,0.95); font-size: 1.08rem; line-height: 1.8; margin-bottom: 1.5rem; letter-spacing: 0.2px;">
        <strong style="color: white; font-weight: 700;">EduLens</strong> is an AI-Powered Academic Evaluation System designed to transform education through 
        intelligent assessment. Our platform combines cutting-edge artificial intelligence with intuitive design.
    </p>
    """, unsafe_allow_html=True)
    
    # Paragraph 2 - with tech highlights
    st.markdown("""
    <p style="color: rgba(255,255,255,0.95); font-size: 1.08rem; line-height: 1.8; margin-bottom: 1.5rem; letter-spacing: 0.2px;">
        EduLens uses <strong style="color: #4fc3f7; font-weight: 700;">YOLO</strong> for precise bluebook detection and <strong style="color: #81c784; font-weight: 700;">Gemini AI</strong> for intelligent 
        assessment, providing instant, accurate feedback that helps both educators and students achieve excellence.
    </p>
    """, unsafe_allow_html=True)
    
    # Info box - enhanced with better styling
    st.markdown("""
    <div style="color: rgba(255,255,255,0.95); font-size: 1rem; line-height: 1.8; margin-bottom: 2.5rem; font-style: italic; 
                padding: 1.25rem 1.5rem; background: linear-gradient(135deg, rgba(255,255,255,0.12), rgba(255,255,255,0.08)); 
                border-radius: 10px; border-left: 4px solid #c41e3a; backdrop-filter: blur(10px);
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <strong style="color: white; font-weight: 600;">🔒 Secure Portal:</strong> This portal is for the exclusive use of RIT students and faculty to streamline academic evaluation processes.
    </div>
    """, unsafe_allow_html=True)
    
    # For Teachers Card - enhanced
    st.markdown("""
    <div class="feature-card" style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                padding: 2.25rem; border-radius: 16px; margin-bottom: 1.5rem; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.15); 
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;">
        <h3 style="color: #c41e3a; margin: 0 0 1.25rem 0; font-size: 1.4rem; font-weight: 800; 
                   border-bottom: 3px solid #c41e3a; padding-bottom: 0.75rem; letter-spacing: 0.3px;">
            👨‍🏫 For Teachers
        </h3>
        <ul style="color: #2d3e50; list-style: none; padding: 0; margin: 0;">
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Upload rubrics in PDF format
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> AI-powered rubric extraction
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Automated bluebook marks extraction
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Set deadlines & attempt limits
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Real-time submission tracking
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # For Students Card - enhanced
    st.markdown("""
    <div class="feature-card" style="background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%); 
                padding: 2.25rem; border-radius: 16px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;">
        <h3 style="color: #c41e3a; margin: 0 0 1.25rem 0; font-size: 1.4rem; font-weight: 800; 
                   border-bottom: 3px solid #c41e3a; padding-bottom: 0.75rem; letter-spacing: 0.3px;">
            👨‍🎓 For Students
        </h3>
        <ul style="color: #2d3e50; list-style: none; padding: 0; margin: 0;">
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Submit reports for instant grading
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Get detailed AI feedback
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Track submission attempts
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> View rubric-based scores
            </li>
            <li style="color: #2d3e50; font-size: 1.05rem; line-height: 2.2; padding-left: 0.5rem;">
                <span style="color: #4caf50; font-weight: 700;">✓</span> Monitor academic progress
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# RIGHT COLUMN
with col2:
    st.markdown('<h2 style="color: white !important; font-size: 2.5rem; font-weight: 800; margin-bottom: 2.5rem; text-align: center; letter-spacing: -0.5px;">Login to Your Account</h2>', unsafe_allow_html=True)
    
    user_type = st.radio("Select your role", ["Student", "Teacher"], horizontal=True)
    
    with st.form("login_form"):
        if user_type == "Student":
            user_id = st.text_input("Student ID", placeholder="e.g., 1MS22CS001")
        else:
            user_id = st.text_input("Teacher ID", placeholder="e.g., t_john_doe")
        
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("LOGIN")
        
        if submitted:
            if not user_id or not password:
                st.error("⚠️ Please fill in all fields")
            else:
                with st.spinner("🔐 Authenticating..."):
                    success = False
                    user_data = None
                    
                    if user_type == "Student":
                        if verify_student_password(user_id, password):
                            user_data = get_student(user_id)
                            success = True
                    else:
                        if verify_teacher_password(user_id, password):
                            user_data = get_teacher(user_id)
                            success = True
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_type = user_type.lower()
                        st.session_state.user_id = user_id
                        st.session_state.user_name = user_data.get('name', user_id) if user_data else user_id
                        
                        st.success("✅ Login successful!")
                        st.balloons()
                        
                        if user_type == "Student":
                            st.switch_page("pages/3_👨‍🎓_Student_Dashboard.py")
                        else:
                            st.switch_page("pages/4_👨‍🏫_Teacher_Dashboard.py")
                    else:
                        st.error("❌ Invalid credentials")
