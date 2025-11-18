import json
import os
from datetime import timezone, timedelta
from google import genai
from google.genai import types

from app.core.database import db_client
from app.core.config import GEMINI_API_KEY, GRADE_MODEL, now_utc

# Initialize Client
client = genai.Client(api_key=GEMINI_API_KEY)

# IST Helper
def get_ist_timezone():
    return timezone(timedelta(hours=5, minutes=30))

def evaluate_student_submission(student_id: str, report_file_path: str, parsed_rubrics, manual_deadline, manual_max_attempts):
    """
    Handles DB checks and grading using Gemini 2.5
    """
    if not db_client:
        raise SystemExit("❌ Database client not initialized.")

    # --- 1. Compute Set ID & Upsert Metadata ---
    # Simple hash for ID (simplified for brevity)
    rubric_set_id = f"rubric_{abs(hash(json.dumps(parsed_rubrics)))}"
    
    db_client.upsert_rubric_set(rubric_set_id, parsed_rubrics, manual_deadline, manual_max_attempts)

    # --- 2. Fetch Authoritative Metadata ---
    rubric_meta = db_client.get_rubric_meta(rubric_set_id)
    
    stored_deadline = None
    if rubric_meta and rubric_meta.get("deadline"):
        stored_deadline = datetime.fromisoformat(rubric_meta["deadline"]).replace(tzinfo=timezone.utc)
    stored_max_attempts = rubric_meta.get("max_attempts")

    # --- 3. Display Info ---
    print("\n🧩 Rubric loaded (Metadata synced from DB).")
    print(f"ℹ️ Rubric Set ID: {rubric_set_id}")
    
    # Deadline Check
    now = now_utc()
    if stored_deadline:
        ist_time = stored_deadline.astimezone(get_ist_timezone())
        print(f"⏰ Deadline (IST): {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        if now > stored_deadline:
            raise SystemExit(f"⛔ Submission window closed! Deadline was {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Attempt Check
    record = db_client.get_submission_record(student_id, rubric_set_id)
    used_attempts = record.get("attempt_number", 0) if record else 0
    
    print(f"🧾 Attempts Used: {used_attempts} / {stored_max_attempts if stored_max_attempts else '∞'}")
    
    if stored_max_attempts is not None and used_attempts >= stored_max_attempts:
        raise SystemExit(f"⛔ Maximum attempts reached.")

    # --- 4. Run Grading (V2 Logic) ---
    if not report_file_path:
         raise SystemExit("❌ No report file provided.")

    print(f"✅ Processing report: {report_file_path}")
    print("\n🧠 Starting Gemini Grading...")
    
    # Upload Student PDF
    student_file_obj = client.files.upload(path=report_file_path)

    # Grading Prompt
    grading_prompt = f"""
    You are a strict grader. 
    Grade this student submission based ONLY on these rubrics:
    {json.dumps(parsed_rubrics)}

    Return a JSON object with:
    - "evaluations": [list of feedback per criteria]
    - "total_score": (sum of scores)
    - "feedback": (overall summary)
    """

    try:
        response = client.models.generate_content(
            model=GRADE_MODEL, # e.g., "gemini-2.5-flash"
            contents=[student_file_obj, grading_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        parsed_result = json.loads(response.text)
    except Exception as e:
        raise RuntimeError(f"Grading Failed: {e}")

    # --- 5. Save Results ---
    new_attempt_number = used_attempts + 1
    parsed_result["_timestamp"] = now.isoformat()
    parsed_result["_attempt_number"] = new_attempt_number

    mongo_op = db_client.upsert_submission(
        student_id, rubric_set_id, report_file_path, parsed_rubrics, parsed_result, new_attempt_number
    )

    return parsed_result, mongo_op, rubric_meta
