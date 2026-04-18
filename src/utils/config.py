"""Central configuration: API keys from environment; everything else is fixed here."""

import os
from dotenv import load_dotenv

load_dotenv()

# Only secrets from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# OpenAI: ComicScript JSON (text)
LLM_MODEL = "gpt-5.4-nano-2026-03-17"


def llm_temperature() -> float:
    """Sampling temperature for chat completions.

    GPT-5 family models (via LiteLLM/DSPy) do not support ``temperature=0``; only ``1`` is
    accepted for many variants. See LiteLLM ``UnsupportedParamsError`` for ``gpt-5*`` models.
    """
    m = (LLM_MODEL or "").lower()
    if "gpt-5" in m:
        return 1.0
    return 0.0

# Gemini: panel images only
GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
# HTTP timeout in milliseconds for google-genai (also sets X-Server-Timeout for long image jobs).
GEMINI_HTTP_TIMEOUT_MS = 20 * 60 * 1000
# Priority tier for image generate_content: often shorter queue vs default (billing may differ). Set 0 to disable.
GEMINI_PRIORITY_IMAGE_TIER = os.getenv("GEMINI_PRIORITY_IMAGE_TIER", "1").lower() in (
    "1",
    "true",
    "yes",
)

STYLE_LOCK = (
    "black and white manga, screentone, high contrast, clean ink lines"
)

ENABLE_CACHE = True

# ComicScript: use DSPy (`dspy.Predict` + same prompts as `script_prompts`) when true; else raw OpenAI client.
USE_DSPY_FOR_SCRIPT = os.getenv("COMIC_USE_DSPY", "0").lower() in ("1", "true", "yes")

# Optional: path to a program saved with `dspy` after `BootstrapFewShot` / other teleprompters (`program.save(...)`).
DSPY_OPTIMIZED_PROGRAM_PATH = (os.getenv("DSPY_COMIC_PROGRAM_PATH") or "").strip() or None
