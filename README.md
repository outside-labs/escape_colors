# Escape Colors

Readable ANSI colors and nested text styles for Python 3.14+, with no runtime
dependencies.

```python
from escape_colors import ansi_print, blue, escape, escape_ansi, init_windows

ansi_print("blue(hello world)")
ansi_print("bold(blue(hello red(world) again))")

# For direct print/f-string output on Windows:
init_windows()
print(escape_ansi("blue(hello red(world))"))
print(f"{blue}hello world{escape}")
```

`escape_ansi` returns a string containing real ANSI SGR codes. `ansi_print` renders
markup and chooses whether to use color for the destination stream. Redirected
output is plain by default; use `color=True` to force ANSI sequences.

## Install and develop

Install from PyPI with Python 3.14 or later:

```sh
python -m pip install escape-colors
```

From this checkout:

```sh
uv sync --locked
uv run python examples/basic.py
python tools/review_source.py
uv run python -m unittest discover -s tests -v
uv build
uv run python tools/verify_distribution.py
```

Install a built wheel into another Python environment with
`uv pip install /path/to/escape_colors-0.1.0-py3-none-any.whl`.

## Releases

Publish a GitHub release with a tag matching the package version, such as
`v0.1.0`. `.github/workflows/release.yaml` tests and verifies the distributions
before publishing to PyPI through the `pypi` environment using Trusted Publishing.
The workflow can also be run manually against an existing release tag.

## Colors and styles

The 16 named foreground colors are `black`, `red`, `green`, `yellow`, `blue`,
`magenta`, `cyan`, and `white`, plus `bright_black`, `bright_red`, `bright_green`,
`bright_yellow`, `bright_blue`, `bright_magenta`, `bright_cyan`, and `bright_white`.
Add `bg_` for a background: `bg_blue`, `bg_bright_white`, and so on. Each name is
both a markup expression and an importable ANSI string constant.

```python
from escape_colors import background, color, escape, escape_ansi

text = escape_ansi("bright_blue(hello bg_white(world))")
indexed = escape_ansi("15(white) 196(red) bg_232(dark background)")
direct = f"{color(196)}red {background(232)}on dark{escape}"
```

Numeric markup selects a **256-color palette index**, not an SGR parameter:
`15(text)` means `ESC[38;5;15m`, and `bg_15(text)` means `ESC[48;5;15m`.
Indices 0–15 address the base palette, 16–231 the color cube, and 232–255 the
grayscale ramp. The terminal controls the actual palette and appearance.
`color(index)` and `background(index)` accept integers 0–255; booleans, floats,
strings, and values outside that range are rejected.

| Expression / constant | SGR | Effect |
| --- | --- | --- |
| `bold` | 1 | Bold/increased intensity |
| `faint`, `dim` | 2 | Decreased intensity |
| `italic`, `italics` | 3 | Italic |
| `underline` | 4 | Underline |
| `double_underline` | 21 | Double underline |
| `blink` | 5 | Slow blink |
| `reverse` | 7 | Swap foreground/background |
| `conceal` | 8 | Conceal text |
| `strike`, `strikethrough` | 9 | Strike through |
| `overline` | 53 | Overline |
| `font0` … `font9` | 10 … 19 | Default/alternative terminal font |
| `escape`, `reset` | 0 | Reset constant for direct output |

Use `bold(text)`, `underline(text)`, `italics(text)`, or combine them by nesting.
When an inner expression closes, its enclosing styles are restored. A top-level
expression ends with a reset. Font selection, italics, blink, and other attributes
depend on terminal support. SGR does not select arbitrary installed typefaces or
font sizes; older terminals may treat SGR 21 as an intensity change.
`escape` and `reset` are constants, rather than markup expressions.

## Grammar and literal text

Markup is case-sensitive. A standalone ASCII name or decimal index immediately
followed by `(` opens an expression. Whitespace between a name and `(` makes it
ordinary text. Unknown names and ordinary parentheses remain in the output;
recognized expressions inside unknown parentheses still work.

```python
from escape_colors import escape_ansi, strip_ansi

assert strip_ansi(escape_ansi("blue(hello (world))")) == "hello (world)"
assert escape_ansi("unknown(hello)") == "unknown(hello)"
assert escape_ansi(r"blue\(literal\)") == "blue(literal)"
assert strip_ansi(escape_ansi(r"blue(a\) b\( c\\d)")) == "a) b( c\\d"
```

`\(` and `\)` quote parentheses; `\\` quotes a backslash. Other backslashes,
Unicode characters, line breaks, and tabs are preserved. Recognized unclosed
expressions and invalid numeric color indices raise `ValueError` with a
zero-based character position. Unmatched ordinary parentheses remain literal.
The parser is iterative and does not evaluate Python or depend on its recursion
limit. Existing raw SGR codes pass through; scope restoration tracks markup
styles, rather than arbitrary control sequences embedded in the input.

## Unicode, hex, and octal notation

These three Python literals hold exactly the same one-character string:

```python
assert "\u001b" == "\x1b" == "\033" == chr(27)
```

The spelling is consumed by Python when it creates the string. No format warning
is emitted, and normal terminal output is identical for all three choices.
`ESCAPE_COLOR_FORMAT` controls the visible representation produced by
`literal=True` or `format_ansi`, and defaults to `"unicode"`.

```python
import escape_colors

escape_colors.ESCAPE_COLOR_FORMAT = "octal"
assert escape_colors.escape_ansi("blue(hello)", literal=True) == r"\033[34mhello\033[0m"
assert escape_colors.escape_ansi("blue(hello)", literal=True, format="hex") == r"\x1b[34mhello\x1b[0m"

# The live runtime string always contains actual ESC characters.
assert escape_colors.escape_ansi("blue(hello)") == "\u001b[34mhello\u001b[0m"
escape_colors.ESCAPE_COLOR_FORMAT = "unicode"
```

Alternatively set the environment variable **before importing**:

```sh
ESCAPE_COLOR_FORMAT=octal uv run python examples/basic.py
```

On PowerShell, use `$env:ESCAPE_COLOR_FORMAT = 'octal'` before starting Python.
Accepted values are exactly `unicode`, `hex`, and `octal`. A per-call `format`
overrides the package setting. Assign `escape_colors.ESCAPE_COLOR_FORMAT` on the
module; assigning a separately imported local name does not update the module.
Invalid settings raise an error when rendering or serializing.

```python
from escape_colors import blue, escape, escape_ansi, format_ansi, normalize_ansi

assert format_ansi(f"{blue}café{escape}", format="unicode") == r"\u001b[34mcafé\u001b[0m"
assert normalize_ansi(r"\x1b[34mcafé\033[0m") == f"{blue}café{escape}"
assert escape_ansi(r"\u001b[34mcafé\033[0m", decode=True) == f"{blue}café{escape}"
```

Textual notation decoding is opt-in. `normalize_ansi` and `decode=True` recognize
only `\u001b`, `\x1b` (also with uppercase `B`), and `\033` followed by complete
numeric SGR sequences. They do not decode general Python escapes, change Unicode,
or decode a backslash-prefixed spelling. Literal output replaces ESC only: it is
readable escape notation, not a complete quoted/escaped Python string literal.

## Printing and Windows

`ansi_print(*objects, sep=" ", end="\n", file=None, flush=False, color=None)`
renders each object's string representation and supports the usual `print`
arguments, including `sep=None` and `end=None`. It returns `None`.

```python
import io
from escape_colors import ansi_print

capture = io.StringIO()
ansi_print("blue(hello)", "bold(world)", sep=" / ", end="!", file=capture)
assert capture.getvalue() == "hello / world!"
ansi_print("196(forced ANSI)", color=True)
ansi_print("blue(plain text)", color=False)
```

- `color=None`: use color for a TTY unless `NO_COLOR` is nonempty or `TERM=dumb`.
  Streams without a working `isatty()` get plain text. Windows also needs
  successful VT initialization.
- `color=True`: attempt Windows initialization and emit ANSI, even on redirection
  or if initialization fails. This overrides environment color preferences.
- `color=False`: remove rendered SGR codes, including existing SGR in objects,
  separators, and endings.

`ansi_print` initializes Windows automatically for the destination stream.
`init_windows(file=None)` is available for direct `print`/f-string output and can
also initialize stderr or another console stream. It preserves existing console
mode bits and enables processed output and virtual-terminal processing. Repeated
calls are safe. It returns `True` on Windows success and `False` on other systems,
unsupported consoles, or redirected/invalid handles. Importing the module does
not change console state. Obsolete Windows consoles without VT support are not
emulated; automatic printing uses plain text there.

`strip_ansi` removes numeric SGR sequences only. These APIs format text and do not
sanitize arbitrary terminal control commands in untrusted input.

## Verification and references

`python tools/review_source.py` performs a static review using only Python's
standard library. It checks first-party Python files for syntax errors and
`SyntaxWarning`s, checks runtime imports against the standard library and local
modules, and reports missing internal modules. It compiles source for validation
without executing the inspected code. Use `--format json` for structured results
or `--root /path/to/checkout` for another source tree. Findings exit with status 1;
invalid invocation exits with status 2. Review covers ordinary import statements,
including conditional imports; dynamic imports and imported attributes are
outside these checks. Runtime behavior is covered by the test suite.

CI tests Python 3.14 on Linux, macOS, and Windows, builds the wheel and source
distribution, and runs the suite from freshly installed wheel artifacts outside
the checkout. The verification script also rebuilds a wheel from the source
archive. Tests cover nested restoration, every indexed color, notation, Unicode,
printing, and Windows API behavior. Visual support still depends on the terminal.

- [Python string escapes](https://docs.python.org/3.14/reference/lexical_analysis.html#escape-sequences)
- [ANSI escape code overview](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Xterm control sequences](https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)
- [Windows VT sequences](https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences)
- [SetConsoleMode](https://learn.microsoft.com/en-us/windows/console/setconsolemode)
