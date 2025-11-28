import streamlit as st

def display_score_card(score, max_score):
    """Display a score card with progress bar"""
    percentage = (score / max_score) * 100 if max_score > 0 else 0
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.progress(percentage / 100)
    
    with col2:
        st.metric("Score", f"{score}/{max_score}")
    
    return percentage

def display_submission_card(submission):
    """Display a submission card"""
    st.markdown(f"""
    ### 📄 Submission Details
    - **Student ID:** {submission.get('student_id', 'N/A')}
    - **Rubric Set:** {submission.get('rubric_set_id', 'N/A')[:16]}...
    - **Attempt:** {submission.get('attempt_number', 1)}
    - **Score:** {submission.get('result', {}).get('total_score', 0)}
    - **Timestamp:** {submission.get('timestamp', 'N/A')}
    """)
