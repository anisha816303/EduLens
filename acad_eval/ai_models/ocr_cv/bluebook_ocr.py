from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

import numpy as np
from PIL import Image
import easyocr


@dataclass
class BluebookResult:
    usn: Optional[str]
    course_code: Optional[str]
    course_name: Optional[str]
    marks_obtained: Optional[int]
    raw_text: str
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2] in original image coords

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BluebookOCRExtractor:
    """OCR logic for a single cropped Bluebook image, using EasyOCR."""

    def __init__(self):
        # GPU=False so it works on any Windows CPU
        self.reader = easyocr.Reader(["en"], gpu=False)

    # ---------- PUBLIC API ----------

    def extract_from_pil(self, img: Image.Image, bbox=None) -> BluebookResult:
        img = img.convert("RGB")

        # 1. Try 4 orientations and pick the one with most readable text
        upright = self._best_orientation(img)

        # 2. OCR on chosen orientation
        results = self.reader.readtext(np.array(upright))
        # results: list of [bbox, text, confidence]
        text_lines = [r[1] for r in results]
        full_text = "\n".join(text_lines)

        return BluebookResult(
            usn=self._extract_usn(full_text),
            course_code=self._extract_course_code(full_text),
            course_name=self._extract_course_name(full_text),
            marks_obtained=self._extract_marks(full_text),
            raw_text=full_text,
            bbox=bbox,
        )

    # ---------- ORIENTATION ----------

    def _best_orientation(self, img: Image.Image) -> Image.Image:
        """
        Try 0, 90, 180, 270 degrees and pick the orientation that gives
        the highest 'score' = sum(len(text) * confidence).
        """
        best_img = img
        best_score = -1

        for angle in (0, 90, 180, 270):
            rotated = img.rotate(angle, expand=True)
            try:
                results = self.reader.readtext(np.array(rotated))
                score = sum(len(r[1]) * float(r[2]) for r in results)
                if score > best_score:
                    best_score = score
                    best_img = rotated
            except Exception:
                continue

        return best_img

    # ---------- FIELD PARSERS ----------

    def _extract_usn(self, text: str) -> Optional[str]:
        """
        Strong preference: pattern 1MS22CSxxx (your batch).
        Fallback: generic 'USN: <token>'.
        """
        # normalize to only A–Z, 0–9
        norm = re.sub(r"[^A-Z0-9]", "", text.upper())

        # 1) Exact batch pattern
        m = re.search(r"1MS22CS[0-9]{3}", norm)
        if m:
            return m.group(0)

        # 2) Fallback: look near 'USN'
        t = " ".join(text.split())
        m2 = re.search(r"USN[:\s]+([A-Za-z0-9]+)", t, re.IGNORECASE)
        if m2:
            return m2.group(1).upper()

        return None

    def _extract_course_code(self, text: str) -> Optional[str]:
        """
        Try to find course code near 'COURSE CODE'.
        Pattern: AA123, CS52, AI52A, etc.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for i, ln in enumerate(lines):
            if "COURSE CODE" in ln.upper():
                window = ln
                if i + 1 < len(lines):
                    window += " " + lines[i + 1]
                if i + 2 < len(lines):
                    window += " " + lines[i + 2]

                window = " ".join(window.split())
                m = re.search(r"\b([A-Z]{2,4}\d{2,3}[A-Z]?)\b", window)
                if m:
                    return m.group(1).upper()

        # fallback: anywhere in the text
        t = " ".join(text.split())
        m2 = re.search(r"\b([A-Z]{2,4}\d{2,3}[A-Z]?)\b", t)
        return m2.group(1).upper() if m2 else None

    def _extract_course_name(self, text: str) -> Optional[str]:
        """
        Extract course name from the 'COURSE CODE & NAME' line and its
        following 1–2 lines, after removing label + course code.
        """
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        for i, ln in enumerate(lines):
            if "COURSE CODE" in ln.upper():
                window_lines = [ln]
                if i + 1 < len(lines):
                    window_lines.append(lines[i + 1])
                if i + 2 < len(lines):
                    window_lines.append(lines[i + 2])

                window = " ".join(window_lines)

                # Remove label
                window = re.sub(
                    r"COURSE CODE[^:]*[:\-]?", "", window, flags=re.IGNORECASE
                )

                # Remove any obvious code-like token
                window = re.sub(r"\b[A-Z]{2,4}\d{2,3}[A-Z]?\b", "", window)

                name = window.strip(" :-")
                if name:
                    return name

        return None

    def _extract_marks(self, text: str) -> Optional[int]:
        """
        Extract marks (assumed out of 30):
        - Grab all 1–2 digit numbers
        - Filter 0–30
        - Take max as 'marks obtained'
        """
        nums = [int(m) for m in re.findall(r"\b\d{1,2}\b", text)]
        valid = [n for n in nums if 0 <= n <= 30]
        return max(valid) if valid else None
