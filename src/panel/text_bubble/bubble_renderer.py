"""Renders dialogue bubbles and Arabic text onto panel images. Draws bubbles ourselves — no YOLO."""
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict, Any

from src.utils.logger import step
from src.panel.text_bubble.text import fit_text_in_box
from src.panel.text_bubble.bubble_placer import compute_bubble_positions


def _draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[int, int, int, int],
    outline: str = "black",
    fill: str = "white",
    width: int = 2,
    radius: int = 12,
) -> None:
    """Draws a rounded rectangle (speech bubble shape)."""
    x1, y1, x2, y2 = bbox
    draw.rounded_rectangle(
        [x1, y1, x2, y2],
        radius=radius,
        outline=outline,
        fill=fill,
        width=width,
    )


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
    Draws bubbles at fixed positions and overlays Arabic text.
    No YOLO — full control over placement and rendering.
    """
    img = panel_img.copy()
    if not dialogue:
        return img

    w, h = img.size
    bboxes = compute_bubble_positions(w, h, len(dialogue))
    step(f"Drawing {len(bboxes)} bubbles at fixed positions")

    draw = ImageDraw.Draw(img)
    num_to_fill = min(len(bboxes), len(dialogue))

    for i in range(num_to_fill):
        d = dialogue[i]
        bbox = bboxes[i]
        _draw_rounded_rect(draw, bbox)
        font, lines = fit_text_in_box(draw, d["text_ar"], bbox, font_path)
        _draw_text_centered(draw, bbox, lines, font)

    return img
