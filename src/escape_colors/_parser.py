"""An iterative parser for nested style expressions."""

import re

from ._codes import NAMED_CODES, RESET, background, color

_OPEN = re.compile(r"(bg_-?[0-9]+|[A-Za-z_][A-Za-z_0-9]*|-?[0-9]+)\(")
_INDEX = re.compile(r"-?[0-9]+\Z")


def _indexed_code(token: str, position: int, *, bg: bool = False) -> str:
    # Avoid Python's large integer string limit and unnecessary conversion work.
    digits = token.lstrip("0") or "0"
    if token.startswith("-") or len(digits) > 3 or int(digits) > 255:
        raise ValueError(f"color index must be between 0 and 255 at position {position}")
    return background(int(digits)) if bg else color(int(digits))


def _style_code(token: str, position: int) -> str | None:
    if token in NAMED_CODES:
        return NAMED_CODES[token]
    if _INDEX.fullmatch(token):
        return _indexed_code(token, position)
    if token.startswith("bg_") and _INDEX.fullmatch(token[3:]):
        return _indexed_code(token[3:], position, bg=True)
    return None


def render(text: str) -> str:
    output = []
    frames: list[tuple[str | None, int]] = []
    active: list[str] = []
    position = 0

    while position < len(text):
        char = text[position]
        if char == "\\" and position + 1 < len(text) and text[position + 1] in "()\\":
            output.append(text[position + 1])
            position += 2
            continue

        standalone = position == 0 or not (text[position - 1].isalnum() or text[position - 1] == "_")
        opening = _OPEN.match(text, position) if standalone else None
        if opening:
            code = _style_code(opening[1], position)
            frames.append((code, position))
            if code is None:
                output.append(opening[0])
            else:
                output.append(code)
                active.append(code)
            position = opening.end()
            continue

        if char == "(":
            frames.append((None, position))
            output.append(char)
        elif char == ")" and frames:
            code, _ = frames.pop()
            if code is None:
                output.append(char)
            else:
                active.pop()
                output.append(RESET)
                output.extend(active)
        else:
            output.append(char)
        position += 1

    for code, start in frames:
        if code is not None:
            raise ValueError(f"unclosed style expression at position {start}")
    return "".join(output)
