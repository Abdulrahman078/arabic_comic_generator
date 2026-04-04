"""In-memory cache for script, style, and character sheet to reduce LLM cost."""

import hashlib
from typing import Any, Dict, Optional

from src.utils.config import ENABLE_CACHE

_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_MAX_ENTRIES = 50


def _make_key(prompt: str, suffix: str = "") -> str:
    """Hash of prompt + suffix for cache key."""
    h = hashlib.sha256((prompt + suffix).encode("utf-8", errors="replace")).hexdigest()
    return h[:24]


def get_cached_script(prompt: str) -> Optional[Dict[str, Any]]:
    """Returns cached full script if available (same prompt)."""
    if not ENABLE_CACHE:
        return None
    key = _make_key(prompt, "script")
    entry = _cache.get(key)
    return entry.get("script") if entry else None


def set_cached_script(prompt: str, script: Dict[str, Any]) -> None:
    """Stores script for reuse when same prompt is used again."""
    if not ENABLE_CACHE:
        return
    if len(_cache) >= _CACHE_MAX_ENTRIES:
        first = next(iter(_cache))
        del _cache[first]
    key = _make_key(prompt, "script")
    _cache[key] = {"script": script}
