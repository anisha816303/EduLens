import json, re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
import PyPDF2
import hashlib

def extract_rubrics_from_file(file) -> str:
    """Uses Gemini to parse the rubric JSON from a PDF file."""
    prompt = """
    You are an academic evaluator.
    Read this rubric document and return a JSON array describing:
    [
      { "title": "...", "description": "...", "scale": ["Excellent", "Good", "Fair", "Poor"] }
    ]
    For each item, ensure it has a unique, URL-safe 'key' field derived from the title.
    Do NOT summarize — return full structured data only.
    """
    response = genai.GenerativeModel("gemini-2.5-flash").generate_content(
        [prompt, file]
    )
    raw_rubric_text = getattr(response, "text", None) or getattr(response, "output_text", None) or str(response)

    # Extract and clean JSON array
    match = re.search(r"\[\s*\{.*?\}\s*\]", raw_rubric_text, re.DOTALL)
    arr_text = match.group(0) if match else raw_rubric_text
    arr_text = arr_text.replace("“", '"').replace("”", '"').replace("’", "'")

    try:
        parsed_rubrics = json.loads(arr_text)
    except Exception as e:
        raise ValueError(f"Failed to parse rubric JSON: {e}")

    # Ensure each rubric has a 'key' for stability
    for rubric in parsed_rubrics:
        if "key" not in rubric and "title" in rubric:
            # Simple key generation
            rubric["key"] = rubric["title"].lower().strip().replace(" ", "_").replace("/", "").replace("-", "_")
    
    return parsed_rubrics

def compute_rubric_set_id(parsed_rubrics: List[Dict[str, Any]]) -> str:
    """Computes a stable hash for the rubric set."""
    rubric_json_canonical = json.dumps(parsed_rubrics, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(rubric_json_canonical.encode("utf-8")).hexdigest()

def extract_numeric_score(text: Any) -> Optional[float]:
    """Robustly extracts a score out of 10 from the feedback string."""
    if not isinstance(text, str): return None
    text = text.strip().replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", text)
    if m:
        val = float(m.group(1))
        return val if 0 <= val <= 10 else None
    m2 = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    for v in m2:
        val = float(v)
        if 0 <= val <= 10:
            return val
    return None

def grade_submission(fname: str, parsed_rubrics: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
    """Calls Gemini to grade the submitted report and parses the result."""
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

    # Try direct file upload
    try:
        file_obj = genai.upload_file(fname)
        resp = model.generate_content([grader_instruction, file_obj])
        raw_out = getattr(resp, "text", None) or str(resp)
        genai.delete_file(file_obj.name) # clean up the uploaded file immediately
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
        raw_out = getattr(resp, "text", None) or str(resp)

    # Parse JSON from Gemini output
    m = re.search(r"\{.*\}", raw_out, re.DOTALL)
    if not m:
        raise ValueError(f"Model did not return valid JSON. Raw output: {raw_out[:1000]}")
        
    json_text = re.sub(r'[“”’]', '"', m.group(0))
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text) # remove trailing commas
    parsed_result = json.loads(json_text)

    # Compute total score
    numeric_scores = []
    for r in parsed_rubrics:
        title = (r.get("title") or "").strip()
        key = (r.get("key") or "").strip()
        
        # Check by returned key (which should match the rubric key)
        found_score = False
        for returned_k, returned_v in parsed_result.items():
            if returned_k.strip().lower() == key.lower():
                s = extract_numeric_score(returned_v)
                if s is not None:
                    numeric_scores.append(s)
                found_score = True
                break
        
    total = round(sum(numeric_scores), 2)
    parsed_result["total_score"] = total
    
    return parsed_result