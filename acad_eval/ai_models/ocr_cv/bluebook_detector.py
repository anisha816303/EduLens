# acad_eval/ai_models/ocr_cv/bluebook_detector.py

import os
from typing import List, Tuple
from PIL import Image
from ultralytics import YOLO


class BluebookDetector:
    """YOLO detector. If weights not found -> fallback to full image."""

    def __init__(self):
        here = os.path.dirname(__file__)
        self.weights = os.path.join(here, "weights", "bluebook_yolo.pt")

        if os.path.exists(self.weights):
            self.yolo = YOLO(self.weights)
        else:
            self.yolo = None  # fallback mode

    def crop_bluebooks(self, image_path: str) -> List[Tuple[Image.Image, List[float]]]:
        img = Image.open(image_path).convert("RGB")
        W, H = img.size

        # NO YOLO → fallback
        if self.yolo is None:
            return [(img, [0, 0, W, H])]

        # YOLO DETECTION
        results = self.yolo.predict(image_path, conf=0.4, iou=0.5, verbose=False)
        boxes = results[0].boxes.xyxy.cpu().numpy() if results else []

        if len(boxes) == 0:
            return [(img, [0, 0, W, H])]

        output = []
        for x1, y1, x2, y2 in boxes:
            crop = img.crop((int(x1), int(y1), int(x2), int(y2)))
            output.append((crop, [float(x1), float(y1), float(x2), float(y2)]))
        return output
