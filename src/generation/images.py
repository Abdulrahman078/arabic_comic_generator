"""Panel image generation: creates art for each panel via Gemini image API."""
import hashlib
import io
import secrets
import time
from PIL import Image
from typing import Dict, Any, List

from src.utils.clients import load_gemini_client
from src.utils.logger import step
from src.utils.config import GEMINI_IMAGE_MODEL, GEMINI_PRIORITY_IMAGE_TIER
from src.generation.context import build_shared_context
from google.genai import types

# Retry config for transient API errors (500, 503, etc.)
_IMAGE_RETRIES = 3
_IMAGE_RETRY_DELAY = 5  # seconds, doubles each attempt

_RETRY_HINTS = (
    "500",
    "503",
    "504",
    "408",
    "429",
    "internal",
    "timeout",
    "timed out",
    "deadline",
    "overloaded",
    "unavailable",
    "connection",
    "reset",
    "broken pipe",
    "resource_exhausted",
    "try again",
    "temporarily",
)


def _short_error(err: Exception, limit: int = 220) -> str:
    """Single-line message for logs (ASCII-safe)."""
    msg = str(err).replace("\n", " ").strip()
    if len(msg) > limit:
        msg = msg[: limit - 3] + "..."
    return msg.encode("ascii", errors="replace").decode("ascii")


def _is_retryable_error(err: Exception) -> bool:
    """True if error is likely transient (5xx, 429, timeouts, connection)."""
    msg = str(err).lower()
    name = type(err).__name__.lower()
    if any(x in name for x in ("timeout", "transport", "connect", "http")):
        return True
    return any(x in msg for x in _RETRY_HINTS)


def _format_script_panel_row(p: Dict[str, Any], *, compact: bool = False) -> str:
    """Single panel row description from ComicScript (visual + camera + mood)."""
    panel_prompt = p["visual_prompt"]
    if p.get("mood") or p.get("camera"):
        extras = []
        if p.get("mood"):
            extras.append(f"Mood: {p['mood']}")
        if p.get("camera"):
            extras.append(f"Camera: {p['camera']}")
        if extras:
            panel_prompt = f"{' | '.join(extras)}. {panel_prompt}"
    pid = p.get("panel_id", 0)
    if compact:
        return f"P{pid}: {panel_prompt}"
    return f"Panel band {pid} (top-to-bottom order): {panel_prompt}"


def _build_three_panel_strip_prompt(script: Dict[str, Any], *, compact: bool = True) -> str:
    """One-image instruction: three horizontal rows stacked vertically in a single frame."""
    rows = [_format_script_panel_row(p, compact=compact) for p in script["panels"]]
    if compact:
        return (
            "ONE image: 3 equal horizontal rows (top/mid/bottom), gutters between rows. "
            "Same cast and setting; vary pose/camera per row.\n\n" + "\n".join(rows)
        )
    return (
        "COMPOSITION — ONE single image only. Draw exactly THREE comic panels stacked vertically: "
        "top band = first panel, middle band = second panel, bottom band = third panel. "
        "Use three equal-height horizontal rows with clear separation (gutter, border, or margin) between rows. "
        "Same characters and setting across all three bands; only action, pose, and framing change per band.\n\n"
        + "\n\n".join(rows)
    )


def _panel_seed(shared_context: str, panel_id: int) -> int:
    """Base seed from context + panel (API may use this for reproducibility)."""
    h = hashlib.sha256((shared_context + str(panel_id)).encode()).hexdigest()
    return int(h[:8], 16) % (2**31)


def _request_image_seed(shared_context: str, panel_id: int) -> int:
    """Different on every Generate click: fixed seed + same cached script used to duplicate images."""
    return (_panel_seed(shared_context, panel_id) ^ secrets.randbelow(2**31)) % (2**31)


def generate_panel_image(
    panel_prompt: str,
    shared_context: str = "",
    panel_id: int = 1,
    aspect_ratio: str = "1:1",
    image_size: str = "1K",
) -> Image.Image:
    """Generates a single panel image using Gemini (art only; no on-image text)."""

    full_prompt_parts = []
    if shared_context.strip():
        full_prompt_parts.append(shared_context.strip())
    full_prompt_parts.append(panel_prompt.strip())
    full_prompt_parts.append(
        "IMPORTANT: No written text, no letters, no subtitles, no speech bubbles anywhere in the image."
    )
    if shared_context.strip():
        full_prompt_parts.append(
            "Keep character design and setting consistent across the three bands."
        )

    prompt = "\n\n".join(full_prompt_parts)

    client = load_gemini_client()

    # IMAGE only — do not request TEXT; TEXT+IMAGE makes the model emit text first and often adds minutes of latency.
    config_kw: Dict[str, Any] = {
        "response_modalities": ["IMAGE"],
        "image_config": types.ImageConfig(
            aspect_ratio=aspect_ratio,
            image_size=image_size,
        ),
    }
    if GEMINI_PRIORITY_IMAGE_TIER:
        config_kw["service_tier"] = types.ServiceTier.PRIORITY
    config_kw["seed"] = _request_image_seed(shared_context, panel_id)

    try:
        config = types.GenerateContentConfig(**config_kw)
    except (TypeError, ValueError):
        config_kw.pop("seed", None)
        try:
            config = types.GenerateContentConfig(**config_kw)
        except (TypeError, ValueError):
            config_kw.pop("service_tier", None)
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
                label = "3-panel strip" if panel_id == 0 else f"Panel {panel_id}"
                step(
                    f"{label} - API error (attempt {attempt + 1}/{_IMAGE_RETRIES}): "
                    f"{_short_error(e)}. Retrying in {delay}s..."
                )
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
    """One Gemini request: a single image showing three stacked comic bands (script panels 1–3)."""
    shared_context = build_shared_context(script, compact=True)
    combined = _build_three_panel_strip_prompt(script, compact=True)
    step("3-panel strip (single image API call) - STARTED")
    t0 = time.perf_counter()
    # Portrait strip; page layout is 1024×1536 (2:3).
    img = generate_panel_image(
        combined,
        shared_context=shared_context,
        panel_id=0,
        aspect_ratio="2:3",
    )
    elapsed = time.perf_counter() - t0
    step(f"3-panel strip - image FINISHED in {elapsed:.1f}s")
    return [img]
