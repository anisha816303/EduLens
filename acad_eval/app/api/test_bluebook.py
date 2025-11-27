# acad_eval/app/api/test_bluebook.py

import sys, os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from ai_models.llm_evaluation.bluebook_extractor import extract_bluebook_data

IMAGE_PATH = r"C:\Users\Diya\EduLens\acad_eval\app\api\20241203_084647.jpg"

result = extract_bluebook_data(IMAGE_PATH)
print(result)
