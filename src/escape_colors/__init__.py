"""ANSI colors and formatting without runtime dependencies."""

import os as _os

from ._codes import NAMED_CODES as _NAMED_CODES
from ._codes import RESET as escape
from ._codes import background, color
from ._notation import normalize_ansi, strip_ansi
from ._notation import require_text as _require_text
from ._notation import serialize as _serialize
from ._notation import validate_format as _validate_format
from ._parser import render as _render

ESCAPE_COLOR_FORMAT = _os.environ.get("ESCAPE_COLOR_FORMAT", "unicode")
reset = escape

# Named constants are ordinary strings, suitable for direct f-string use.
globals().update(_NAMED_CODES)


def format_ansi(text: str, *, format: str | None = None) -> str:
    """Write ESC using unicode, hex, or octal notation, preserving other text."""
    return _serialize(text, ESCAPE_COLOR_FORMAT if format is None else format)


def escape_ansi(
    text: str,
    *,
    format: str | None = None,
    literal: bool = False,
    decode: bool = False,
) -> str:
    """Render nested styles; optionally decode or serialize textual ESC notation."""
    _require_text(text)
    selected = _validate_format(ESCAPE_COLOR_FORMAT if format is None else format)
    if not isinstance(literal, bool) or not isinstance(decode, bool):
        raise TypeError("literal and decode must be bools")
    rendered = _render(normalize_ansi(text) if decode else text)
    return _serialize(rendered, selected) if literal else rendered


__all__ = [
    "ESCAPE_COLOR_FORMAT",
    "background",
    "color",
    "escape",
    "escape_ansi",
    "format_ansi",
    "normalize_ansi",
    "reset",
    "strip_ansi",
    *_NAMED_CODES,
]
