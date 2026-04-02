"""
Single source of truth for the comic generation pipeline.
Takes a user prompt and produces script, panels, and assembled page.
"""
import base64
import io
import json
import os
import sys
import time

# Ensure project root is on path (src/pipeline/ -> project root is 2 levels up)
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.utils.logger import step
from src.panel.text_bubble.text import download_font, get_font_path
from src.generation import generate_comic_script, generate_all_panels
from src.panel.layout.page import build_three_panel_layout, assemble_page
from src.panel.text_bubble.bubble_renderer import render_panel_with_bubbles

PAGE_W = 1024
PAGE_H = 1536


def run_pipeline(user_prompt: str, save_to_disk: bool = False) -> dict:
    """
    Run the full comic generation pipeline.

    Args:
        user_prompt: Arabic story/prompt for the comic.
        save_to_disk: If True, save page and panels to PNG files.

    Returns:
        dict with keys: script, raw_panels, final_panels, page
    """
    step("Pipeline started — prompt received")
    step("Checking foundation (font)...")
    download_font()

    step("Script generation — STARTED")
    t0 = time.perf_counter()
    script = generate_comic_script(user_prompt)
    step(f"Script generation — FINISHED in {time.perf_counter() - t0:.1f}s")
    step("Building layout...")
    layout = build_three_panel_layout(page_w=PAGE_W, page_h=PAGE_H)

    step("Generating panel images via Gemini...")
    raw_panels = generate_all_panels(script)
    step("Panel images generated — adding dialogue bubbles...")

    final_panels = []
    for i, p in enumerate(script["panels"]):
        step(f"Panel {i + 1} — bubble rendering STARTED")
        t0 = time.perf_counter()
        final_panels.append(render_panel_with_bubbles(raw_panels[i], p["dialogue"], get_font_path()))
        step(f"Panel {i + 1} — bubble rendering FINISHED in {time.perf_counter() - t0:.1f}s")

    step("Assembling final page...")
    page = assemble_page(final_panels, layout)
    step("Pipeline complete — comic ready")

    if save_to_disk:
        page.save("comic_page.png")
        for i, img in enumerate(final_panels, start=1):
            img.save(f"panel_{i}.png")

    return {
        "script": script,
        "raw_panels": raw_panels,
        "final_panels": final_panels,
        "page": page,
    }


def _pil_to_base64(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _sanitize_for_json(s: str) -> str:
    """Remove invalid surrogates so string can be safely JSON-encoded."""
    return s.encode("utf-8", "replace").decode("utf-8")


def _run_json_mode() -> None:
    """Read prompt from COMIC_PROMPT_B64 env (base64, set by API) or stdin, run pipeline, output JSON."""
    raw_b64 = os.environ.get("COMIC_PROMPT_B64")
    if raw_b64:
        try:
            raw = base64.b64decode(raw_b64).decode("utf-8", errors="replace")
        except Exception:
            raw = ""
    else:
        raw = sys.stdin.read()
    prompt = _sanitize_for_json(str(raw).strip())
    if not prompt:
        print(json.dumps({"success": False, "error": "Empty prompt"}))
        sys.exit(1)

    logs: list[str] = []

    def on_log(msg: str):
        logs.append(msg)

    from src.utils.logger import set_log_callback
    set_log_callback(on_log, suppress_terminal=True, terminal_stream=sys.stderr)
    try:
        result = run_pipeline(prompt, save_to_disk=False)
        safe_logs = [_sanitize_for_json(m) for m in logs]
        out = {
            "success": True,
            "page_base64": _pil_to_base64(result["page"]),
            "script": result["script"],
            "logs": safe_logs,
        }
        print(json.dumps(out, ensure_ascii=False), flush=True)
    except Exception as e:
        err_str = _sanitize_for_json(str(e))
        safe_logs = [_sanitize_for_json(m) for m in logs]
        print(json.dumps({"success": False, "error": err_str, "logs": safe_logs}), flush=True)
        sys.exit(1)
    finally:
        set_log_callback(None, suppress_terminal=False)


def main() -> None:
    """CLI entry point for the comic pipeline."""
    if "--json" in sys.argv:
        _run_json_mode()
        return

    default_prompt = """
    كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد في شارع قديم ليلًا، إضاءة فوانيس بسيطة.
    هارون الرشيد يظهر بملامح وقار مع لمسة استغراب، حاجب مرفوع ونظرة فاحصة. رجل بسيط يحمل زجاجة خمر، ملامحه ذكية وماكرة قليلًا.
    الكوميكس مكوّن من ثلاث لوحات واضحة: اللوحة الأولى: هارون الرشيد ينظر إلى الزجاجة ويسأل باستغرب: «ما هذا بيدك؟» اللوحة الثانية:
    الرجل يرد بسرعة وبوجه بريء: «هذا لبن». اللوحة الثالثة: هارون الرشيد يقترب قليلًا ويقول متعجبًا: «ومتى أصبح اللبن أحمر يا هذا؟» الرجل يبتسم بثقة ودهاء ويجيب: «احمر خجلًا منك يا أمير المؤمنين» فعجب هارون الرشيد من دهاء الرجل فضحك أمير المؤمنين وعفى عنه.
    ألوان دافئة، تعبيرات وجه واضحة ومبالغ فيها قليلًا لإبراز الطرافة، لغة جسد كوميدية، أسلوب كوميكس لطيف، جودة عالية.
    """.strip()

    step("Generating comic script...")
    result = run_pipeline(default_prompt, save_to_disk=True)
    step("Script generated successfully")
    print(json.dumps(result["script"], ensure_ascii=False, indent=2))
    step("Success! Saved full page to: comic_page.png")
    for i in range(len(result["final_panels"])):
        step(f"Saved panel {i + 1} to: panel_{i + 1}.png")


if __name__ == "__main__":
    main()
