"""Script generation: turns user prompt into structured 3-panel ComicScript via OpenAI.

When `COMIC_USE_DSPY` is set, generation goes through DSPy (`dspy.Predict`) using the same
instruction strings as the direct API path (`src.generation.script_prompts`).
"""
import json
import re
from typing import Any, Dict

from src.utils.clients import load_openai_client
from src.utils.config import LLM_MODEL, USE_DSPY_FOR_SCRIPT, llm_temperature
from src.utils.logger import step
from src.utils.cache import get_cached_script, set_cached_script
from src.generation.script_prompts import COMIC_SCRIPT_SYSTEM_RULES, build_script_user_message


def _sanitize_llm_output(text: str) -> str:
    """Remove invalid surrogate characters that LLMs sometimes emit."""
    return text.encode("utf-8", "replace").decode("utf-8")


def _extract_json(text: str) -> str:
    """Extract the first valid JSON object from potentially messy LLM output.
    
    Handles:
    - Markdown code fences (```json ... ```)
    - Multiple concatenated JSON objects
    - Extra text before/after JSON
    """
    # Remove markdown code fences
    if text.startswith("```"):
        lines = text.split("\n", 1)
        if len(lines) > 1:
            text = lines[1]
        else:
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    
    # Try to find and validate JSON by looking for balanced braces
    # This handles cases where there are multiple JSON objects or extra text
    first_brace = text.find('{')
    if first_brace == -1:
        raise ValueError("No JSON object found in response")
    
    # Try extracting JSON starting from each '{' we find
    depth = 0
    in_string = False
    escape_next = False
    json_start = -1
    
    for i, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if in_string:
            continue
        
        if char == '{':
            if depth == 0:
                json_start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and json_start != -1:
                # Found a complete JSON object
                candidate = text[json_start:i+1]
                # Validate it's actually valid JSON
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    # Not valid, continue searching
                    pass
    
    # Fallback: try the naive approach (first '{' to last '}')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace:last_brace + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    
    # If nothing worked, return the naive extraction and let json.loads fail with a clear error
    if first_brace != -1 and last_brace != -1:
        return text[first_brace:last_brace + 1]
    
    raise ValueError(f"No valid JSON object found in response (length: {len(text)})")


def _sanitize_script(obj: Any) -> Any:
    """Recursively sanitize strings in script dict."""
    if isinstance(obj, str):
        return _sanitize_llm_output(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_script(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_script(v) for v in obj]
    return obj


def _cache_backend() -> str:
    return "dspy" if USE_DSPY_FOR_SCRIPT else "openai"


def _call_openai_direct(user_message: str) -> str:
    """Direct OpenAI Chat Completions: same system rules + given user turn."""
    step("Loading OpenAI client (direct)...")
    client = load_openai_client()
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": COMIC_SCRIPT_SYSTEM_RULES},
            {"role": "user", "content": user_message},
        ],
        temperature=llm_temperature(),
    )
    txt = resp.choices[0].message.content
    if not txt:
        raise ValueError("Empty response from OpenAI")
    return txt.strip()


def _call_dspy(user_message: str) -> str:
    from src.generation.script_dspy import generate_comic_script_json_text

    step("DSPy ComicScript forward...")
    return generate_comic_script_json_text(user_message=user_message)


def _request_raw_script_text(user_message: str) -> str:
    if USE_DSPY_FOR_SCRIPT:
        return _call_dspy(user_message)
    return _call_openai_direct(user_message)


def generate_comic_script(user_prompt_ar: str, max_retries: int = 2) -> Dict[str, Any]:
    """Generates a structured 3-panel ComicScript JSON using OpenAI (direct or via DSPy)."""
    user_prompt_ar = _sanitize_llm_output(user_prompt_ar)
    backend = _cache_backend()

    cached = get_cached_script(user_prompt_ar, backend=backend)
    if cached is not None:
        step("Script cache hit - reusing")
        return cached

    user_first = build_script_user_message(user_prompt_ar)
    user_retry = (
        "Your previous output was invalid JSON or wrong schema.\n"
        "Return ONLY valid JSON with exactly 3 panels and the exact keys.\n"
        "No markdown.\n\n"
        f"Story prompt (Arabic): {user_prompt_ar}"
    )

    last_err = None
    for attempt in range(max_retries):
        try:
            step(
                f"Requesting script from LLM (attempt {attempt + 1}, "
                f"backend={'dspy' if USE_DSPY_FOR_SCRIPT else 'openai'})..."
            )
            user_msg = user_first if attempt == 0 else user_retry
            txt = _request_raw_script_text(user_msg)
            txt = _sanitize_llm_output(txt)

            # Extract valid JSON from potentially messy LLM output
            step(f"Raw LLM response length: {len(txt)} chars")
            txt = _extract_json(txt)
            step(f"Extracted JSON length: {len(txt)} chars")

            script = json.loads(txt)
            script = _sanitize_script(script)

            assert "panels" in script and isinstance(script["panels"], list), "Missing panels[]"
            assert len(script["panels"]) == 3, "Must be exactly 3 panels"
            for i, p in enumerate(script["panels"], start=1):
                assert p.get("panel_id") == i, f"panel_id must be {i}"
                assert "visual_prompt" in p
                assert "dialogue" in p and isinstance(p["dialogue"], list)

            step("Script validated successfully")
            set_cached_script(user_prompt_ar, script, backend=backend)
            return script

        except Exception as e:
            last_err = e
            step(f"Attempt {attempt + 1} failed: {str(e)[:200]}")
            # Log first 500 chars of raw response for debugging
            step(f"Raw response preview: {txt[:500]}...")

    err_msg = _sanitize_llm_output(str(last_err))
    raise RuntimeError(f"Failed to generate valid ComicScript JSON. Last error: {err_msg}")
