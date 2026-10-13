"""ANSI colors and formatting without runtime dependencies."""

import os as _os

from ._codes import NAMED_CODES as _NAMED_CODES
from ._codes import RESET as escape
from ._codes import background, color
from ._notation import normalize_ansi, strip_ansi
from ._notation import serialize as _serialize

ESCAPE_COLOR_FORMAT = _os.environ.get("ESCAPE_COLOR_FORMAT", "unicode")
reset = escape

# Named constants are ordinary strings, suitable for direct f-string use.
globals().update(_NAMED_CODES)


def format_ansi(text: str, *, format: str | None = None) -> str:
    """Write ESC using unicode, hex, or octal notation, preserving other text."""
    return _serialize(text, ESCAPE_COLOR_FORMAT if format is None else format)


__all__ = [
    "ESCAPE_COLOR_FORMAT",
    "background",
    "color",
    "escape",
    "format_ansi",
    "normalize_ansi",
    "reset",
    "strip_ansi",
    *_NAMED_CODES,
]
