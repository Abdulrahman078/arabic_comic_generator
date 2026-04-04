"""Central configuration: API keys from environment; everything else is fixed here."""

import os
from dotenv import load_dotenv

load_dotenv()

# Only secrets from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# OpenAI: ComicScript JSON (text)
LLM_MODEL = "gpt-5.4-nano-2026-03-17"

# Gemini: panel images only
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"

# YOLO bubble detection: lower = more detections (may include false positives)
YOLO_CONF_PRIMARY = 0.15
YOLO_CONF_FALLBACK = 0.06

# Font: amiri | cairo | noto_naskh
FONT_PREFERENCE = "amiri"
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

STYLE_LOCK = (
    "black and white manga, screentone, high contrast, clean ink lines"
)

ENABLE_CACHE = True
