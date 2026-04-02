"""Central configuration: API keys, model names, paths."""
import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# OpenAI (script generation + optional image generation)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_IMAGE_MODEL = "gpt-image-1"

# Gemini (panel image generation)
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# YOLO bubble detection: lower = more detections (may include false positives)
YOLO_CONF_PRIMARY = 0.15
YOLO_CONF_FALLBACK = 0.06

# Font: amiri (default), cairo, noto_naskh
FONT_PREFERENCE = os.getenv("FONT_PREFERENCE", "amiri").lower()
FONTS = {
    "amiri": (
        "https://github.com/google/fonts/raw/main/ofl/amiri/Amiri-Regular.ttf",
        "Amiri-Regular.ttf",
    ),
    "cairo": (
        "https://github.com/google/fonts/raw/main/ofl/cairo/Cairo-Regular.ttf",
        "Cairo-Regular.ttf",
    ),
    "noto_naskh": (
        "https://github.com/google/fonts/raw/main/ofl/notonaskharabic/NotoNaskhArabic-Regular.ttf",
        "NotoNaskhArabic-Regular.ttf",
    ),
}
FONT_URL, FONT_PATH = FONTS.get(FONT_PREFERENCE, FONTS["amiri"])

# Style lock: fixed suffix for consistent panel look (overridable via env)
STYLE_LOCK = os.getenv(
    "STYLE_LOCK",
    "black and white manga, screentone, high contrast, clean ink lines",
)
