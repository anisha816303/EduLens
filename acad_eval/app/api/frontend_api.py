"""
Frontend API - Thin bridge between Streamlit UI and Backend Logic.
Directly imports and uses core logic from ai_models and app.core.
"""

from typing import Optional, List, Dict, Any, Union
import os
import certifi

# 💉 FIX: Point to valid SSL certificates to prevent [Errno 2] in pipeline.py
os.environ["SSL_CERT_FILE"] = certifi.where()
import sys
import json
import secrets
import re
from datetime import datetime, timezone

# Add parent directory to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# --- Core Imports ---
from app.core.database import db_client
from app.core.config import GEMINI_API_KEY, RUBRIC_MODEL, GRADE_MODEL, now_utc

# --- AI Logic Imports (Reuse existing modules) ---
try:
    from ai_models.llm_evaluation.evaluator import (
        extract_rubrics_from_file, 
        compute_rubric_set_id, 
        grade_submission,
        validate_rubrics_with_llm
    )
except ImportError as e:
    print(f"❌ Error importing evaluator: {e}")

try:
    from ai_models.llm_evaluation.bluebook_extractor import extract_bluebook_data
except ImportError as e:
    print(f"❌ Error importing bluebook_extractor: {e}")

# --- Google GenAI Setup (Only for file upload helpers if needed) ---
import google.generativeai as genai

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


# ============================================
# RUBRIC MANAGEMENT
# ============================================

def list_rubric_sets() -> List[Dict[str, Any]]:
    """Fetch all rubric sets from DB."""
    if not db_client: return []
    return list(db_client.rubric_sets_col.find({}, {'_id': 0}))

def get_rubric_meta(rubric_set_id: str) -> Optional[Dict[str, Any]]:
    """Fetch metadata for a single rubric set."""
    if not db_client: return None
    return db_client.get_rubric_meta(rubric_set_id)

def extract_and_save_rubric_from_pdf(pdf_path: str, teacher_id: Optional[str],
                                     deadline_iso: Optional[str], 
                                     max_attempts: Optional[int]) -> Dict[str, Any]:
    """
    Uses core `evaluator.py` logic to extract rubrics and `database.py` to save.
    """
    try:
        # 1. Upload file to Gemini (needed for extraction)
        print(f"📤 Uploading rubric: {pdf_path}")
        file_obj = genai.upload_file(pdf_path)
        
        # 2. Extract using CORE logic
        print("🧠 Extracting rubrics...")
        parsed_rubrics = extract_rubrics_from_file(file_obj)
        
        # 3. Cleanup
        try: genai.delete_file(file_obj.name)
        except: pass
        
        if not parsed_rubrics:
            return {"error": "Failed to extract rubrics from PDF"}

        # Validate rubrics
        print("🕵️ Validating rubrics...")
        validation_result = validate_rubrics_with_llm(parsed_rubrics)

        # 4. Compute ID using CORE logic
        rubric_set_id = compute_rubric_set_id(parsed_rubrics)
        
        # 5. Parse deadline
        deadline_dt = datetime.fromisoformat(deadline_iso) if deadline_iso else None
        
        # 6. Save to DB
        if db_client:
            db_client.upsert_rubric_set(rubric_set_id, parsed_rubrics, deadline_dt, max_attempts)
            
            # Link to teacher
            if teacher_id:
                db_client.rubric_sets_col.update_one(
                    {"rubric_set_id": rubric_set_id},
                    {"$set": {"teacher_id": teacher_id}}
                )
                
        return {
            "ok": True,
            "rubric_set_id": rubric_set_id,
            "parsed_rubrics": parsed_rubrics,
            "validation": validation_result
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ============================================
# SUBMISSION & GRADING
# ============================================


def get_student_submission_record(student_id: str, rubric_set_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a student's submission record for a specific rubric.
    Used by frontend to check attempt counts without direct DB access.
    """
    if not db_client:
        return None
    return db_client.get_submission_record(student_id, rubric_set_id)

def list_submissions_for_student(student_id: str) -> List[Dict[str, Any]]:
    """List all submissions for a student."""
    if not db_client: return []
    return list(db_client.submissions_col.find({"student_id": student_id}, {'_id': 0}).sort("timestamp", -1))

def list_submissions_for_rubric(rubric_set_id: str) -> List[Dict[str, Any]]:
    """List all submissions for a rubric."""
    if not db_client: return []
    return list(db_client.submissions_col.find({"rubric_set_id": rubric_set_id}, {'_id': 0}))

def grade_student_submission(student_id: str, report_file_path: str, rubric_set_id: str) -> Dict[str, Any]:
    """
    Uses core `evaluator.py` logic to grade submission.
    """
    if not db_client: return {"error": "Database not connected"}

    try:
        # 1. Get Rubric Metadata
        rubric_meta = db_client.get_rubric_meta(rubric_set_id)
        if not rubric_meta: return {"error": "Rubric not found"}
        
        parsed_rubrics = rubric_meta.get('parsed_rubrics')
        
        # 2. Check Constraints (Deadline & Attempts)
        if rubric_meta.get('deadline'):
            deadline = datetime.fromisoformat(rubric_meta['deadline']).replace(tzinfo=timezone.utc)
            if now_utc() > deadline:
                return {"error": "Submission deadline has passed"}

        max_attempts = rubric_meta.get('max_attempts')
        record = db_client.get_submission_record(student_id, rubric_set_id)
        used_attempts = record.get('attempt_number', 0) if record else 0
        
        if max_attempts and used_attempts >= max_attempts:
            return {"error": f"Max attempts ({max_attempts}) reached"}

        # 3. Grade using CORE logic
        print(f"🧠 Grading submission for {student_id}...")
        # Note: grade_submission expects a file path, not file object, based on your main.py usage
        parsed_result = grade_submission(report_file_path, parsed_rubrics, GRADE_MODEL)
        
        # 4. Save to DB
        new_attempt = used_attempts + 1
        parsed_result["_timestamp"] = now_utc().isoformat()
        parsed_result["_attempt_number"] = new_attempt
        
        mongo_op = db_client.upsert_submission(
            student_id, rubric_set_id, report_file_path,
            parsed_rubrics, parsed_result, new_attempt
        )
        
        return {
            "result": parsed_result,
            "mongo_op": mongo_op,
            "meta": rubric_meta
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Grading failed: {str(e)}"}

# ============================================
# BLUEBOOK EXTRACTION
# ============================================

def extract_bluebook(image_paths: Union[str, List[str]]) -> Dict[str, Any]:
    """
    Uses core `bluebook_extractor.py` logic.
    """
    try:
        print(f"🧠 Extracting bluebook(s): {image_paths}")
        # Directly call the core logic function
        result = extract_bluebook_data(image_paths)
        
        # Standardize response for frontend
        if "error" in result:
             return {"error": result["error"]}

        bluebooks = result.get("bluebooks", [])
        return {
            "success": True,
            "bluebooks": bluebooks,
            "total_bluebooks": len(bluebooks),
            "visualized_images": result.get("visualized_images", [])
        }
        
    except Exception as e:
        return {"error": str(e)}

def save_bluebook_results(teacher_id: str, data: Dict[str, Any], filename: str) -> bool:
    """Save bluebook results to DB."""
    if not db_client: return False
    try:
        doc = {
            "teacher_id": teacher_id,
            "image_filename": filename,
            "extraction_date": now_utc().isoformat(),
            "bluebooks": data.get("bluebooks", []),
            "visualized_images": data.get("visualized_images", [])
        }
        db_client.db["bluebook_results"].insert_one(doc)
        return True
    except Exception:
        return False

def get_bluebook_history(teacher_id: str) -> List[Dict[str, Any]]:
    """Fetch bluebook history."""
    if not db_client: return []
    return list(db_client.db["bluebook_results"].find({"teacher_id": teacher_id}).sort("extraction_date", -1))

# ============================================
# AUTHENTICATION (Direct DB calls)
# ============================================

def login_student(student_id: str, password: str) -> bool:
    return db_client.verify_student_password(student_id, password) if db_client else False

def login_teacher(teacher_id: str, password: str) -> bool:
    return db_client.verify_teacher_password(teacher_id, password) if db_client else False

def register_student(student_id: str, name: str, password: str) -> bool:
    return db_client.create_student(student_id, name, password) if db_client else False

def register_teacher(name: str, password: str) -> Optional[str]:
    if not db_client: return None
    base = re.sub(r'[^a-z0-9]+', '_', name.strip().lower())
    teacher_id = f"t_{base[:20]}_{secrets.token_hex(2)}"
    if db_client.create_teacher(teacher_id, name, password):
        return teacher_id
    return None

def get_student_info(student_id: str):
    return db_client.get_student(student_id) if db_client else None

def get_teacher_info(teacher_id: str):
    return db_client.get_teacher(teacher_id) if db_client else None

# ============================================
# ALIASES FOR BACKWARD COMPATIBILITY
# ============================================

# The login/register pages expect these names:
verify_student_password = login_student
verify_teacher_password = login_teacher
get_student = get_student_info
get_teacher = get_teacher_info
