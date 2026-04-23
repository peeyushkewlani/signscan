"""
train_official.py
=================
Builds a YOLO-format dataset from the three official GTSRB archives and
trains YOLOv8n for 30 epochs at 224×224 resolution (v3 — high-accuracy run).

Datasets used:
  - GTSRB_Final_Training_Images/GTSRB/Final_Training/Images/   (43 classes, ~39k PPM images)
  - GTSRB_Final_Test_Images/GTSRB/Final_Test/                  (PPM images, unlabelled)
  - GTSRB_Final_Test_GT/GT-final_test.csv                      (ground-truth for test set)

Output:
  - datasets/gtsrb/  (fresh YOLO dataset)
  - app/models/best.pt  (overwritten with the new trained model)
  - training.log  (full progress log)
"""

from __future__ import annotations

import csv
import logging
import random
import shutil
import sys
import time
from pathlib import Path

import cv2

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

TRAIN_IMAGES_ROOT = BASE_DIR / "GTSRB_Final_Training_Images" / "GTSRB" / "Final_Training" / "Images"
TEST_IMAGES_ROOT  = BASE_DIR / "GTSRB_Final_Test_Images" / "GTSRB" / "Final_Test" / "Images"
TEST_GT_CSV       = BASE_DIR / "GTSRB_Final_Test_GT" / "GT-final_test.csv"

DATASET_DIR       = BASE_DIR / "datasets" / "gtsrb"
YAML_PATH         = BASE_DIR / "gtsrb_yolo.yaml"
DEST_MODEL        = BASE_DIR / "app" / "models" / "best.pt"
LOG_FILE          = BASE_DIR / "training.log"

# ---------------------------------------------------------------------------
# Hyper-parameters
# ---------------------------------------------------------------------------
VAL_SPLIT   = 0.10   # fraction of training images used for validation
EPOCHS      = 30
BATCH       = 4      # 4 images/batch; safe for CPU at 224px (OOM risk at 8+)
IMG_SIZE    = 224    # 224px — essential for distinguishing similar speed-limit signs
SEED        = 42
RUN_NAME    = "gtsrb_official_v3"  # v3: 224px high-accuracy run
PROJECT_DIR = BASE_DIR / "runs" / "detect"  # absolute path avoids nested-dir bug

# ---------------------------------------------------------------------------
# Class names (43 GTSRB classes)
# ---------------------------------------------------------------------------
CLASS_NAMES = [
    "speed_limit_20", "speed_limit_30", "speed_limit_50", "speed_limit_60",
    "speed_limit_70", "speed_limit_80", "end_speed_limit_80", "speed_limit_100",
    "speed_limit_120", "no_passing", "no_passing_trucks",
    "priority_road_intersection", "priority_road", "yield", "stop",
    "no_vehicles", "no_trucks", "no_entry", "general_caution",
    "dangerous_curve_left", "dangerous_curve_right", "double_curve",
    "bumpy_road", "slippery_road", "road_narrows_right", "road_work",
    "traffic_signals", "pedestrians", "children_crossing", "bicycles_crossing",
    "beware_ice_snow", "wild_animals_crossing", "end_speed_pass_limits",
    "turn_right_ahead", "turn_left_ahead", "ahead_only",
    "go_straight_or_right", "go_straight_or_left", "keep_right", "keep_left",
    "roundabout_mandatory", "end_no_passing", "end_no_passing_trucks",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ppm_to_jpeg(src: Path, dst: Path) -> bool:
    """Convert a PPM image to JPEG. Returns True on success."""
    img = cv2.imread(str(src))
    if img is None:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    return cv2.imwrite(str(dst), img, [cv2.IMWRITE_JPEG_QUALITY, 92])


def _yolo_bbox(img_w: int, img_h: int, x1: int, y1: int, x2: int, y2: int) -> str:
    """Return a YOLO-format bounding box string (cx cy w h, all 0-1)."""
    cx = ((x1 + x2) / 2) / img_w
    cy = ((y1 + y2) / 2) / img_h
    bw = (x2 - x1) / img_w
    bh = (y2 - y1) / img_h
    cx, cy, bw, bh = (max(0.0, min(1.0, v)) for v in (cx, cy, bw, bh))
    return f"{cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}"


def _write_label(label_path: Path, class_id: int, bbox_str: str) -> None:
    label_path.parent.mkdir(parents=True, exist_ok=True)
    label_path.write_text(f"{class_id} {bbox_str}\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Step 1 – Prerequisites check
# ---------------------------------------------------------------------------

def check_prerequisites(skip_data: bool = False) -> None:
    log.info("=== Checking prerequisites ===")

    if skip_data:
        # Only verify the converted dataset exists
        if not DATASET_DIR.exists():
            raise SystemExit(f"Dataset not found at {DATASET_DIR}. Run without --skip-data first.")
        n_train = len(list((DATASET_DIR / "images" / "train").glob("*.jpg")))
        log.info("  --skip-data: dataset found (%d train images)", n_train)
        return

    # Full check: raw source files must exist
    missing = []
    for p in (TRAIN_IMAGES_ROOT, TEST_IMAGES_ROOT, TEST_GT_CSV):
        if not p.exists():
            missing.append(str(p))

    if missing:
        for m in missing:
            log.error("  MISSING: %s", m)
        raise SystemExit("Prerequisites missing — aborting.")

    log.info("  Training images root : %s", TRAIN_IMAGES_ROOT)
    log.info("  Test images root     : %s", TEST_IMAGES_ROOT)
    log.info("  Test GT CSV          : %s", TEST_GT_CSV)

    class_dirs = sorted(TRAIN_IMAGES_ROOT.iterdir())
    log.info("  Class folders found  : %d", len(class_dirs))


# ---------------------------------------------------------------------------
# Step 2 – Clean & create dataset directories
# ---------------------------------------------------------------------------

def clean_dataset_dir() -> None:
    log.info("=== Cleaning dataset directory ===")
    if DATASET_DIR.exists():
        log.info("  Removing %s ...", DATASET_DIR)
        shutil.rmtree(DATASET_DIR)

    for split in ("train", "val", "test"):
        (DATASET_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    log.info("  Dataset directory created at %s", DATASET_DIR)


# ---------------------------------------------------------------------------
# Step 3 – Process training data  (→ train / val splits)
# ---------------------------------------------------------------------------

def process_training_data() -> dict[str, int]:
    log.info("=== Processing training data ===")
    random.seed(SEED)

    stats = {"train": 0, "val": 0, "skipped": 0}
    class_dirs = sorted(d for d in TRAIN_IMAGES_ROOT.iterdir() if d.is_dir())

    for class_dir in class_dirs:
        class_id = int(class_dir.name)
        csv_files = list(class_dir.glob("GT-*.csv"))

        if not csv_files:
            log.warning("  No GT CSV in %s — skipping", class_dir)
            continue

        gt_csv = csv_files[0]
        rows: list[dict] = []

        with gt_csv.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                rows.append(row)

        # Shuffle & split
        random.shuffle(rows)
        n_val = max(1, int(len(rows) * VAL_SPLIT))
        val_rows   = rows[:n_val]
        train_rows = rows[n_val:]

        for split, split_rows in (("train", train_rows), ("val", val_rows)):
            for row in split_rows:
                try:
                    src_ppm = class_dir / row["Filename"]
                    img_w   = int(row["Width"])
                    img_h   = int(row["Height"])
                    x1      = int(row["Roi.X1"])
                    y1      = int(row["Roi.Y1"])
                    x2      = int(row["Roi.X2"])
                    y2      = int(row["Roi.Y2"])

                    stem    = f"{class_id:05d}_{src_ppm.stem}"
                    dst_jpg = DATASET_DIR / "images" / split / f"{stem}.jpg"
                    dst_lbl = DATASET_DIR / "labels" / split / f"{stem}.txt"

                    if not _ppm_to_jpeg(src_ppm, dst_jpg):
                        stats["skipped"] += 1
                        continue

                    bbox_str = _yolo_bbox(img_w, img_h, x1, y1, x2, y2)
                    _write_label(dst_lbl, class_id, bbox_str)
                    stats[split] += 1

                except Exception as exc:
                    log.debug("  Row error: %s — %s", row, exc)
                    stats["skipped"] += 1

        log.info(
            "  Class %02d (%s): %d train + %d val",
            class_id, CLASS_NAMES[class_id], 
            sum(1 for r in train_rows), sum(1 for r in val_rows)
        )

    log.info(
        "  Training split total  : train=%d  val=%d  skipped=%d",
        stats["train"], stats["val"], stats["skipped"]
    )
    return stats


# ---------------------------------------------------------------------------
# Step 4 – Process official test data  (using GT-final_test.csv)
# ---------------------------------------------------------------------------

def process_test_data() -> dict[str, int]:
    log.info("=== Processing test data ===")
    stats = {"test": 0, "skipped": 0}

    with TEST_GT_CSV.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        rows = list(reader)

    log.info("  Test GT rows: %d", len(rows))

    for row in rows:
        try:
            filename = row["Filename"]
            img_w    = int(row["Width"])
            img_h    = int(row["Height"])
            x1       = int(row["Roi.X1"])
            y1       = int(row["Roi.Y1"])
            x2       = int(row["Roi.X2"])
            y2       = int(row["Roi.Y2"])
            class_id = int(row["ClassId"])

            src_ppm  = TEST_IMAGES_ROOT / filename
            stem     = Path(filename).stem
            dst_jpg  = DATASET_DIR / "images" / "test" / f"{stem}.jpg"
            dst_lbl  = DATASET_DIR / "labels" / "test" / f"{stem}.txt"

            if not src_ppm.exists():
                stats["skipped"] += 1
                continue

            if not _ppm_to_jpeg(src_ppm, dst_jpg):
                stats["skipped"] += 1
                continue

            bbox_str = _yolo_bbox(img_w, img_h, x1, y1, x2, y2)
            _write_label(dst_lbl, class_id, bbox_str)
            stats["test"] += 1

        except Exception as exc:
            log.debug("  Row error: %s — %s", row, exc)
            stats["skipped"] += 1

    log.info("  Test split total: test=%d  skipped=%d", stats["test"], stats["skipped"])
    return stats


# ---------------------------------------------------------------------------
# Step 5 – Write updated gtsrb_yolo.yaml
# ---------------------------------------------------------------------------

def write_yaml() -> None:
    log.info("=== Writing gtsrb_yolo.yaml ===")
    names_block = "\n".join(
        f"  {i}: \"{name}\"" for i, name in enumerate(CLASS_NAMES)
    )
    yaml_content = f"""\
# gtsrb_yolo.yaml — auto-generated by train_official.py
path: {DATASET_DIR.as_posix()}

train: images/train
val:   images/val
test:  images/test

nc: 43

names:
{names_block}
"""
    YAML_PATH.write_text(yaml_content, encoding="utf-8")
    log.info("  Saved to %s", YAML_PATH)


# ---------------------------------------------------------------------------
# Step 6 – Train YOLOv8n
# ---------------------------------------------------------------------------

def train_yolo() -> Path | None:
    log.info("=== Starting YOLOv8n training ===")
    log.info("  Epochs: %d | Batch: %d | ImgSize: %d", EPOCHS, BATCH, IMG_SIZE)

    try:
        from ultralytics import YOLO  # noqa: PLC0415
    except ImportError:
        raise SystemExit("ultralytics not installed. Run: pip install ultralytics")

    model = YOLO("yolov8n.pt")

    results = model.train(
        data=str(YAML_PATH),
        epochs=EPOCHS,
        batch=BATCH,
        imgsz=IMG_SIZE,
        optimizer="AdamW",
        cos_lr=True,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=3,
        patience=20,
        close_mosaic=5,       # disable mosaic in last 5 epochs for cleaner learning
        device="cpu",
        workers=0,
        project=str(PROJECT_DIR),   # absolute path — avoids nested-dir bug
        name=RUN_NAME,
        exist_ok=True,
        amp=False,
        cache=False,
        verbose=True,
        seed=SEED,
        augment=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,         # slightly more rotation for sign-face variance
        translate=0.12,
        scale=0.5,            # wider scale range helps small/large sign detection
        fliplr=0.0,           # traffic signs are NOT horizontally symmetric
        mosaic=1.0,
    )

    # Use YOLO's reported save_dir — avoids guessing the path
    save_dir = Path(results.save_dir)
    best_pt  = save_dir / "weights" / "best.pt"

    if not best_pt.exists():
        # Fallback: search under PROJECT_DIR
        candidates = list(PROJECT_DIR.rglob(f"{RUN_NAME}/weights/best.pt"))
        if candidates:
            best_pt = candidates[0]
        else:
            log.error("  best.pt not found. save_dir was: %s", save_dir)
            return None

    log.info("  Training complete. Best model: %s", best_pt)
    return best_pt


# ---------------------------------------------------------------------------
# Step 7 – Copy best.pt → app/models/best.pt
# ---------------------------------------------------------------------------

def deploy_model(best_pt: Path) -> None:
    log.info("=== Deploying model ===")
    DEST_MODEL.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_pt, DEST_MODEL)
    size_mb = DEST_MODEL.stat().st_size / (1024 * 1024)
    log.info("  Copied %s → %s (%.1f MB)", best_pt.name, DEST_MODEL, size_mb)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-data", action="store_true",
                        help="Skip dataset conversion (use existing datasets/gtsrb/).")
    args = parser.parse_args()

    t0 = time.perf_counter()
    log.info("=" * 42)
    log.info("   GTSRB Official Training Pipeline")
    log.info("=" * 42)
    log.info("Log file: %s", LOG_FILE)

    check_prerequisites(skip_data=args.skip_data)

    if args.skip_data:
        log.info("--skip-data set: reusing existing dataset at %s", DATASET_DIR)
        train_stats = {"train": "(existing)", "val": "(existing)", "skipped": 0}
        test_stats  = {"test": "(existing)", "skipped": 0}
        write_yaml()
    else:
        clean_dataset_dir()
        train_stats = process_training_data()
        test_stats  = process_test_data()
        write_yaml()

    best_pt = train_yolo()
    if best_pt:
        deploy_model(best_pt)
    else:
        log.error("Training did not produce a valid model — skipping deployment.")

    elapsed = time.perf_counter() - t0
    h, m = divmod(int(elapsed), 3600)
    m, s = divmod(m, 60)
    log.info("=== Done in %dh %dm %ds ===", h, m, s)
    log.info("Training set  : %d images", train_stats["train"])
    log.info("Validation set: %d images", train_stats["val"])
    log.info("Test set      : %d images", test_stats["test"])
    if best_pt:
        log.info("Deployed model: %s", DEST_MODEL)


if __name__ == "__main__":
    main()
