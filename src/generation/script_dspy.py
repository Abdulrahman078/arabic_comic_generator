"""DSPy path for ComicScript generation — same instructions as `script_prompts`, structured as a Signature.

Docs: https://dspy.ai/ (DSPy 3.x: `dspy.LM`, `dspy.Predict`, optional `dspy.load` for compiled programs).
"""
from __future__ import annotations

import os
from typing import Any

import dspy

from src.generation.script_prompts import COMIC_SCRIPT_SYSTEM_RULES, build_script_user_message
from src.utils.config import DSPY_OPTIMIZED_PROGRAM_PATH, LLM_MODEL, OPENAI_API_KEY, llm_temperature


class ComicScriptSignature(dspy.Signature):
    """Placeholder — replaced at import time with `COMIC_SCRIPT_SYSTEM_RULES` (legacy system prompt)."""

    user_message: str = dspy.InputField(
        description="User turn: Arabic story and instruction to output ComicScript JSON only."
    )
    comic_script_json: str = dspy.OutputField(
        description="Single valid JSON object (ComicScript). No markdown or code fences."
    )


ComicScriptSignature.__doc__ = COMIC_SCRIPT_SYSTEM_RULES

_lm_ready = False
_predictor: Any = None


def ensure_dspy_configured() -> None:
    """Configure global `dspy` LM from project settings (idempotent)."""
    _ensure_lm()


def _configure_litellm_drop_params() -> None:
    """DSPy uses LiteLLM; drop unsupported params for newer OpenAI models (optional)."""
    try:
        import litellm

        if os.getenv("LITELLM_DROP_PARAMS", "1").lower() not in ("0", "false", "no"):
            litellm.drop_params = True
    except ImportError:
        pass


def _ensure_lm() -> None:
    global _lm_ready
    if _lm_ready:
        return
    _configure_litellm_drop_params()
    kwargs: dict[str, Any] = {"temperature": llm_temperature(), "max_tokens": 16000}
    if OPENAI_API_KEY:
        kwargs["api_key"] = OPENAI_API_KEY
    lm = dspy.LM(f"openai/{LLM_MODEL}", **kwargs)
    dspy.configure(lm=lm)
    _lm_ready = True


def _get_predictor() -> Any:
    global _predictor
    if _predictor is not None:
        return _predictor
    path = DSPY_OPTIMIZED_PROGRAM_PATH
    if path and os.path.isfile(path):
        _predictor = dspy.load(path)
    else:
        _predictor = dspy.Predict(ComicScriptSignature)
    return _predictor


def generate_comic_script_json_text(
    *,
    story_prompt_ar: str | None = None,
    user_message: str | None = None,
) -> str:
    """Returns raw model text (expected to be JSON). Uses DSPy Predict or a saved optimized program.

    Pass `user_message` for the exact user turn (first attempt or retry). If omitted, builds it from
    `story_prompt_ar` like the direct OpenAI path.
    """
    _ensure_lm()
    if user_message is not None:
        um = user_message
    elif story_prompt_ar is not None:
        um = build_script_user_message(story_prompt_ar)
    else:
        raise ValueError("Provide story_prompt_ar or user_message")
    out = _get_predictor()(user_message=um)
    return (out.comic_script_json or "").strip()
