"""Model clients: OpenAI (script text) and Gemini (images only)."""
from typing import Any

from src.utils.config import GEMINI_API_KEY, OPENAI_API_KEY


def load_openai_client() -> Any:
    """OpenAI client for ComicScript JSON generation."""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=OPENAI_API_KEY)


def load_gemini_client() -> Any:
    """Google Gemini client for panel image generation only."""
    from google import genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=GEMINI_API_KEY)
