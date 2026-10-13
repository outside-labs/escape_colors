"""Select Graphic Rendition codes and indexed palette helpers."""

ESC = "\u001b"
RESET = f"{ESC}[0m"


def _sgr(*parameters: int) -> str:
    return f"{ESC}[{';'.join(map(str, parameters))}m"


def _palette_index(index: int) -> int:
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError("color index must be an integer")
    if not 0 <= index <= 255:
        raise ValueError("color index must be between 0 and 255")
    return index


def color(index: int) -> str:
    """Return the foreground SGR sequence for palette index 0 through 255."""
    return _sgr(38, 5, _palette_index(index))


def background(index: int) -> str:
    """Return the background SGR sequence for palette index 0 through 255."""
    return _sgr(48, 5, _palette_index(index))


COLOR_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
NAMED_CODES = {}
for _offset, _name in enumerate(COLOR_NAMES):
    NAMED_CODES[_name] = _sgr(30 + _offset)
    NAMED_CODES[f"bright_{_name}"] = _sgr(90 + _offset)
    NAMED_CODES[f"bg_{_name}"] = _sgr(40 + _offset)
    NAMED_CODES[f"bg_bright_{_name}"] = _sgr(100 + _offset)

for _name, _parameter in {
    "bold": 1,
    "faint": 2,
    "dim": 2,
    "italic": 3,
    "italics": 3,
    "underline": 4,
    "double_underline": 21,
    "blink": 5,
    "reverse": 7,
    "conceal": 8,
    "strike": 9,
    "strikethrough": 9,
    "overline": 53,
}.items():
    NAMED_CODES[_name] = _sgr(_parameter)

for _font in range(10):
    NAMED_CODES[f"font{_font}"] = _sgr(10 + _font)
