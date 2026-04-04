"""Model provider client: Google Gemini (script + images)."""
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def load_gemini_client() -> Any:
    """Load and return the Google Gemini client for script and image generation."""
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY not set in environment")
    return genai.Client(api_key=api_key)
