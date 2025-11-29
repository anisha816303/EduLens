# Add these imports near the top of your file
import os
import io
import base64
import json
import PIL.Image
from google import genai
from google.genai import types
from google.genai import Client # <-- MODERN API CLIENT
import cv2
import numpy as np
import re # <-- REGEX IMPORT ADDED
from ultralytics import YOLO
from pathlib import Path
from typing import List, Tuple, Dict, Any, Union

# ---------------- CONFIG ----------------
# Get the project root directory, which is three levels up from this file's directory
# (yolo_pipeline -> ai_models -> acad_eval -> project_root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Define paths relative to the project root
YOLO_WEIGHTS_PATH = PROJECT_ROOT / "acad_eval" / "ai_models" / "yolo_pipeline" / "weights" / "best.pt"
OUTPUT_PROJECT_PATH = PROJECT_ROOT / "outputs"

# --- API KEY ---
# Import from centralized config which handles .env and Streamlit secrets
try:
    # Try to import from the app.core.config module
    import sys
    from pathlib import Path
    acad_eval_path = Path(__file__).resolve().parents[2]
    if str(acad_eval_path) not in sys.path:
        sys.path.insert(0, str(acad_eval_path))
    from app.core.config import GEMINI_API_KEY
    API_KEY = GEMINI_API_KEY
except ImportError:
    # Fallback to environment variable if config import fails
    API_KEY = os.environ.get("GEMINI_API_KEY", "")
    if not API_KEY:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                API_KEY = st.secrets['GEMINI_API_KEY']
        except:
            pass

# Pick a model you have access to
GEMINI_MODEL = "gemini-2.5-flash"

# Additional config for pipeline
MODEL_PATH = str(YOLO_WEIGHTS_PATH) # Use the relative path
OUTPUT_PROJECT = str(OUTPUT_PROJECT_PATH) # Use the relative path
CONF_THRESHOLD = 0.25
OUTPUT_NAME = "bluebook_test"
BLUEBOOK_CLUSTER_THRESHOLD_Y = 1000 # High threshold for single document mode

# ----------------------------
# Fallback Image Processing (Kept for compatibility)
# ----------------------------
try:
    from image_processing_fixed import extract_handwriting_from_boxes, CLASS_NAMES
except ImportError:
    CLASS_NAMES = ['USN_BOX', 'SUBJECT_BOX', 'CIE1_MARKS_BOX', 'CIE2_MARKS_BOX']
    def extract_handwriting_from_boxes(img, boxes, class_ids=None, threshold=180): return img

# ----------------------------
# GEMINI PROMPT (Comprehensive prompt referencing YOLO Boxes)
# ----------------------------
GEMINI_PROMPT_SINGLE_BLUEBOOK = """
You are analyzing a crop of a Blue Book internal assessment sheet. This crop contains exactly ONE Blue Book.

The image contains:
- The printed form fields (USN, COURSE CODE & NAME, Marks Grid).
- Handwritten student data and marks.
- **IMPORTANT**: The image has **colored bounding boxes** drawn around the fields. USE these boxes as strong visual anchors to precisely locate and read the handwritten data.

Your task is to extract all required information.

1. Locate the field "USN" and read the Student Registration Number.
2. Locate "COURSE CODE & NAME" and extract ONLY the subject code (e.g., CS533, 21CS34, etc.)
3. Locate the internal marks grid. Extract marks for T1 and T2.

4. Return the result strictly in this JSON structure:

{
  "usn": "...",
  "subject_code": "...",
  "cie_marks": {
    "T1": {
      "Q1": { "a": "...", "b": "...", "c": "..." , "d": "..." },
      "Q2": { "a": "...", "b": "...", "c": "..." , "d": "..." },
      "Q3": { "a": "...", "b": "...", "c": "..." , "d": "..." }
    },
    "T2": {
      "Q1": { "a": "...", "b": "...", "c": "..." , "d": "..." },
      "Q2": { "a": "...", "b": "...", "c": "..." , "d": "..." },
      "Q3": { "a": "...", "b": "...", "c": "..." , "d": "..." }
    }
  }
}

VERY IMPORTANT RULES:
- If any value is missing, use null
- DO NOT return explanations or any text outside of the JSON object.
- Return ONLY valid JSON.
"""

# ----------------------------
# Helper: create Gemini client
# ----------------------------
def make_gemini_client(api_key: str = API_KEY) -> Client:
    """Create Gemini client using the modern google-genai SDK."""
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("Gemini API key is not configured.")
    try:
        client = Client(api_key=api_key)
        return client
    except ImportError:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")
    except Exception as e:
        raise RuntimeError(f"Failed to create Gemini client: {e}")

# ----------------------------
# Helper: call Gemini on a PIL image and parse JSON
# ----------------------------
def call_gemini_for_pil_image(
    pil_image: PIL.Image.Image, 
    client: Client, 
    prompt_text: str, 
    model: str = GEMINI_MODEL
) -> Dict[str, Any]:
    """Sends one PIL image + prompt to Gemini Vision."""
    try:
        response = client.models.generate_content(
            model=model,
            contents=[prompt_text, pil_image]
        )
    except Exception as e:
        return {"error": f"gemini call failed: {e}"}

    json_text = response.text.strip()
    
    try:
        return json.loads(json_text)
    except Exception:
        start = json_text.find("{")
        end = json_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(json_text[start:end+1])
            except Exception as e:
                return {"error": f"json parse failed after substring attempt: {e}", "raw": json_text}
        return {"error": "could not parse gemini response as JSON", "raw": json_text}

# ----------------------------
# Helper: Cluster detected boxes (Restored to Simple Single-Cluster Mode)
# ----------------------------
def cluster_boxes_into_bluebooks(all_boxes_data: List[Tuple[int, float, float, float, float]]) -> List[List[Tuple[int, float, float, float, float]]]:
    """Returns all detected boxes in a single cluster, assuming a single document."""
    if not all_boxes_data:
        return []
    
    # Return a list containing a single list of all boxes
    return [all_boxes_data]

# ----------------------------
# Helper: Get the overall bounding box for a cluster
# ----------------------------
def get_cluster_bbox(cluster: List[Tuple[int, float, float, float, float]]) -> Tuple[int, int, int, int]:
    """Returns (x1, y1, x2, y2) encompassing all boxes in the cluster."""
    if not cluster:
        return 0, 0, 0, 0
    x1 = int(min(b[1] for b in cluster))
    y1 = int(min(b[2] for b in cluster))
    x2 = int(max(b[3] for b in cluster))
    y2 = int(max(b[4] for b in cluster))
    return x1, y1, x2, y2

# ----------------------------
# YOLO Execution and Box Extraction
# ----------------------------
def run_yolo_and_extract_boxes(
    image_path: str, model_path: str, output_project: str, conf_threshold: float
) -> Tuple[Path, List[Tuple[int, float, float, float, float]]]:
    """Runs YOLO prediction and returns the path to the visualized image and box data."""
    model = YOLO(model_path)
    
    results = model.predict(
        source=image_path, 
        conf=conf_threshold, 
        show_labels=False,
        save_conf=True, 
        save=True, 
        project=output_project, 
        name=OUTPUT_NAME, 
        exist_ok=True
    )

    yolo_run_dir = Path(results[0].save_dir)
    visualized_image_path = yolo_run_dir / Path(image_path).name
    
    all_boxes_data = []
    for r in results:
        boxes = r.boxes.xyxy.cpu().numpy()
        class_ids = r.boxes.cls.cpu().numpy().astype(int)
        for cls_id, box in zip(class_ids, boxes):
            all_boxes_data.append((cls_id, *box))
            
    return visualized_image_path, all_boxes_data

# ----------------------------
# Gemini Processing for a single bluebook
# ----------------------------
def process_single_bluebook_with_gemini(
    cluster: List[Tuple[int, float, float, float, float]],
    visualized_img_rgb: np.ndarray,
    client: Client
) -> Dict[str, Any]:
    """Crops a bluebook from the image and sends it to Gemini for extraction."""
    x1_bb, y1_bb, x2_bb, y2_bb = get_cluster_bbox(cluster)
    
    pad = 50 
    x1_crop, y1_crop = max(0, x1_bb - pad), max(0, y1_bb - pad)
    x2_crop, y2_crop = min(visualized_img_rgb.shape[1], x2_bb + pad), min(visualized_img_rgb.shape[0], y2_bb + pad)
    
    crop = visualized_img_rgb[y1_crop:y2_crop, x1_crop:x2_crop]
    
    if crop.size == 0:
        return {"error": "Crop size is zero."}

    pil_crop = PIL.Image.fromarray(crop)
    result = call_gemini_for_pil_image(pil_crop, client, prompt_text=GEMINI_PROMPT_SINGLE_BLUEBOOK, model=GEMINI_MODEL)
    
    # --- USN Validation ---
    usn_raw = result.get("usn")
    if usn_raw and isinstance(usn_raw, str):
        cleaned_usn = usn_raw.upper().strip().replace('O', '0').replace('I', '1')
        usn_pattern = r"^[1I]MS(22|23)CS\d{3}$"
        if re.match(usn_pattern, cleaned_usn):
            result["usn"] = cleaned_usn
    
    return result

# ----------------------------
# Main Pipeline Orchestration
# ----------------------------
def run_pipeline_and_call_gemini(
    image_paths: Union[str, List[str]],
    model_path: str = MODEL_PATH,
    output_project: str = OUTPUT_PROJECT,
    conf_threshold: float = CONF_THRESHOLD
) -> Dict[str, Any]:
    """
    Runs YOLO, clusters boxes, and sends crops to Gemini for data extraction.
    Supports processing multiple images and aggregating results.
    """
    if isinstance(image_paths, str):
        image_paths = [image_paths]

    # Initialize Gemini client once
    try:
        client = make_gemini_client()
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}

    aggregated_data = {"bluebooks": []}
    visualized_images = []
    
    # Process each image
    for image_path in image_paths:
        print(f"Processing: {image_path}")
        
        # 1. Run YOLO and get box data
        try:
            visualized_image_path, all_boxes_data = run_yolo_and_extract_boxes(
                image_path, model_path, output_project, conf_threshold
            )
            visualized_images.append(str(visualized_image_path))
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            continue

        # 2. Cluster boxes
        bluebook_clusters = cluster_boxes_into_bluebooks(all_boxes_data)
        if not bluebook_clusters:
            print(f"No bluebooks detected in {image_path}")
            continue

        # 3. Load the visualized image
        img_bgr_viz = cv2.imread(str(visualized_image_path))
        if img_bgr_viz is None:
             print(f"Could not read visualized image at {visualized_image_path}")
             continue
        visualized_img_rgb = cv2.cvtColor(img_bgr_viz, cv2.COLOR_BGR2RGB)
        
        # 4. Process each bluebook in the image
        for cluster in bluebook_clusters:
            result = process_single_bluebook_with_gemini(cluster, visualized_img_rgb, client)
            
            if "error" not in result and result.get('usn') and result.get('usn') != 'null':
                # Add source image info for tracking
                result['_source_image'] = str(Path(image_path).name)
                aggregated_data["bluebooks"].append(result)

    # 5. Save and return final results
    # We'll save the combined JSON in the output directory of the last processed image, 
    # or a general output dir if possible. For now, use the project output dir.
    
    output_dir = Path(output_project) / OUTPUT_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    
    gemini_output_file = output_dir / "combined_gemini_results.json"
    
    with open(gemini_output_file, "w") as f:
        json.dump(aggregated_data, f, indent=2)

    return {
        "visualized_images": visualized_images,
        "gemini_json": str(gemini_output_file),
        "gemini_result": aggregated_data
    }

# ----------------------------
# Example: run this integration in __main__
# ----------------------------
if __name__ == "__main__":
    # Define a sample image path for testing purposes
    test_image_path = str(PROJECT_ROOT / "jpegmini_optimized" / "IMG_4821.jpg")
    
    if not Path(test_image_path).exists():
        print(f"Test image not found at: {test_image_path}")
    else:
        # Test with a list of images
        test_image_paths = [test_image_path]
        
        print(f"Running pipeline on {len(test_image_paths)} images...")
        
        res = run_pipeline_and_call_gemini(
            test_image_paths,
            model_path=MODEL_PATH,
            output_project=OUTPUT_PROJECT
        )
        
        print("\nPipeline result summary:")
        bluebook_count = len(res.get("gemini_result", {}).get("bluebooks", []))
        
        print(json.dumps({
            "total_bluebooks_found": bluebook_count,
            "visualized_imgs": res.get("visualized_images"),
            "gemini_json": res.get("gemini_json"),
        }, indent=2))
