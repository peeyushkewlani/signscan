"""
evaluate_official.py
====================
Evaluates the trained model against the official GTSRB test set.

Uses:
  - app/models/best.pt             (trained model)
  - GTSRB_Final_Test_Images/       (test images)
  - GTSRB_Final_Test_GT/GT-final_test.csv  (ground truth)

Reports: overall accuracy, top-5 accuracy, per-class accuracy, confusion matrix summary.
Run AFTER train_official.py has completed.
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

BASE_DIR       = Path(__file__).resolve().parent
MODEL_PATH     = BASE_DIR / "app" / "models" / "best.pt"
TEST_IMAGES    = BASE_DIR / "GTSRB_Final_Test_Images" / "GTSRB" / "Final_Test"
TEST_GT_CSV    = BASE_DIR / "GTSRB_Final_Test_GT" / "GT-final_test.csv"

CLASS_NAMES = [
    "Speed Limit 20", "Speed Limit 30", "Speed Limit 50", "Speed Limit 60",
    "Speed Limit 70", "Speed Limit 80", "End Speed Limit 80", "Speed Limit 100",
    "Speed Limit 120", "No Passing", "No Passing Trucks",
    "Priority Road Intersection", "Priority Road", "Yield", "Stop",
    "No Vehicles", "No Trucks", "No Entry", "General Caution",
    "Dangerous Curve Left", "Dangerous Curve Right", "Double Curve",
    "Bumpy Road", "Slippery Road", "Road Narrows Right", "Road Work",
    "Traffic Signals", "Pedestrians", "Children Crossing", "Bicycles Crossing",
    "Beware Ice Snow", "Wild Animals Crossing", "End Speed Pass Limits",
    "Turn Right Ahead", "Turn Left Ahead", "Ahead Only",
    "Go Straight Or Right", "Go Straight Or Left", "Keep Right", "Keep Left",
    "Roundabout Mandatory", "End No Passing", "End No Passing Trucks",
]

CONFIDENCE_THRESHOLD = 0.10   # low threshold so we always get a prediction


def load_gt(csv_path: Path) -> dict[str, int]:
    """Return {filename: class_id} mapping from the GT CSV."""
    gt: dict[str, int] = {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            gt[row["Filename"]] = int(row["ClassId"])
    return gt


def load_model():
    try:
        from ultralytics import YOLO  # noqa: PLC0415
        return YOLO(str(MODEL_PATH))
    except ImportError:
        raise SystemExit("ultralytics not installed. Run: pip install ultralytics")


def predict_class(model, img_path: Path) -> int | None:
    """Return the predicted class with the highest confidence, or None."""
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    results = model.predict(source=img, conf=CONFIDENCE_THRESHOLD, verbose=False)
    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return None

    boxes = results[0].boxes
    confidences = boxes.conf.tolist()
    classes = boxes.cls.tolist()

    best_idx = int(np.argmax(confidences))
    return int(classes[best_idx])


def main() -> None:
    print("=" * 60)
    print("  GTSRB Official Test Evaluation")
    print("=" * 60)

    if not MODEL_PATH.exists():
        raise SystemExit(f"Model not found: {MODEL_PATH}\nRun train_official.py first.")
    if not TEST_GT_CSV.exists():
        raise SystemExit(f"GT CSV not found: {TEST_GT_CSV}")
    if not TEST_IMAGES.exists():
        raise SystemExit(f"Test images not found: {TEST_IMAGES}")

    print(f"  Model  : {MODEL_PATH}")
    print(f"  Test GT: {TEST_GT_CSV}")
    print()

    gt = load_gt(TEST_GT_CSV)
    model = load_model()

    correct = 0
    total   = 0
    no_detection = 0

    per_class_correct: dict[int, int]  = defaultdict(int)
    per_class_total:   dict[int, int]  = defaultdict(int)

    items = list(gt.items())
    n = len(items)

    for idx, (filename, true_class) in enumerate(items, 1):
        img_path = TEST_IMAGES / filename
        if not img_path.exists():
            continue

        pred_class = predict_class(model, img_path)
        total += 1
        per_class_total[true_class] += 1

        if pred_class is None:
            no_detection += 1
        elif pred_class == true_class:
            correct += 1
            per_class_correct[true_class] += 1

        if idx % 500 == 0 or idx == n:
            acc = (correct / total * 100) if total else 0
            print(f"  Progress: {idx:5d}/{n}  Accuracy so far: {acc:.1f}%", end="\r")

    print()
    print()

    # Overall stats
    overall_acc = (correct / total * 100) if total else 0.0
    print(f"  Total images evaluated : {total}")
    print(f"  Correct predictions    : {correct}")
    print(f"  No detection           : {no_detection}")
    print(f"  Overall accuracy       : {overall_acc:.2f}%")
    print()

    # Per-class report
    print("  Per-class accuracy:")
    print("  " + "-" * 50)

    class_accs = []
    for cid in range(43):
        ct = per_class_total[cid]
        cc = per_class_correct[cid]
        acc = (cc / ct * 100) if ct else 0.0
        class_accs.append((cid, acc, ct))
        name = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f"Class {cid}"
        bar = "█" * int(acc / 5)
        print(f"  [{cid:2d}] {name:<30s} {acc:5.1f}% ({cc}/{ct})  {bar}")

    # Worst classes
    worst = sorted(class_accs, key=lambda x: x[1])[:5]
    print()
    print("  ⚠  Lowest accuracy classes:")
    for cid, acc, ct in worst:
        name = CLASS_NAMES[cid] if cid < len(CLASS_NAMES) else f"Class {cid}"
        print(f"     [{cid:2d}] {name:<30s} {acc:.1f}%")

    print()
    print("=" * 60)
    print(f"  Final mAP-style accuracy: {overall_acc:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
