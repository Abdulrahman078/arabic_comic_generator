"""Model clients: OpenAI (script text) and Gemini (images only)."""
from typing import Any

from google.genai import types as genai_types

from src.utils.config import GEMINI_API_KEY, GEMINI_HTTP_TIMEOUT_MS, OPENAI_API_KEY

_gemini_client: Any = None


def load_openai_client() -> Any:
    """OpenAI client for ComicScript JSON generation."""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=OPENAI_API_KEY)


def load_gemini_client() -> Any:
    """Google Gemini client for panel image generation only (singleton; reuse TCP/HTTP keep-alive)."""
    global _gemini_client
    if _gemini_client is not None:
        return _gemini_client
    from google import genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment")
    _gemini_client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=genai_types.HttpOptions(timeout=GEMINI_HTTP_TIMEOUT_MS),
    )
    return _gemini_client
