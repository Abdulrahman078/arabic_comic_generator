"""Optional DSPy teleprompter: BootstrapFewShot on ComicScript (add your own trainset for real gains).

Run (from repo root, with OPENAI_API_KEY set):
  uv run python -m src.generation.dspy_optimize

Saves `data/dspy_comic_script_program.json` unless `DSPY_COMIC_OPTIMIZER_OUT` is set.
See https://dspy.ai/ for optimizers (MIPROv2, GEPA, etc.).
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

import dspy

from src.generation.script_dspy import ComicScriptSignature, ensure_dspy_configured
from src.generation.script_prompts import build_script_user_message


def _valid_script_metric(gold: Any, pred: Any, trace: Any | None = None) -> float:
    """1.0 if prediction parses as ComicScript-like JSON with 3 panels."""
    try:
        raw = getattr(pred, "comic_script_json", None) or ""
        obj = json.loads(str(raw).strip())
        panels = obj.get("panels")
        if not isinstance(panels, list) or len(panels) != 3:
            return 0.0
        for i, p in enumerate(panels, start=1):
            if p.get("panel_id") != i:
                return 0.0
        return 1.0
    except Exception:
        return 0.0


def _minimal_demo_trainset() -> list[dspy.Example]:
    """One tiny Arabic story + gold JSON — replace with real labeled data for optimization."""
    story_ar = (
        "مشهد قصير: شخص واحد في غرفة مضاءة. يتكلم بثلاث جمل قصيرة فقط في ثلاث لقطات متتابعة."
    )
    structured = {
        "title": "مشهد تجريبي",
        "style": {"art_style": "manga", "palette": "warm", "line_style": "clean"},
        "characters": [
            {
                "name": "راوٍ",
                "appearance": "شاب، شعر قصير داكن، بشرة فاتحة",
                "clothing": "قميص بسيط بيج وبنطال داكن",
                "personality": "هادئ",
            }
        ],
        "setting": "غرفة صغيرة بإضاءة دافئة",
        "panels": [
            {
                "panel_id": 1,
                "visual_prompt": "الشخص يقف ويبتسم قليلاً",
                "camera": "wide",
                "mood": "هادئ",
                "dialogue": [{"speaker": "راوٍ", "text_ar": "أولاً."}],
            },
            {
                "panel_id": 2,
                "visual_prompt": "نفس الشخص يرفع يده قليلاً",
                "camera": "medium",
                "mood": "مرح",
                "dialogue": [{"speaker": "راوٍ", "text_ar": "ثانياً."}],
            },
            {
                "panel_id": 3,
                "visual_prompt": "لقطة أقرب للوجه",
                "camera": "close-up",
                "mood": "خفيف",
                "dialogue": [{"speaker": "راوٍ", "text_ar": "ثالثاً."}],
            },
        ],
    }
    gold_json = json.dumps(structured, ensure_ascii=False)
    um = build_script_user_message(story_ar)
    return [dspy.Example(user_message=um, comic_script_json=gold_json).with_inputs("user_message")]


def main() -> None:
    parser = argparse.ArgumentParser(description="BootstrapFewShot optimize ComicScript Predict")
    parser.add_argument(
        "-o",
        "--out",
        default=os.getenv("DSPY_COMIC_OPTIMIZER_OUT", "data/dspy_comic_script_program.json"),
        help="Output path for saved DSPy program",
    )
    args = parser.parse_args()

    ensure_dspy_configured()
    trainset = _minimal_demo_trainset()
    student = dspy.Predict(ComicScriptSignature)
    tele = dspy.BootstrapFewShot(metric=_valid_script_metric, max_bootstrapped_demos=2)
    optimized = tele.compile(student=student, trainset=trainset)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    optimized.save(out_path)
    print(f"Saved optimized program to {out_path}")
    print("Point DSPY_COMIC_PROGRAM_PATH at this file to load it at runtime.")


if __name__ == "__main__":
    main()
