# rubric_extraction.py
import os
import sys
import tkinter as tk
from tkinter import filedialog
from datetime import datetime, timezone, timedelta
from google import genai
from google.genai import types

# Import the wrapper we just made
from ai_wrapper import GeminiLC

# --- CONFIGURATION ---
# Ensure your key is set
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = input("🔑 Enter your Google API Key: ").strip()

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

def select_file_locally():
    """Opens a dialog to select the PDF (replaces files.upload)"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(
        title="Select Rubric PDF",
        filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
    )
    root.destroy()
    return file_path

def main():
    # 1. 📂 Upload Rubric
    print("📄 Please select your rubric PDF file...")
    rubric_path = select_file_locally()
    
    if not rubric_path:
        raise SystemExit("❌ No rubric file selected.")

    print(f"✅ Selected rubric file: {rubric_path}")

    # Upload to Gemini (V2 Syntax)
    print("⬆️ Uploading to Gemini...")
    file_obj = client.files.upload(path=rubric_path)

    # 2. 🕒 User Inputs (Deadline & Attempts)
    deadline_input = input("\n⏰ Enter submission deadline (YYYY-MM-DD HH:MM in IST) or leave blank: ").strip()

    DEADLINE = None
    if deadline_input:
        try:
            deadline_ist = datetime.fromisoformat(deadline_input)
            if deadline_ist.tzinfo is None:
                # Treat as IST
                deadline_ist = deadline_ist.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            DEADLINE = deadline_ist.astimezone(timezone.utc)
        except Exception as e:
            print("❌ Error parsing datetime:", str(e))
            raise SystemExit("Invalid format.")

    max_attempts_input = input("🔁 Enter max attempts (integer) or leave blank for unlimited: ").strip()
    MAX_ATTEMPTS = int(max_attempts_input) if max_attempts_input.isdigit() else None

    # 3. ✅ Summary
    print("\n✅ Deadline and attempt settings recorded.")
    if DEADLINE:
        DEADLINE_IST = DEADLINE.astimezone(timezone(timedelta(hours=5, minutes=30)))
        print(f"  • Deadline (IST): {DEADLINE_IST.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    else:
        print("  • Deadline: None (unlimited time)")
    
    print(f"  • Max Attempts: {MAX_ATTEMPTS if MAX_ATTEMPTS else 'Unlimited'}")

    # 4. 🧠 Extract Rubrics (Direct Gemini Call)
    prompt = """
    You are an academic evaluator.
    Read this rubric document and return a JSON array describing:
    [
      { "title": "...", "description": "...", "scale": ["Excellent", "Good", "Fair", "Poor"] }
    ]
    Do NOT summarize — return full structured data only.
    """

    print("\n🧠 Extracting rubrics...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[file_obj, prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )

    print("\n✅ Rubrics extracted successfully!\n")
    print(response.text)

    # 5. ✨ Initialize LangChain Wrapper
    print("\n✨ Initializing LangChain wrapper...")
    lc_gemini = GeminiLC()
    print("✅ LangChain wrapper ready: lc_gemini")
    
    # Optional: Test the wrapper
    # print(lc_gemini("Hello, are you ready?"))

if __name__ == "__main__":
    main()
