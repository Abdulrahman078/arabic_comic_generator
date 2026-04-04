"""Panel image generation: creates art for each panel via Gemini image API."""
import hashlib
import io
import time
from PIL import Image
from typing import Dict, Any, List

from src.utils.clients import load_gemini_client
from src.utils.logger import step
from src.utils.config import GEMINI_IMAGE_MODEL
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


def _build_bubble_prompt(num_bubbles: int) -> str:
    """Instructs Gemini to draw empty speech bubbles so YOLO can detect regions for Arabic text."""
    if num_bubbles <= 0:
        return (
            "Do NOT draw any speech bubbles. If any bubbles appear, they must be completely empty."
        )
    return (
        f"CRITICAL: Draw exactly {num_bubbles} empty speech bubble(s) for this panel. "
        "Each bubble must correspond to a dialogue line—but do NOT put any text, letters, or words inside the bubbles. "
        "The bubbles must be completely empty: white fill, black outline, rounded rectangle shape. "
        "Place each bubble near the character who will speak. "
        "We will detect these bubbles and fill them with text later—they must be clearly visible and empty."
    )


def generate_panel_image(
    panel_prompt: str,
    shared_context: str = "",
    panel_id: int = 1,
    num_bubbles: int = 0,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
) -> Image.Image:
    """Generates a single panel image using Gemini. Empty bubbles for YOLO + Arabic overlay."""

    full_prompt_parts = []
    if shared_context.strip():
        full_prompt_parts.append(shared_context.strip())
    full_prompt_parts.append(panel_prompt.strip())
    full_prompt_parts.append(
        "IMPORTANT: No written text, no letters, no subtitles anywhere in the image."
    )
    full_prompt_parts.append(_build_bubble_prompt(num_bubbles))

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


def generate_all_panels(script: Dict[str, Any]) -> List[Image.Image]:
    """Generates all 3 panel images via Gemini. Empty bubbles for YOLO; text overlay in renderer."""
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
        num_bubbles = len(p.get("dialogue", []))
        img = generate_panel_image(
            panel_prompt,
            shared_context=shared_context,
            panel_id=panel_id,
            num_bubbles=num_bubbles,
        )
        elapsed = time.perf_counter() - t0
        step(f"Panel {panel_id} — image FINISHED in {elapsed:.1f}s")
        panels.append(img)
    return panels
