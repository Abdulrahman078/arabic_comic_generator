"""Shared context logic: builds visual context string for consistent panel generation."""
from typing import Dict, Any

from src.utils.config import STYLE_LOCK


def _character_appearance(c: Dict[str, Any]) -> str:
    """Physical look: prefer `appearance`, fall back to legacy `visual_description`."""
    return (c.get("appearance") or c.get("visual_description") or "").strip()


def build_character_sheet(script: Dict[str, Any], *, compact: bool = False) -> str:
    """Builds a locked character-design block for every panel prompt (manga consistency)."""
    chars = script.get("characters") or []
    if not chars:
        return ""
    blocks: list[str] = []
    for c in chars:
        name = (c.get("name") or "").strip()
        appearance = _character_appearance(c)
        clothing = (c.get("clothing") or "").strip()
        if not name and not appearance and not clothing:
            continue
        if compact:
            segs: list[str] = []
            if name:
                segs.append(name)
            if appearance:
                segs.append(f"look: {appearance}")
            if clothing:
                segs.append(f"outfit: {clothing}")
            if segs:
                blocks.append(" | ".join(segs))
            continue
        parts = []
        if name:
            parts.append(f"Name: {name}")
        if appearance:
            parts.append(
                f"Appearance (locked - same face, hair, body, proportions in every panel): {appearance}"
            )
        if clothing:
            parts.append(
                f"Outfit (locked - identical clothes, colors, and accessories in every panel): {clothing}"
            )
        blocks.append(" | ".join(parts))
    if not blocks:
        return ""
    joined = "\n".join(f"  - {b}" for b in blocks)
    if compact:
        return "CHARACTER LOCK (same in all bands):\n" + joined
    return (
        "CHARACTER DESIGN LOCK - apply EXACTLY to panels 1, 2, and 3. "
        "Do not change outfits, hair, faces, proportions, or body type between panels.\n"
        f"{joined}"
    )


def build_shared_context(script: Dict[str, Any], *, compact: bool = False) -> str:
    """Builds shared context from script for visual consistency across panels.

    ``compact=True`` uses fewer tokens for the Gemini image call (shorter queue / faster decode on long prompts).
    """
    parts = []

    char_sheet = build_character_sheet(script, compact=compact)
    if char_sheet:
        parts.append(char_sheet)

    style = script.get("style") or {}
    if style:
        art = style.get("art_style", "")
        palette = style.get("palette", "")
        lines = style.get("line_style", "")
        if any([art, palette, lines]):
            if compact:
                parts.append(f"Art: {art} | Palette: {palette} | Lines: {lines}")
            else:
                parts.append(
                    f"Art style: {art}. Color palette: {palette}. Line style: {lines}."
                )

    setting = script.get("setting", "")
    if setting:
        if compact:
            parts.append(f"Setting: {setting}")
        else:
            parts.append(f"Setting (same environment in all panels): {setting}.")

    if not parts:
        return ""
    if compact:
        return (
            "VISUAL CONTEXT — same cast, outfit, and setting in all 3 vertical bands.\n\n"
            + "\n\n".join(parts)
            + f"\n\n{STYLE_LOCK}"
        )
    base = (
        "CONSISTENT VISUAL CONTEXT - prepend to EVERY panel. "
        "Same characters (appearance + outfit), same setting, same art style across all 3 panels.\n\n"
        + "\n\n".join(parts)
    )
    return base + f"\n\nStyle lock: {STYLE_LOCK}."
