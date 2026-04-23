"""YOLOv8 and Tesseract inference pipeline."""

from __future__ import annotations

import base64
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

try:
    import pytesseract
except ImportError:
    pytesseract = None

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "best.pt"
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE", "0.25"))

CLASS_NAMES = {
    0: "Speed Limit 20",
    1: "Speed Limit 30",
    2: "Speed Limit 50",
    3: "Speed Limit 60",
    4: "Speed Limit 70",
    5: "Speed Limit 80",
    6: "End Speed Limit 80",
    7: "Speed Limit 100",
    8: "Speed Limit 120",
    9: "No Passing",
    10: "No Passing Trucks",
    11: "Priority Road Intersection",
    12: "Priority Road",
    13: "Yield",
    14: "Stop",
    15: "No Vehicles",
    16: "No Trucks",
    17: "No Entry",
    18: "General Caution",
    19: "Dangerous Curve Left",
    20: "Dangerous Curve Right",
    21: "Double Curve",
    22: "Bumpy Road",
    23: "Slippery Road",
    24: "Road Narrows Right",
    25: "Road Work",
    26: "Traffic Signals",
    27: "Pedestrians",
    28: "Children Crossing",
    29: "Bicycles Crossing",
    30: "Beware Ice Snow",
    31: "Wild Animals Crossing",
    32: "End Speed Pass Limits",
    33: "Turn Right Ahead",
    34: "Turn Left Ahead",
    35: "Ahead Only",
    36: "Go Straight Or Right",
    37: "Go Straight Or Left",
    38: "Keep Right",
    39: "Keep Left",
    40: "Roundabout Mandatory",
    41: "End No Passing",
    42: "End No Passing Trucks",
}

BOX_COLORS = [
    (45, 212, 191),
    (59, 130, 246),
    (251, 191, 36),
    (244, 114, 182),
    (163, 230, 53),
    (249, 115, 22),
]


def humanize_label(value: str) -> str:
    value = value.replace("_", " ").replace("-", " ").strip()
    value = re.sub(r"\s+", " ", value)
    return value.title()


def resolve_tesseract_runtime() -> tuple[bool, str, str | None]:
    """Return OCR availability, a status message, and the executable path."""
    if pytesseract is None:
        return False, "pytesseract is not installed in the current Python environment.", None

    candidate_paths = [
        os.getenv("TESSERACT_CMD"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]

    for candidate in candidate_paths:
        if not candidate:
            continue

        candidate_path = Path(candidate)
        if not candidate_path.exists():
            continue

        try:
            pytesseract.pytesseract.tesseract_cmd = str(candidate_path)
            _ = pytesseract.get_tesseract_version()
            return True, f"Tesseract is available at {candidate_path}.", str(candidate_path)
        except Exception:
            continue

    return (
        False,
        "Tesseract executable not found. Install Tesseract locally or set TESSERACT_CMD.",
        None,
    )


class SignDetector:
    """Run detection, OCR, and image annotation for uploaded sign images."""

    def __init__(self, model_path: str | Path = MODEL_PATH):
        self.model_path = Path(model_path)
        self.model: YOLO | None = None
        self.class_names = CLASS_NAMES.copy()
        self.ocr_available, self.ocr_message, self.tesseract_cmd = resolve_tesseract_runtime()
        self._load_model()

    def _load_model(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {self.model_path}. Put best.pt inside app/models/."
            )

        print(f"[INFO] Loading YOLO model from {self.model_path}")
        self.model = YOLO(str(self.model_path))

        model_names = getattr(self.model, "names", None)
        if isinstance(model_names, dict) and model_names:
            self.class_names = {
                int(class_id): humanize_label(str(label))
                for class_id, label in model_names.items()
            }

        print(f"[INFO] Model loaded with {len(self.class_names)} classes.")

    def _get_box_color(self, class_id: int) -> tuple[int, int, int]:
        return BOX_COLORS[class_id % len(BOX_COLORS)]

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r"[^A-Za-z0-9/\- ]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _ensure_region_bounds(
        image: np.ndarray, bbox: list[float], padding_ratio: float = 0.1
    ) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = [int(value) for value in bbox]
        image_height, image_width = image.shape[:2]
        pad_x = int((x2 - x1) * padding_ratio)
        pad_y = int((y2 - y1) * padding_ratio)
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(image_width, x2 + pad_x)
        y2 = min(image_height, y2 + pad_y)
        return x1, y1, x2, y2

    def _prepare_ocr_variants(self, region: np.ndarray) -> list[np.ndarray]:
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 5, 75, 75)

        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )

        return [gray, otsu, cv2.bitwise_not(otsu), adaptive]

    def _extract_text_from_region(self, image: np.ndarray, bbox: list[float]) -> str:
        if not self.ocr_available or pytesseract is None:
            return ""

        try:
            x1, y1, x2, y2 = self._ensure_region_bounds(image, bbox)
            region = image[y1:y2, x1:x2]
            if region.size == 0:
                return ""

            min_dimension = min(region.shape[:2])
            if min_dimension < 80:
                scale = 80 / max(1, min_dimension)
                region = cv2.resize(
                    region,
                    None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_CUBIC,
                )

            best_text = ""
            configs = [
                "--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
                "--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-",
            ]

            for prepared_region in self._prepare_ocr_variants(region):
                for config in configs:
                    text = self._clean_text(
                        pytesseract.image_to_string(prepared_region, config=config)
                    )
                    if len(text) > len(best_text):
                        best_text = text

            return best_text
        except Exception as exc:
            print(f"[WARNING] Region OCR failed: {exc}")
            return ""

    def _run_global_ocr(self, image: np.ndarray) -> str:
        if not self.ocr_available or pytesseract is None:
            return ""

        try:
            max_side = max(image.shape[:2])
            scale = 1200 / max_side if max_side < 1200 else 1.0
            working_image = image
            if scale > 1:
                working_image = cv2.resize(
                    image,
                    None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_CUBIC,
                )

            gray = cv2.cvtColor(working_image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            text = pytesseract.image_to_string(thresh, config="--psm 11 --oem 3")
            return self._clean_text(text)
        except Exception as exc:
            print(f"[WARNING] Global OCR failed: {exc}")
            return ""

    def _annotate_image(
        self, image: np.ndarray, detections: list[dict[str, Any]]
    ) -> np.ndarray:
        annotated = image.copy()

        for detection in detections:
            x1, y1, x2, y2 = [int(value) for value in detection["bbox"]]
            color = self._get_box_color(detection["class_id"])
            label = f"{detection['class_name']} {detection['confidence']:.0%}"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

            (label_width, label_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
            )
            text_top = max(label_height + baseline + 6, y1)
            cv2.rectangle(
                annotated,
                (x1, text_top - label_height - baseline - 8),
                (x1 + label_width + 10, text_top),
                color,
                -1,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 5, text_top - 6),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (8, 15, 24),
                2,
                lineType=cv2.LINE_AA,
            )

        return annotated

    @staticmethod
    def _image_to_data_url(image: np.ndarray) -> str:
        success, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not success:
            raise ValueError("Failed to encode the image result.")
        encoded = base64.b64encode(buffer).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    @staticmethod
    def _summarize_text(detections: list[dict[str, Any]], global_text: str) -> str:
        detected_text = []
        for detection in detections:
            extracted_text = detection.get("extracted_text", "").strip()
            if extracted_text and extracted_text not in detected_text:
                detected_text.append(extracted_text)

        if detected_text:
            return " | ".join(detected_text)
        return global_text

    def analyze(self, image_path: str | Path, confidence_threshold: float | None = None) -> dict[str, Any]:
        if self.model is None:
            raise RuntimeError("YOLO model is not loaded.")

        start_time = time.perf_counter()
        image_path = Path(image_path)
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        conf = confidence_threshold if confidence_threshold is not None else CONFIDENCE_THRESHOLD
        prediction = self.model.predict(
            source=image,
            conf=conf,
            verbose=False,
        )[0]

        detections: list[dict[str, Any]] = []
        if prediction.boxes is not None:
            for box in prediction.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = [round(float(value), 1) for value in box.xyxy[0].tolist()]
                extracted_text = self._extract_text_from_region(image, bbox)

                detections.append(
                    {
                        "class_id": class_id,
                        "class_name": self.class_names.get(class_id, f"Class {class_id}"),
                        "confidence": round(confidence, 4),
                        "bbox": bbox,
                        "extracted_text": extracted_text,
                    }
                )

        detections.sort(key=lambda item: item["confidence"], reverse=True)

        global_text = self._run_global_ocr(image)
        extracted_text = self._summarize_text(detections, global_text)
        annotated_image = self._annotate_image(image, detections)
        processing_time = round(time.perf_counter() - start_time, 3)
        average_confidence = (
            round(sum(item["confidence"] for item in detections) / len(detections), 4)
            if detections
            else 0.0
        )

        return {
            "detections": detections,
            "total_detections": len(detections),
            "avg_confidence": average_confidence,
            "extracted_text": extracted_text,
            "global_text": global_text,
            "annotated_image": self._image_to_data_url(annotated_image),
            "original_image": self._image_to_data_url(image),
            "processing_time": processing_time,
            "image_size": {
                "width": int(image.shape[1]),
                "height": int(image.shape[0]),
            },
            "ocr": {
                "enabled": self.ocr_available,
                "message": self.ocr_message,
            },
        }
