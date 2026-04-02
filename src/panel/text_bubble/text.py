"""Arabic text shaping, font download, and text fitting for bubbles."""
import os
import requests
import arabic_reshaper
from bidi.algorithm import get_display
from PIL import ImageFont, ImageDraw
from typing import List, Tuple

from src.utils.config import FONTS, FONT_PREFERENCE, FONT_URL, FONT_PATH
from src.utils.logger import step

# Fallback order: preferred → amiri → cairo → noto_naskh
_FONT_ORDER = ["amiri", "cairo", "noto_naskh"]


def _font_priority() -> List[Tuple[str, str, str]]:
    """Returns (name, url, path) in priority order."""
    order = [FONT_PREFERENCE] + [f for f in _FONT_ORDER if f != FONT_PREFERENCE]
    return [(name, FONTS[name][0], FONTS[name][1]) for name in order if name in FONTS]


def get_font_path() -> str:
    """Returns path to first available font (preferred or fallback)."""
    for _name, url, path in _font_priority():
        if os.path.exists(path):
            return path
    return FONT_PATH


def download_font() -> None:
    """Downloads Arabic font(s) — preferred first, then fallbacks until one succeeds."""
    for name, url, path in _font_priority():
        if os.path.exists(path):
            return
        try:
            step(f"Downloading font {name} from {url}...")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            step(f"Font saved to: {path}")
            return
        except Exception as e:
            step(f"Font {name} failed: {e}, trying fallback...")
    raise RuntimeError("Could not download any Arabic font")


def shape_arabic(text: str) -> str:
    """Shapes Arabic correctly and applies bidi reordering for display."""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def wrap_text_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """Greedy word wrap for shaped (display) text."""
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text_in_box(
    draw: ImageDraw.ImageDraw,
    text_ar: str,
    bbox: Tuple[int, int, int, int],
    font_path: str,
) -> Tuple[ImageFont.FreeTypeFont, List[str]]:
    """Chooses the largest font size that fits shaped Arabic text inside bbox."""
    x1, y1, x2, y2 = bbox
    box_w = x2 - x1
    box_h = y2 - y1

    padding = max(8, int(min(box_w, box_h) * 0.06))
    max_w = box_w - 2 * padding
    max_h = box_h - 2 * padding

    shaped = shape_arabic(text_ar)

    for font_size in range(120, 10, -4):
        font = ImageFont.truetype(font_path, font_size)
        lines = wrap_text_to_width(draw, shaped, font, max_w)

        line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
        line_h = int(line_h * 1.15)
        gap = int(line_h * 0.25)
        total_h = line_h * len(lines) + gap * max(0, len(lines) - 1)

        widest = 0
        for ln in lines:
            widest = max(widest, draw.textlength(ln, font=font))

        if widest <= max_w and total_h <= max_h * 0.95:
            return font, lines

    font = ImageFont.truetype(font_path, 24)
    lines = wrap_text_to_width(draw, shape_arabic(text_ar), font, max_w)
    return font, lines
