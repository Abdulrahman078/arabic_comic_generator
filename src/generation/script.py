"""Script generation: turns user prompt into structured 3-panel ComicScript via LLM."""
import json
from typing import Any, Dict

from src.utils.clients import load_openai_client
from src.utils.config import LLM_MODEL
from src.utils.logger import step
from src.utils.cache import get_cached_script, set_cached_script


def _sanitize_llm_output(text: str) -> str:
    """Remove invalid surrogate characters that LLMs sometimes emit."""
    return text.encode("utf-8", "replace").decode("utf-8")


def _sanitize_script(obj: Any) -> Any:
    """Recursively sanitize strings in script dict."""
    if isinstance(obj, str):
        return _sanitize_llm_output(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_script(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_script(v) for v in obj]
    return obj


def generate_comic_script(user_prompt_ar: str, max_retries: int = 2) -> Dict[str, Any]:
    """Generates a structured 3-panel ComicScript JSON using GPT."""
    user_prompt_ar = _sanitize_llm_output(user_prompt_ar)

    cached = get_cached_script(user_prompt_ar)
    if cached is not None:
        step("Script cache hit — reusing")
        return cached

    system = (
        "You are a comic storyboard assistant. Return ONLY valid JSON. No markdown. No code fences.\n\n"
        "REQUIRED RULES (all must be followed):\n"
        "- Exactly 3 panels. Each panel must have panel_id 1, 2, 3.\n"
        "- visual_prompt: ART ONLY. No written text, no letters, no subtitles, no speech bubbles.\n"
        "- camera: use terms like close-up, wide shot, over-the-shoulder for manga feel.\n"
        "- dialogue[].text_ar: Arabic text only.\n"
        "- dialogue[].bubble_type: exactly one of speech, thought, caption.\n"
        "- All keys are required. No optional fields.\n\n"
        "EXACT JSON SHAPE:\n"
        '{"title":"string","style":{"art_style":"string","palette":"string","line_style":"string"},'
        '"characters":[{"name":"string","visual_description":"string","clothing":"string","personality":"string"}],'
        '"setting":"string","panels":['
        '{"panel_id":1,"visual_prompt":"string","camera":"string","mood":"string","dialogue":[{"speaker":"string","text_ar":"string","bubble_type":"speech"}]},'
        '{"panel_id":2,"visual_prompt":"string","camera":"string","mood":"string","dialogue":[{"speaker":"string","text_ar":"string","bubble_type":"speech"}]},'
        '{"panel_id":3,"visual_prompt":"string","camera":"string","mood":"string","dialogue":[{"speaker":"string","text_ar":"string","bubble_type":"speech"}]}'
        "]}"
    )

    user = (
        "Story prompt (Arabic):\n"
        f"{user_prompt_ar}\n\n"
        "Generate the ComicScript JSON now."
    )

    step("Loading OpenAI client...")
    client = load_openai_client()
    last_err = None
    for attempt in range(max_retries):
        try:
            step(f"Requesting script from LLM (attempt {attempt + 1})...")
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0,
            )

            txt = resp.choices[0].message.content.strip()
            txt = _sanitize_llm_output(txt)
            script = json.loads(txt)
            script = _sanitize_script(script)

            assert "panels" in script and isinstance(script["panels"], list), "Missing panels[]"
            assert len(script["panels"]) == 3, "Must be exactly 3 panels"
            for i, p in enumerate(script["panels"], start=1):
                assert p.get("panel_id") == i, f"panel_id must be {i}"
                assert "visual_prompt" in p
                assert "dialogue" in p and isinstance(p["dialogue"], list)

            step("Script validated successfully")
            set_cached_script(user_prompt_ar, script)
            return script

        except Exception as e:
            last_err = e
            user = (
                "Your previous output was invalid JSON or wrong schema.\n"
                "Return ONLY valid JSON with exactly 3 panels and the exact keys.\n"
                "No markdown.\n\n"
                f"Story prompt (Arabic): {user_prompt_ar}"
            )

    err_msg = _sanitize_llm_output(str(last_err))
    raise RuntimeError(f"Failed to generate valid ComicScript JSON. Last error: {err_msg}")
