"""ANSI colors and formatting without runtime dependencies."""

import os as _os
import sys as _sys
from typing import TextIO as _TextIO

from ._codes import NAMED_CODES as _NAMED_CODES
from ._codes import RESET as escape
from ._codes import background, color
from ._notation import normalize_ansi, strip_ansi
from ._notation import require_text as _require_text
from ._notation import serialize as _serialize
from ._notation import validate_format as _validate_format
from ._parser import render as _render
from ._terminal import color_enabled as _color_enabled
from ._terminal import init_windows

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


def ansi_print(
    *objects: object,
    sep: str | None = " ",
    end: str | None = "\n",
    file: _TextIO | None = None,
    flush: bool = False,
    color: bool | None = None,
) -> None:
    """Print nested markup, choosing color automatically unless overridden."""
    if sep is not None and not isinstance(sep, str):
        raise TypeError("sep must be None or a string")
    if end is not None and not isinstance(end, str):
        raise TypeError("end must be None or a string")
    stream = _sys.stdout if file is None else file
    enabled = _color_enabled(stream, color)
    if stream is None:
        return
    rendered = [escape_ansi(str(obj)) for obj in objects]
    if not enabled:
        rendered = [strip_ansi(text) for text in rendered]
        sep = strip_ansi(sep) if sep is not None else None
        end = strip_ansi(end) if end is not None else None
    print(*rendered, sep=sep, end=end, file=stream, flush=flush)


__all__ = [
    "ESCAPE_COLOR_FORMAT",
    "ansi_print",
    "background",
    "color",
    "escape",
    "escape_ansi",
    "format_ansi",
    "init_windows",
    "normalize_ansi",
    "reset",
    "strip_ansi",
    *_NAMED_CODES,
]
