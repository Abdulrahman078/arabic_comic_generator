"""Renders Arabic text into YOLO-detected speech bubbles on panel images."""
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any

from src.utils.schemas import Bubble
from src.utils.logger import step
from src.panel.text_bubble.text import fit_text_in_box
from src.panel.text_bubble.bubble_detector import detect_bubbles_in_panel


def _draw_text_centered(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[int, int, int, int],
    lines: List[str],
    font: ImageFont.FreeTypeFont,
) -> None:
    """Draws text centered within a bounding box."""
    x1, y1, x2, y2 = bbox
    box_w = x2 - x1
    box_h = y2 - y1

    padding = max(6, int(min(box_w, box_h) * 0.06))
    inner_x1 = x1 + padding
    inner_y1 = y1 + padding
    inner_x2 = x2 - padding
    inner_y2 = y2 - padding

    line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    gap = int(line_h * 0.3)
    total_h = line_h * len(lines) + gap * (len(lines) - 1)

    start_y = inner_y1 + max(0, (inner_y2 - inner_y1 - total_h) // 2)

    for i, ln in enumerate(lines):
        w = draw.textlength(ln, font=font)
        x = inner_x1 + max(0, (inner_x2 - inner_x1 - int(w)) // 2)
        y = start_y + i * (line_h + gap)
        draw.text((x, y), ln, font=font, fill="black")


def render_panel_with_bubbles(
    panel_img: Image.Image,
    dialogue: List[Dict[str, Any]],
    font_path: str,
) -> Image.Image:
    """
    Uses YOLO to detect speech bubbles, then overlays Arabic text into each region.
    If no bubbles are detected, the panel is returned unchanged.
    """
    img = panel_img.copy()
    draw = ImageDraw.Draw(img)

    step("Detecting bubbles with YOLO...")
    detected_bboxes = detect_bubbles_in_panel(img)

    if len(detected_bboxes) == 0 or len(dialogue) == 0:
        if len(detected_bboxes) == 0 and len(dialogue) > 0:
            step("No bubbles detected — leaving panel unchanged (no manual overlays)")
        return img

    num_to_fill = min(len(detected_bboxes), len(dialogue))
    step(f"Using {num_to_fill} YOLO-detected bubbles")

    for i in range(num_to_fill):
        d = dialogue[i]
        bbox = detected_bboxes[i]
        b = Bubble(
            bbox=bbox,
            bubble_type=d["bubble_type"],
            speaker=d["speaker"],
            text_ar=d["text_ar"],
        )
        font, lines = fit_text_in_box(draw, b.text_ar, b.bbox, font_path)
        _draw_text_centered(draw, b.bbox, lines, font)

    return img
