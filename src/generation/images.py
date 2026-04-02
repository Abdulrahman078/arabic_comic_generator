"""Panel image generation: creates art for each panel via AI image API (Gemini by default, OpenAI optional)."""
import base64
import hashlib
import io
import time
from PIL import Image
from typing import Dict, Any, List

from src.utils.clients import load_gemini_client, load_openai_client
from src.utils.logger import step
from src.utils.config import GEMINI_IMAGE_MODEL, OPENAI_IMAGE_MODEL
from src.generation.context import build_shared_context
from google.genai import types

# Retry config for transient API errors (500, 503, etc.)
_IMAGE_RETRIES = 3
_IMAGE_RETRY_DELAY = 5  # seconds, doubles each attempt


def _is_retryable_error(err: Exception) -> bool:
    """True if error is likely transient (500, 503, 429, timeout)."""
    msg = str(err).lower()
    return any(
        x in msg
        for x in ("500", "503", "429", "internal", "timeout", "overloaded", "unavailable")
    )


def _panel_seed(shared_context: str, panel_id: int) -> int:
    """Deterministic seed from context + panel for consistency (if API supports it)."""
    h = hashlib.sha256((shared_context + str(panel_id)).encode()).hexdigest()
    return int(h[:8], 16) % (2**31)


_NO_BUBBLES_PROMPT = (
    "Do NOT draw any speech bubbles. No text, no letters, no subtitles, no captions anywhere."
)


def generate_panel_image(
    panel_prompt: str,
    shared_context: str = "",
    panel_id: int = 1,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
) -> Image.Image:
    """Generates a single panel image using Gemini API. No bubbles — we draw them ourselves."""

    full_prompt_parts = []
    if shared_context.strip():
        full_prompt_parts.append(shared_context.strip())
    full_prompt_parts.append(panel_prompt.strip())
    full_prompt_parts.append(_NO_BUBBLES_PROMPT)

    prompt = "\n\n".join(full_prompt_parts)

    client = load_gemini_client()

    config_kw: Dict[str, Any] = {
        "response_modalities": ["TEXT", "IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    }
    config_kw["seed"] = _panel_seed(shared_context, panel_id)

    try:
        config = types.GenerateContentConfig(**config_kw)
    except (TypeError, ValueError):
        config_kw.pop("seed", None)
        config = types.GenerateContentConfig(**config_kw)

    last_err = None
    delay = _IMAGE_RETRY_DELAY
    for attempt in range(_IMAGE_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_IMAGE_MODEL,
                contents=[prompt],
                config=config,
            )
            parts = getattr(response, "parts", None) or (
                response.candidates[0].content.parts if response.candidates else []
            )
            for part in parts:
                if getattr(part, "inline_data", None):
                    raw = getattr(part.inline_data, "data", None)
                    if raw:
                        return Image.open(io.BytesIO(raw)).convert("RGB")
            raise RuntimeError("Gemini did not return an image")
        except Exception as e:
            last_err = e
            if attempt < _IMAGE_RETRIES - 1 and _is_retryable_error(e):
                step(f"Panel {panel_id} — API error (attempt {attempt + 1}/{_IMAGE_RETRIES}), retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                err_msg = str(e)
                if "500" in err_msg or "internal" in err_msg.lower():
                    raise RuntimeError(
                        "Gemini API temporarily unavailable (500). Try again in a few minutes."
                    ) from e
                raise

    raise RuntimeError(f"Gemini image generation failed after {_IMAGE_RETRIES} attempts: {last_err}")


def generate_panel_image_openai(
    panel_prompt: str,
    shared_context: str = "",
    size: str = "1024x1024",
) -> Image.Image:
    """Generates a single panel image using OpenAI Image API (alternative to Gemini)."""
    full_prompt_parts = []
    if shared_context.strip():
        full_prompt_parts.append(shared_context.strip())
    full_prompt_parts.append(panel_prompt.strip())
    base = "\n\n---\n\n".join(full_prompt_parts)
    safe_prompt = base + "\n\n" + _NO_BUBBLES_PROMPT

    client = load_openai_client()
    img_resp = client.images.generate(model=OPENAI_IMAGE_MODEL, prompt=safe_prompt, size=size)

    if img_resp.data[0].b64_json:
        raw = base64.b64decode(img_resp.data[0].b64_json)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    import requests

    resp = requests.get(img_resp.data[0].url)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGB")


def generate_all_panels(script: Dict[str, Any]) -> List[Image.Image]:
    """Generates all 3 panel images from the script using Gemini. No bubbles in image — we draw them ourselves."""
    shared_context = build_shared_context(script)
    panels = []
    for p in script["panels"]:
        panel_id = p["panel_id"]
        step(f"Panel {panel_id} — image generation STARTED")
        t0 = time.perf_counter()
        panel_prompt = p["visual_prompt"]
        if p.get("mood") or p.get("camera"):
            extras = []
            if p.get("mood"):
                extras.append(f"Mood: {p['mood']}")
            if p.get("camera"):
                extras.append(f"Camera: {p['camera']}")
            if extras:
                panel_prompt = f"{' | '.join(extras)}. {panel_prompt}"
        img = generate_panel_image(
            panel_prompt,
            shared_context=shared_context,
            panel_id=panel_id,
        )
        elapsed = time.perf_counter() - t0
        step(f"Panel {panel_id} — image FINISHED in {elapsed:.1f}s")
        panels.append(img)
    return panels
