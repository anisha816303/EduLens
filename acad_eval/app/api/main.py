# main.py - The execution and orchestration file.

import os, re, json, sys
from getpass import getpass
from datetime import datetime, timezone, timedelta
# REMOVED: from google.colab import files
import google.generativeai as genai

# --- Imports from other modules ---
# Assuming 'app' is the root level for imports when running in a structured environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.config import GEMINI_API_KEY, RUBRIC_MODEL, GRADE_MODEL, get_ist_timezone, now_utc
from app.core.database import db_client
from ai_models.llm_evaluation.evaluator import (
    extract_rubrics_from_file, compute_rubric_set_id, grade_submission,
    validate_rubrics_with_llm # NEW: Import the validation function
)

# --- Initialize Gemini Client ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception:
    raise SystemExit("❌ Failed to configure Gemini API.")

print("✅ Initialized dependencies and configured Gemini.")


# --- Replacement for files.upload() ---
def get_local_file_path(prompt_text: str) -> str:
    """Prompts the user for a local file path and validates it."""
    while True:
        file_path = input(prompt_text).strip()
        if not file_path:
            # Allow cancellation for optional uploads, but we'll enforce existence later.
            return ""

        if not os.path.exists(file_path):
            print(f"❌ Error: File not found at '{file_path}'. Please check the path.")
            continue
        return file_path


# =========================
# 1️⃣ TEACHER FLOW
# =========================
def teacher_setup_rubric():
    """
    Teacher uploads a rubric PDF ONCE, sets deadline & max attempts.
    We parse rubrics, compute rubric_set_id, and persist rubric metadata.
    """
    if not db_client:
        raise SystemExit("❌ Database client not initialized. Cannot proceed.")

    print("\n📘 [TEACHER MODE] Create / Update Rubric Set")
    print("📄 Enter the **FULL PATH** to your rubric PDF file (e.g., /Users/user/Desktop/rubric.pdf)")

    rubric_filename = get_local_file_path("   -> Rubric File Path: ")
    if not rubric_filename:
        raise SystemExit("❌ No rubric file provided. Cannot continue.")

    print(f"✅ Loaded rubric file: {rubric_filename}")

    # Upload your PDF to Gemini for parsing
    print("⬆️ Temporarily uploading rubric file to Gemini...")
    file_obj = genai.upload_file(rubric_filename)

    # Get deadline input (in IST)
    deadline_input = input("\n⏰ Enter submission deadline (YYYY-MM-DD HH:MM in IST) or leave blank: ").strip()
    DEADLINE = None
    if deadline_input:
        try:
            deadline_ist = datetime.fromisoformat(deadline_input)
            if deadline_ist.tzinfo is None:
                # Assuming input is local IST time if no timezone is specified
                deadline_ist = deadline_ist.replace(tzinfo=get_ist_timezone())
            DEADLINE = deadline_ist.astimezone(timezone.utc)  # Convert to UTC
        except Exception as e:
            print("❌ Error parsing datetime:", str(e))
            genai.delete_file(file_obj.name)
            raise SystemExit("Invalid format. Use YYYY-MM-DD HH:MM (e.g., 2025-12-01 23:59)")

    # Get max attempts input
    max_attempts_input = input("🔁 Enter max attempts per student (integer) or leave blank for unlimited: ").strip()
    MAX_ATTEMPTS = int(max_attempts_input) if max_attempts_input.isdigit() else None

    # Extract rubrics using the evaluator module (Cell 2 logic)
    print("\n🧠 Asking Gemini to extract and understand rubrics...")
    parsed_rubrics = extract_rubrics_from_file(file_obj)
    print(parsed_rubrics)

    # Clean up uploaded file from Gemini
    try:
        genai.delete_file(file_obj.name)
    except Exception:
        pass

    # Compute Rubric Set ID (Cell 4 logic)
    rubric_set_id = compute_rubric_set_id(parsed_rubrics)

    # Upsert rubric-set metadata (persist deadline & max_attempts)
    db_client.upsert_rubric_set(rubric_set_id, parsed_rubrics, DEADLINE, MAX_ATTEMPTS)

    # Confirmation summary
    print("\n✅ Rubric setup complete.")
    print(f"   • Rubric Set ID: {rubric_set_id}")
    if DEADLINE:
        ist_time = DEADLINE.astimezone(get_ist_timezone())
        print(f"   • Deadline (IST): {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"   • Deadline (UTC): {DEADLINE.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("   • Deadline: None (no submission window limit)")

    print(f"   • Max Attempts: {MAX_ATTEMPTS if MAX_ATTEMPTS is not None else 'Unlimited'}")
    print(f"   • Parsed Rubrics: {len(parsed_rubrics)} criteria")

    print("\n📌 Share this Rubric Set ID with students so they can submit against it.")
    return rubric_set_id


# =========================
# 2️⃣ STUDENT FLOW
# =========================
def student_grade_submission():
    """
    Student uploads a report PDF for an EXISTING rubric_set_id.
    We read rubric metadata from DB, enforce deadline & attempts,
    grade via Gemini, and persist the submission.
    """
    if not db_client:
        raise SystemExit("❌ Database client not initialized. Cannot proceed.")

    print("\n🎓 [STUDENT MODE] Submit Report for Grading")

    rubric_set_id = input("📌 Enter Rubric Set ID (given by your teacher): ").strip()
    if not rubric_set_id:
        raise SystemExit("❌ Rubric Set ID is required.")

    # Read authoritative metadata back from DB
    rubric_meta = db_client.get_rubric_meta(rubric_set_id)
    if not rubric_meta:
        raise SystemExit("❌ No rubric metadata found for the given Rubric Set ID.")

    parsed_rubrics = rubric_meta.get("parsed_rubrics")
    if not parsed_rubrics:
        raise SystemExit("❌ Rubric set has no parsed rubrics stored.")

    stored_deadline = None
    if rubric_meta.get("deadline"):
        stored_deadline = datetime.fromisoformat(rubric_meta["deadline"]).replace(tzinfo=timezone.utc)
    stored_max_attempts = rubric_meta.get("max_attempts")

    # Display authoritative info
    print("\n🧩 Rubric loaded successfully (authoritative metadata read from DB).")
    if stored_deadline:
        ist_time = stored_deadline.astimezone(get_ist_timezone())
        print(f"⏰ Deadline (IST): {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("⏰ No deadline set — unlimited submission window.")
    print(f"🔁 Max Attempts: {stored_max_attempts if stored_max_attempts is not None else 'Unlimited'}")
    print(f"ℹ️ Rubric Set ID: {rubric_set_id}")

    # Student login & checks
    student_id = input("\n👤 Enter your Student ID: ").strip()
    if not student_id:
        raise SystemExit("❌ Student ID is required.")

    # Deadline enforcement
    now = now_utc()
    if stored_deadline and now > stored_deadline:
        ist_time = stored_deadline.astimezone(get_ist_timezone())
        raise SystemExit(f"⛔ Submission window closed! Deadline was {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Attempt tracking
    record = db_client.get_submission_record(student_id, rubric_set_id)
    used_attempts = record.get("attempt_number", 0) if record else 0
    remaining_attempts = (stored_max_attempts - used_attempts) if stored_max_attempts is not None else "Unlimited"

    print(f"\n🧾 Attempts Used: {used_attempts} | Attempts Left: {remaining_attempts}")
    if stored_max_attempts is not None and used_attempts >= stored_max_attempts:
        raise SystemExit(f"⛔ Maximum attempts reached ({used_attempts}/{stored_max_attempts}).")

    # Upload report PDF
    print("\n📤 Enter the **FULL PATH** to your project report PDF for grading:")
    fname = get_local_file_path("   -> Report File Path: ")

    if not fname:
        raise SystemExit("❌ No report uploaded.")
    print(f"✅ Loaded report file: {fname}")

    # Run grading
    print("\n🧠 Starting Gemini Grading...")
    parsed_result = grade_submission(fname, parsed_rubrics, GRADE_MODEL)

    # Update submission record
    new_attempt_number = used_attempts + 1
    parsed_result["_timestamp"] = now.isoformat()
    parsed_result["_attempt_number"] = new_attempt_number

    mongo_op = db_client.upsert_submission(
        student_id, rubric_set_id, fname, parsed_rubrics, parsed_result, new_attempt_number
    )

    # Display summary
    print("\n✅ Evaluation Complete!")
    print(f"   • Student ID: {student_id}")
    print(f"   • Rubric Set ID: {rubric_set_id}")
    print(f"   • Attempt: {new_attempt_number} / {stored_max_attempts if stored_max_attempts is not None else '∞'}")

    total_rubric_items = len(parsed_rubrics)
    max_total_score = total_rubric_items * 10

    print(f"   • Total Score: {parsed_result['total_score']} / {max_total_score}")
    print(f"   • MongoDB Operation: {mongo_op}")

    print("\n📊 Detailed Rubric Feedback:\n")
    print(json.dumps(parsed_result, indent=2, ensure_ascii=False))


# =========================
# 3️⃣ ENTRY POINT
# =========================
if __name__ == "__main__":
    try:
        print("\n===============================")
        print(" Academic Evaluation System CLI")
        print("===============================\n")
        print("Select Mode:")
        print("  1. Teacher – Create / Update Rubric Set")
        print("  2. Student – Submit Report for Grading")
        mode = input("\nEnter 1 or 2: ").strip()

        if mode == "1":
            teacher_setup_rubric()
        elif mode == "2":
            student_grade_submission()
        else:
            print("❌ Invalid choice. Please run again and choose 1 or 2.")

    except SystemExit as e:
        print(e)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
