"""Shared context logic: builds visual context string for consistent panel generation."""
from typing import Dict, Any

from src.utils.config import STYLE_LOCK


def build_character_sheet(script: Dict[str, Any]) -> str:
    """Builds a compact character sheet string for use in every panel prompt."""
    chars = script.get("characters") or []
    if not chars:
        return ""
    lines = []
    for c in chars:
        name = c.get("name", "")
        vis = c.get("visual_description", "")
        cloth = c.get("clothing", "")
        line = f"{name}: {vis}" + (f", {cloth}" if cloth else "")
        if line.strip():
            lines.append(line.strip())
    if not lines:
        return ""
    return "Character sheet (identical in all panels): " + "; ".join(lines)


def build_shared_context(script: Dict[str, Any]) -> str:
    """Builds shared context from script for visual consistency across panels."""
    parts = []

    char_sheet = build_character_sheet(script)
    if char_sheet:
        parts.append(char_sheet)

    style = script.get("style") or {}
    if style:
        art = style.get("art_style", "")
        palette = style.get("palette", "")
        lines = style.get("line_style", "")
        if any([art, palette, lines]):
            parts.append(
                f"Art style: {art}. Color palette: {palette}. Line style: {lines}."
            )

    setting = script.get("setting", "")
    if setting:
        parts.append(f"Setting (same environment in all panels): {setting}.")

    if not parts:
        return ""
    base = (
        "CONSISTENT VISUAL CONTEXT — apply to EVERY panel. "
        "Characters, clothing, and setting must be identical across all 3 panels:\n"
        + " ".join(parts)
    )
    return base + f"\n\nStyle lock: {STYLE_LOCK}."
