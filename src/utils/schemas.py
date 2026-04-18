"""Data schemas: Layout and ComicScript JSON schema."""
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple


@dataclass
class Layout:
    page_w: int
    page_h: int
    margin: int
    gutter: int
    panel_boxes: List[Tuple[int, int, int, int]]  # (x1, y1, x2, y2)


COMIC_SCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "style": {
            "type": "object",
            "properties": {
                "art_style": {"type": "string"},
                "palette": {"type": "string"},
                "line_style": {"type": "string"},
            },
            "required": ["art_style", "palette", "line_style"],
            "additionalProperties": False
        },
        "characters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "appearance": {"type": "string"},
                    "clothing": {"type": "string"},
                    "personality": {"type": "string"}
                },
                "required": ["name", "appearance", "clothing", "personality"],
                "additionalProperties": False
            }
        },
        "setting": {"type": "string"},
        "panels": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {
                    "panel_id": {"type": "integer", "minimum": 1, "maximum": 3},
                    "visual_prompt": {"type": "string"},
                    "camera": {"type": "string"},
                    "mood": {"type": "string"},
                    "dialogue": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {"type": "string"},
                                "text_ar": {"type": "string"},
                            },
                            "required": ["speaker", "text_ar"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["panel_id", "visual_prompt", "camera", "mood", "dialogue"],
                "additionalProperties": False
            }
        }
    },
    "required": ["title", "style", "characters", "setting", "panels"],
    "additionalProperties": False
}
