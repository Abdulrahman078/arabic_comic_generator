"""Detects speech bubbles in comic panels using YOLO."""
import os
from typing import List, Tuple

from PIL import Image

from src.utils.config import YOLO_CONF_FALLBACK, YOLO_CONF_PRIMARY

IOU_THRESHOLD = 0.8


def _get_model_path() -> str:
    """Downloads the YOLO model from Hugging Face if not cached."""
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download(
            repo_id="ogkalu/comic-speech-bubble-detector-yolov8m",
            filename="comic-speech-bubble-detector.pt",
        )
    except Exception as e:
        fallback = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "models", "comic-speech-bubble-detector.pt"
        )
        if os.path.exists(fallback):
            return fallback
        raise RuntimeError(
            "Could not load bubble detector model. Install: pip install ultralytics huggingface_hub. "
            f"Error: {e}"
        ) from e


def _run_detection(model, img_source, conf: float) -> List[Tuple[int, int, int, int]]:
    """Run YOLO predict and extract clamped bboxes."""
    results = model.predict(
        img_source,
        imgsz=1024,
        conf=conf,
        iou=IOU_THRESHOLD,
        verbose=False,
    )
    if not results or len(results) == 0:
        return []
    boxes = results[0].boxes
    if boxes is None or len(boxes) == 0:
        return []
    h, w = results[0].orig_shape[:2]
    xyxy = boxes.xyxy.cpu().numpy()
    bboxes = []
    for row in xyxy:
        x1, y1, x2, y2 = row
        x1 = max(0, min(int(x1), w - 1))
        y1 = max(0, min(int(y1), h - 1))
        x2 = max(x1 + 1, min(int(x2), w))
        y2 = max(y1 + 1, min(int(y2), h))
        if x2 > x1 and y2 > y1:
            area = (x2 - x1) * (y2 - y1)
            if area >= 800:
                bboxes.append((x1, y1, x2, y2))
    bboxes.sort(key=lambda b: (b[1], b[0]))
    return bboxes


def detect_bubbles_in_panel(panel_img: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    Uses YOLO to detect speech bubbles in a comic panel.
    Returns list of (x1, y1, x2, y2) bounding boxes.
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        return []

    model_path = _get_model_path()
    model = YOLO(model_path)

    bboxes = _run_detection(model, panel_img, YOLO_CONF_PRIMARY)
    if len(bboxes) == 0:
        bboxes = _run_detection(model, panel_img, YOLO_CONF_FALLBACK)

    return bboxes
