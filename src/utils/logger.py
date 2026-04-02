"""
Comprehensive logging for the comic generator pipeline.
Logs to file, terminal, and optionally to a Streamlit UI callback.
"""
import os
import sys
from datetime import datetime
from typing import Callable, Optional, TextIO

# Log file in project root / logs /
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LOG_DIR = os.path.join(_PROJECT_ROOT, "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "comic_generator.log")

_log_callback: Optional[Callable[[str], None]] = None
_suppress_terminal: bool = False
_terminal_stream: Optional[TextIO] = None


def set_log_callback(
    callback: Optional[Callable[[str], None]],
    suppress_terminal: bool = False,
    terminal_stream: Optional[TextIO] = None,
) -> None:
    """Register a callback. If suppress_terminal, don't print to stdout (for JSON mode).
    If terminal_stream is set (e.g. sys.stderr), write logs there so they appear in terminal."""
    global _log_callback, _suppress_terminal, _terminal_stream
    _log_callback = callback
    _suppress_terminal = suppress_terminal
    _terminal_stream = terminal_stream


def _ensure_log_dir() -> None:
    os.makedirs(_LOG_DIR, exist_ok=True)


def _format_message(level: str, msg: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}] [{level}] {msg}"


def _log(level: str, msg: str) -> None:
    _ensure_log_dir()
    formatted = _format_message(level, msg)

    # File
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

    # Terminal: stdout when not suppressed, or stderr when terminal_stream is set (JSON mode)
    if not _suppress_terminal:
        print(formatted)
    elif _terminal_stream is not None:
        try:
            _terminal_stream.write(formatted + "\n")
            _terminal_stream.flush()
        except Exception:
            pass

    # UI callback (pass formatted line for console-style display)
    if _log_callback:
        try:
            _log_callback(formatted)
        except Exception:
            pass


def info(msg: str) -> None:
    _log("INFO", msg)


def step(msg: str) -> None:
    """Log a pipeline step (same as info but semantically a step)."""
    _log("STEP", msg)


def warn(msg: str) -> None:
    _log("WARN", msg)


def error(msg: str) -> None:
    _log("ERROR", msg)
