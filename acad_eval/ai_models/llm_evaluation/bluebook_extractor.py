# ai_models/llm_evaluation/bluebook_extractor.py

import json
import PIL.Image
import google.generativeai as genai 
from typing import Dict, Any

def extract_bluebook_data(image_path: str) -> Dict[str, Any]:
    """
    Analyzes a bluebook cover page image to extract student metadata and marks
    using the globally initialized GEMINI_CLIENT.
    """
  
    # --- 2. LOAD IMAGE ---
    try:
        img = PIL.Image.open(image_path)
    except Exception as e:
        return {"error": f"Error loading image: {e}"}

    # --- 3. REFINE THE PROMPT ---
    prompt = """
    Analyze this Blue Book cover page as a structured table.
    Step 0: Check if there are multiple bluebooks in one image, if present then for each bluebook perform the following steps and return the results for all the bluebooks as a nested json. If a single bluebook still proceed with the steps for that bluebook.
    Step 1: Locate the row where the 'Test' column says 'T1' or there is a Date present.
    Step 2: In that same row, read the handwritten number in the 'Marks Obtained' column.
    Step 3: Check the next row in the 'Marks Obtained' column, if its filled with marks, then add the average of the first and second rows marks and round it off.
    Step 4: If that fails, look at the bottom summary table for a field labeled "Test Marks" or "Total".
    
    Return this JSON structure:
    {
      "usn": "The Student Registration Number (e.g., 1MS22CS...)",
      "subject_code": "The Subject Code",
      "marks_obtained": "The handwritten value from the T1 row or Test Marks box "
    }
    """

    # --- 4. GENERATE CONTENT ---
    

    print("Scanning grid structure...")
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        response = model.generate_content(
            [
                img,
                prompt
            ],
            generation_config={
                "response_mime_type": "application/json"
            }
        )

        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}
