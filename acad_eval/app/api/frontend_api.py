"""
Frontend API - Bridge between Streamlit UI and backend logic
"""

from typing import Optional, List, Dict, Any
import os
import sys
import json
import hashlib
import secrets
import re
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import db_client
from app.core.config import GEMINI_API_KEY, RUBRIC_MODEL, GRADE_MODEL

# Import and initialize Gemini client
genai_available = False
try:
    import google.generativeai as genai
    
    # Ensure API key is set
    if not GEMINI_API_KEY or GEMINI_API_KEY == "":
        raise ValueError("GEMINI_API_KEY is not set")
    
    # Configure genai
    genai.configure(api_key=GEMINI_API_KEY)
    genai_available = True
    print("✅ Gemini API configured successfully")
    print(f"✅ Using models: {RUBRIC_MODEL}, {GRADE_MODEL}")
    
except ImportError as e:
    print(f"❌ Failed to import Gemini API: {e}")
    print("Please run: pip install google-generativeai")
except ValueError as e:
    print(f"❌ API Key error: {e}")
except Exception as e:
    print(f"❌ Failed to configure Gemini: {e}")

# ============================================
# HELPER FUNCTION TO CHECK CLIENT
# ============================================

def ensure_genai():
    """Ensure Gemini is configured"""
    if not genai_available:
        raise Exception("Gemini API not available. Please install google-generativeai")

# ============================================
# RUBRIC MANAGEMENT FUNCTIONS
# ============================================

def list_rubric_sets() -> List[Dict[str, Any]]:
    """Get all rubric sets from database"""
    if db_client is None:
        return []
    try:
        return list(db_client.rubric_sets_col.find({}, {'_id': 0}))
    except Exception as e:
        print(f"Error listing rubric sets: {e}")
        return []


def get_rubric_meta(rubric_set_id: str) -> Optional[Dict[str, Any]]:
    """Get metadata for a specific rubric set"""
    if db_client is None:
        return None
    return db_client.get_rubric_meta(rubric_set_id)


def compute_rubric_set_id(parsed_rubrics: List[Dict[str, Any]]) -> str:
    """Generate a unique ID for a rubric set"""
    rubric_str = json.dumps(parsed_rubrics, sort_keys=True)
    return hashlib.sha256(rubric_str.encode()).hexdigest()


def extract_rubrics_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Extract rubrics from PDF using Gemini AI"""
    ensure_genai()
    
    try:
        # Upload file to Gemini
        print(f"📤 Uploading file: {file_path}")
        file_obj = genai.upload_file(file_path)
        print(f"✅ File uploaded: {file_obj.name}")
        
        prompt = """
You are an academic evaluator. Read this rubric document carefully.

Extract ALL grading criteria and return them as a JSON array. Each criterion should have:
- "title": Brief name of the criterion
- "description": Detailed description of what is being evaluated
- "max_score": Maximum points (default 10)

Example format:
[
  {
    "title": "Code Quality",
    "description": "Assess code organization, naming conventions, and comments",
    "max_score": 10
  }
]

Return ONLY the JSON array, no additional text.
"""
        
        # Generate content
        print("🧠 Extracting rubrics with AI...")
        model = genai.GenerativeModel(RUBRIC_MODEL)
        response = model.generate_content(
            [file_obj, prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse response
        parsed = json.loads(response.text)
        print(f"✅ Extracted {len(parsed) if isinstance(parsed, list) else 0} rubric criteria")
        
        # Clean up uploaded file
        try:
            genai.delete_file(file_obj.name)
        except:
            pass
        
        return parsed if isinstance(parsed, list) else []
        
    except Exception as e:
        raise Exception(f"Failed to extract rubrics: {str(e)}")


def save_rubric_set(rubric_set_id: str, parsed_rubrics: List[Dict[str, Any]], 
                    deadline_iso: Optional[str], max_attempts: Optional[int],
                    teacher_id: Optional[str] = None) -> bool:
    """Save rubric set to database"""
    if db_client is None:
        return False
    
    try:
        # Convert deadline string to datetime if provided
        deadline_dt = None
        if deadline_iso:
            deadline_dt = datetime.fromisoformat(deadline_iso)
        
        db_client.upsert_rubric_set(rubric_set_id, parsed_rubrics, deadline_dt, max_attempts)
        
        # Attach teacher_id if provided
        if teacher_id:
            try:
                db_client.rubric_sets_col.update_one(
                    {"rubric_set_id": rubric_set_id},
                    {"$set": {"teacher_id": teacher_id}}
                )
            except:
                pass
        
        return True
    except Exception as e:
        print(f"Error saving rubric set: {e}")
        return False


def extract_and_save_rubric_from_pdf(pdf_path: str, teacher_id: Optional[str],
                                     deadline_iso: Optional[str], 
                                     max_attempts: Optional[int]) -> Dict[str, Any]:
    """Extract rubrics from PDF and save to database"""
    try:
        # Extract rubrics
        parsed_rubrics = extract_rubrics_from_file(pdf_path)
        
        if not parsed_rubrics:
            return {"error": "No rubrics extracted from PDF"}
        
        # Compute rubric set ID
        rubric_set_id = compute_rubric_set_id(parsed_rubrics)
        
        # Save to database
        success = save_rubric_set(rubric_set_id, parsed_rubrics, deadline_iso, 
                                  max_attempts, teacher_id)
        
        if not success:
            return {"error": "Failed to save rubric set to database"}
        
        return {
            "ok": True,
            "rubric_set_id": rubric_set_id,
            "parsed_rubrics": parsed_rubrics
        }
        
    except Exception as e:
        return {"error": str(e)}


# ============================================
# SUBMISSION MANAGEMENT FUNCTIONS
# ============================================

def list_submissions_for_student(student_id: str) -> List[Dict[str, Any]]:
    """Get all submissions for a specific student"""
    if db_client is None:
        return []
    try:
        return list(db_client.submissions_col.find(
            {"student_id": student_id},
            {'_id': 0}
        ).sort("timestamp", -1))
    except Exception as e:
        print(f"Error listing submissions: {e}")
        return []


def list_submissions_for_rubric(rubric_set_id: str) -> List[Dict[str, Any]]:
    """Get all submissions for a specific rubric"""
    if db_client is None:
        return []
    try:
        return list(db_client.submissions_col.find(
            {"rubric_set_id": rubric_set_id},
            {'_id': 0}
        ))
    except Exception as e:
        print(f"Error listing submissions: {e}")
        return []


def grade_student_submission(student_id: str, report_file_path: str, 
                            rubric_set_id: str) -> Dict[str, Any]:
    """Grade a student submission using AI"""
    ensure_genai()
    
    try:
        # Get rubric metadata
        rubric_meta = get_rubric_meta(rubric_set_id)
        if not rubric_meta:
            raise Exception("Rubric not found")
        
        parsed_rubrics = rubric_meta.get('parsed_rubrics')
        if not parsed_rubrics:
            raise Exception("No rubrics found in rubric set")
        
        # Get deadline and max attempts
        manual_deadline = None
        if rubric_meta.get('deadline'):
            try:
                manual_deadline = datetime.fromisoformat(rubric_meta['deadline'])
            except:
                pass
        
        manual_max_attempts = rubric_meta.get('max_attempts')
        
        # Check deadline
        from app.core.config import now_utc
        if manual_deadline and now_utc() > manual_deadline:
            raise Exception("Submission deadline has passed")
        
        # Check attempts
        record = db_client.get_submission_record(student_id, rubric_set_id)
        used_attempts = record.get('attempt_number', 0) if record else 0
        
        if manual_max_attempts and used_attempts >= manual_max_attempts:
            raise Exception(f"Maximum attempts ({manual_max_attempts}) reached")
        
        # Upload student report to Gemini
        print(f"📤 Uploading student report: {report_file_path}")
        student_file = genai.upload_file(report_file_path)
        print(f"✅ Student report uploaded: {student_file.name}")
        
        # Create grading prompt
        grading_prompt = f"""
You are a strict academic grader. Grade this student submission based on these rubrics:

{json.dumps(parsed_rubrics, indent=2)}

For each criterion, provide:
- "criterion": The criterion title
- "score": Score out of {parsed_rubrics[0].get('max_score', 10)}
- "feedback": Detailed feedback explaining the score

Return JSON in this exact format:
{{
  "evaluations": [
    {{
      "criterion": "criterion title",
      "score": numeric_score,
      "feedback": "detailed feedback"
    }}
  ],
  "total_score": sum_of_all_scores,
  "feedback": "overall summary of the submission"
}}

Return ONLY valid JSON, no markdown formatting.
"""
        
        # Generate grading
        print("🧠 Grading with AI...")
        model = genai.GenerativeModel(GRADE_MODEL)
        response = model.generate_content(
            [student_file, grading_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        parsed_result = json.loads(response.text)
        print("✅ Grading complete")
        
        # Clean up uploaded file
        try:
            genai.delete_file(student_file.name)
        except:
            pass
        
        # Save submission
        new_attempt_number = used_attempts + 1
        parsed_result["_timestamp"] = now_utc().isoformat()
        parsed_result["_attempt_number"] = new_attempt_number
        
        mongo_op = db_client.upsert_submission(
            student_id, rubric_set_id, report_file_path,
            parsed_rubrics, parsed_result, new_attempt_number
        )
        
        return {
            "result": parsed_result,
            "mongo_op": mongo_op,
            "meta": rubric_meta
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Grading failed: {str(e)}")


# ============================================
# USER MANAGEMENT FUNCTIONS
# ============================================

def get_student(student_id: str) -> Optional[Dict[str, Any]]:
    """Get student information"""
    if db_client is None:
        return None
    return db_client.get_student(student_id)


def get_teacher(teacher_id: str) -> Optional[Dict[str, Any]]:
    """Get teacher information"""
    if db_client is None:
        return None
    return db_client.get_teacher(teacher_id)


def verify_student_password(student_id: str, password: str) -> bool:
    """Verify student login credentials"""
    if db_client is None:
        return False
    return db_client.verify_student_password(student_id, password)


def verify_teacher_password(teacher_id: str, password: str) -> bool:
    """Verify teacher login credentials"""
    if db_client is None:
        return False
    return db_client.verify_teacher_password(teacher_id, password)


def register_student(student_id: str, name: Optional[str], password: str) -> bool:
    """Register a new student"""
    if db_client is None or not student_id or not password:
        return False
    return db_client.create_student(student_id.strip(), name.strip() if name else None, password)


def register_teacher(name: str, password: str) -> Optional[str]:
    """Register a new teacher with auto-generated ID"""
    if db_client is None or not name or not password:
        return None
    
    # Generate teacher ID from name
    base = re.sub(r'[^a-z0-9]+', '_', name.strip().lower())
    suffix = secrets.token_hex(2)
    teacher_id = f"t_{base[:20]}_{suffix}"
    
    success = db_client.create_teacher(teacher_id, name.strip(), password)
    return teacher_id if success else None


# ============================================
# BLUEBOOK EXTRACTION FUNCTION
# ============================================

def extract_bluebook(image_path: str) -> Dict[str, Any]:
    """Extract data from bluebook cover page image"""
    ensure_genai()
    
    try:
        # Upload image to Gemini
        print(f"📤 Uploading bluebook image: {image_path}")
        image_file = genai.upload_file(image_path)
        
        prompt = """
Analyze this bluebook cover page image and extract:
- student_name
- student_id
- course_name
- exam_name
- marks (if visible)
- date (if visible)

Return JSON format:
{
  "student_name": "...",
  "student_id": "...",
  "course_name": "...",
  "exam_name": "...",
  "marks": "...",
  "date": "..."
}

If any field is not visible, use null. Return ONLY valid JSON.
"""
        
        print("🧠 Extracting bluebook data...")
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            [image_file, prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        extracted_data = json.loads(response.text)
        print("✅ Bluebook extraction complete")
        
        # Clean up
        try:
            genai.delete_file(image_file.name)
        except:
            pass
        
        return extracted_data
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


# ============================================
# INITIALIZATION
# ============================================

print("✅ Frontend API module loaded successfully")
if not genai_available:
    print("⚠️  Warning: Gemini API is not configured. AI features may not work.")
    print("   Please check your GEMINI_API_KEY in app/core/config.py")
