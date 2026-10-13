"""Represent ESC without decoding unrelated user text."""

import re

from ._codes import ESC

SPELLINGS = {"unicode": r"\u001b", "hex": r"\x1b", "octal": r"\033"}
SGR_PATTERN = re.compile(r"\u001b\[[0-9;]*m")
_LITERAL_ESC = re.compile(r"(?<!\\)(?:\\u001[bB]|\\x1[bB]|\\033)(?=\[[0-9;]*m)")


def validate_format(format: str) -> str:
    if not isinstance(format, str):
        raise TypeError("escape format must be a string")
    if format not in SPELLINGS:
        raise ValueError("escape format must be 'unicode', 'hex', or 'octal'")
    return format


def require_text(text: str) -> None:
    if not isinstance(text, str):
        raise TypeError("text must be a string")


def serialize(text: str, format: str) -> str:
    require_text(text)
    return text.replace(ESC, SPELLINGS[validate_format(format)])


def normalize_ansi(text: str) -> str:
    """Decode textual ESC spellings only before complete numeric SGR codes."""
    require_text(text)
    return _LITERAL_ESC.sub(lambda match: ESC, text)


def strip_ansi(text: str) -> str:
    """Remove numeric SGR codes; leave other control sequences untouched."""
    require_text(text)
    return SGR_PATTERN.sub("", text)
