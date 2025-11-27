import os
from datetime import datetime, timezone, timedelta

# --- API and Model Configuration ---
# Your actual Gemini API key should be set via environment variable for production!
# For this example, we'll keep the placeholder from your base code.
GEMINI_API_KEY = "AIzaSyC9DEpz2yAS4dpfFNvy7JLj3DR0GqoqemQ" # Placeholder from base code


# Model names
RUBRIC_MODEL = "gemini-2.5-flash"   # Used for parsing rubrics (deterministic)
GRADE_MODEL  = "gemini-2.5-flash"   # Used for grading

# --- Database Configuration ---
# The MongoDB connection string
MONGO_URI = "mongodb+srv://supermarioking13:supermariox@testapp.qylpec3.mongodb.net/?appName=TestApp"
DATABASE_NAME = "grading_db"
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