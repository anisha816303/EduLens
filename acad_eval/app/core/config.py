import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# --- Helper function to get secrets from env or Streamlit ---
def get_secret(key: str, default: str = None) -> str:
    """Get secret from environment variable or Streamlit secrets."""
    # First try environment variable
    value = os.getenv(key)
    if value:
        return value
    
    # Try Streamlit secrets (for cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    # Return default if provided
    if default is not None:
        return default
    
    raise ValueError(f"Secret '{key}' not found in environment or Streamlit secrets")

# --- API and Model Configuration ---
GEMINI_API_KEY = get_secret("GEMINI_API_KEY", "")

# Model names
RUBRIC_MODEL = "gemini-2.5-flash"   # Used for parsing rubrics (deterministic)
GRADE_MODEL  = "gemini-2.5-flash"   # Used for grading

# --- Database Configuration ---
MONGO_URI = get_secret("MONGO_URI", "")
DATABASE_NAME = get_secret("DATABASE_NAME", "grading_db")
SUBMISSIONS_COLLECTION = "submissions"
RUBRIC_SETS_COLLECTION = "rubric_sets"

# --- Utility Functions ---

def get_ist_timezone():
    """Returns the IST timezone object (UTC+5:30)."""
    return timezone(timedelta(hours=5, minutes=30))

def now_utc():
    """Returns the current UTC datetime."""
    return datetime.now(timezone.utc)

print("✅ Loaded core configuration.")