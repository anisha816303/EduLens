import json
import re
import hashlib
from typing import Dict, Any, List, Optional

import google.generativeai as genai
import PyPDF2


# ---------------- Rubric extraction (match Cell 2) ----------------

def extract_rubrics_from_file(file) -> List[Dict[str, Any]]:
    """
    Uses Gemini to parse the rubric JSON from a PDF file.

    Logic & prompt are aligned with Colab Cell 2:
    - Same prompt text
    - Pass [prompt, file] to generate_content
    - Then parse the JSON array locally
    - Add a 'key' field in Python (not in the prompt)
    """
    prompt = """
You are an academic evaluator.
Read this rubric document and return a JSON array describing:
[
  { "title": "...", "description": "...", "scale": ["Excellent", "Good", "Fair", "Poor"] }
]
Do NOT summarize — return full structured data only.
"""
    response = genai.GenerativeModel("gemini-2.5-flash").generate_content(
        [prompt, file]
    )

    raw_rubric_text = (
        getattr(response, "text", None)
        or getattr(response, "output_text", None)
        or str(response)
    )

    # ---------------------- Robust JSON extraction ----------------------

    # 1. Try to extract content inside ```json ... ``` blocks
    fenced = re.search(r"```json(.*?)```", raw_rubric_text, re.DOTALL | re.IGNORECASE)
    if fenced:
        arr_text = fenced.group(1).strip()
    else:
        # 2. Fallback: extract from the FIRST '[' to the LAST ']'
        start = raw_rubric_text.find("[")
        end = raw_rubric_text.rfind("]") + 1

        if start != -1 and end != -1 and end > start:
            arr_text = raw_rubric_text[start:end]
        else:
            # 3. Last fallback — raw text (will likely error; debugging)
            arr_text = raw_rubric_text

    # 4. Normalize quotes
    arr_text = arr_text.replace("“", '"').replace("”", '"').replace("’", "'")

    # 5. Remove trailing commas inside arrays/objects
    arr_text = re.sub(r",\s*([}\]])", r"\1", arr_text)

    # 6. Remove fenced block backticks
    arr_text = arr_text.replace("```", "").strip()

    # ---------------------- Parse the JSON ----------------------
    try:
        parsed_rubrics = json.loads(arr_text)
    except Exception as e:
        raise ValueError(f"Failed to parse rubric JSON: {e}\nPreview:\n{arr_text[:1000]}")

    # ---------------------- Add stable keys ----------------------
    for i, rubric in enumerate(parsed_rubrics):
        if "key" not in rubric:
            title = (rubric.get("title") or f"criterion_{i+1}").strip()
            key = title.lower()
            key = re.sub(r"\s+", "_", key)
            key = key.replace("/", "_").replace("-", "_")
            rubric["key"] = key

    return parsed_rubrics


# ---------------- Rubric set ID (matches Cell 4) ----------------

def compute_rubric_set_id(parsed_rubrics: List[Dict[str, Any]]) -> str:
    """Computes a stable hash for the rubric set (same logic as Cell 4)."""
    rubric_json_canonical = json.dumps(parsed_rubrics, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(rubric_json_canonical.encode("utf-8")).hexdigest()


# ---------------- Score extraction helper (Cell 4 logic) ----------------

def extract_numeric_score(text: Any) -> Optional[float]:
    """Robustly extracts a score out of 10 from the feedback string (Cell 4 logic)."""
    if not isinstance(text, str):
        return None
    text = text.strip().replace(",", ".")
    # Look for '<num>/10'
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    if m:
        val = float(m.group(1))
        return val if 0 <= val <= 10 else None

    # Fallback: any number between 0 and 10
    m2 = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    for v in m2:
        val = float(v)
        if 0 <= val <= 10:
            return val
    return None


# ---------------- Grading (match Cell 4 logic) ----------------

def grade_submission(fname: str,
                     parsed_rubrics: List[Dict[str, Any]],
                     model_name: str) -> Dict[str, Any]:
    """
    Calls Gemini to grade the submitted report and parses the result.

    This is aligned with Colab Cell 4:
    - Same grading prompt
    - Upload PDF to Gemini, fallback to local PDF text extraction
    - Parse JSON object from model output
    - Compute total_score by matching rubric key OR title (plus fuzzy match)
    """
    expected_keys = [r["key"] for r in parsed_rubrics if "key" in r]
    rubrics_json_for_prompt = json.dumps(parsed_rubrics, indent=2, ensure_ascii=False)
    requested_keys_list = expected_keys + ["overall_summary"]
    requested_keys = ", ".join([f'"{k}"' for k in requested_keys_list])

    grader_instruction = f"""
You are an expert academic evaluator.

Use the EXACT rubric JSON below (do NOT modify keys).
Rubrics JSON:
{rubrics_json_for_prompt}

Task:
- For each rubric key, return "Score: <number>/10 — <one-line feedback>"
- Include "overall_summary"
- Return ONLY a JSON object with keys: {requested_keys}
"""

    model = genai.GenerativeModel(model_name)
    raw_out = ""
    file_obj = None

    # Try direct file upload (Cell 4 style)
    try:
        file_obj = genai.upload_file(fname)
        resp = model.generate_content([grader_instruction, file_obj])
        raw_out = (
            getattr(resp, "text", None)
            or getattr(resp, "output_text", None)
            or str(resp)
        )
    except Exception as e:
        print(f"⚠️ Upload to Gemini failed ({e}), attempting local PDF extraction...")
        # Fallback to local PDF text extraction
        txt = ""
        try:
            with open(fname, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                txt = "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            txt = ""
        if not txt:
            raise SystemExit("❌ Could not upload or extract text from the PDF.")
        resp = model.generate_content(grader_instruction + "\n\nProject Report:\n" + txt)
        raw_out = (
            getattr(resp, "text", None)
            or getattr(resp, "output_text", None)
            or str(resp)
        )
    finally:
        # Clean up uploaded file if we created one
        if file_obj is not None:
            try:
                genai.delete_file(file_obj.name)
            except Exception:
                pass

    # Parse JSON from Gemini output (Cell 4 pattern)
    m = re.search(r"\{.*\}", raw_out, re.DOTALL)
    if not m:
        raise ValueError(
            f"Model did not return valid JSON. Raw output (preview):\n{raw_out[:1000]}"
        )

    json_text = m.group(0)
    json_text = re.sub(r'[“”’]', '"', json_text)
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)  # remove trailing commas

    parsed_result = json.loads(json_text)

    # Compute total score like Cell 4:
    #   - match by key
    #   - if not found, try title
    #   - if still not found, fuzzy substring match on keys
    numeric_scores: List[float] = []

    for r in parsed_rubrics:
        title = (r.get("title") or "").strip()
        key = (r.get("key") or "").strip()
        found = False

        # Exact match on key or title
        for returned_k, returned_v in parsed_result.items():
            if not isinstance(returned_k, str):
                continue
            rk = returned_k.strip().lower()
            if rk == key.lower() or rk == title.lower():
                s = extract_numeric_score(returned_v)
                if s is not None:
                    numeric_scores.append(s)
                found = True
                break

        # Fuzzy substring match on returned keys if not found
        if not found:
            for returned_k, returned_v in parsed_result.items():
                if not isinstance(returned_k, str):
                    continue
                rk = returned_k.strip().lower()
                if title.lower() in rk or key.lower() in rk:
                    s = extract_numeric_score(returned_v)
                    if s is not None:
                        numeric_scores.append(s)
                        found = True
                        break

    total = round(sum(numeric_scores), 2)
    parsed_result["total_score"] = total

    return parsed_result
