# acad_eval/ai_models/llm_evaluation/bluebook_extractor.py

"""
YOLO + OCR based bluebook extractor.

Public API:

    extract_bluebook_data(image_path: str) -> Dict[str, Any]

Return format:

{
  "bluebooks": [
    {
      "usn": "...",
      "course_code": "...",
      "course_name": "...",
      "marks_obtained": 30,
      "raw_text": "...",
      "bbox": [x1, y1, x2, y2]
    },
    ...
  ]
}
"""

from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path

# NOTE: project root on sys.path is `acad_eval`,
# so top-level packages are `ai_models`, `app`, etc.
from ai_models.yolo_pipeline.pipeline import run_pipeline_and_call_gemini

# --- Constants ---
# Get the project root directory (the parent of 'acad_eval')
PROJECT_ROOT = Path(__file__).resolve().parents[3]
YOLO_WEIGHTS_PATH = PROJECT_ROOT / "acad_eval" / "ai_models" / "yolo_pipeline" / "weights" / "best.pt"
OUTPUT_DIR = PROJECT_ROOT / "outputs"


def extract_bluebook_data(image_path: str) -> Dict[str, Any]:
    """
    High-level entry point used by the rest of the project.

    - Runs the YOLOv8 + Gemini pipeline.
    - Returns the extracted data in the format expected by the application.
    """
    if not YOLO_WEIGHTS_PATH.exists():
        raise FileNotFoundError(f"YOLO weights not found at {YOLO_WEIGHTS_PATH}")

    # Ensure the output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Call the new pipeline
    pipeline_result = run_pipeline_and_call_gemini(
        image_path=image_path,
        model_path=str(YOLO_WEIGHTS_PATH),
        output_project=str(OUTPUT_DIR)
    )

    # The pipeline already returns data in the desired format.
    # If the key is "gemini_result", we use that.
    if "gemini_result" in pipeline_result:
        return pipeline_result["gemini_result"]
    
    # Fallback if the structure is different
    return pipeline_result
