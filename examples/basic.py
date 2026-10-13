"""Run with uv run python examples/basic.py."""

from escape_colors import (
    ansi_print,
    blue,
    escape,
    escape_ansi,
    format_ansi,
    init_windows,
)


def main() -> None:
    ansi_print("blue(hello world)")
    ansi_print("bold(blue(hello red(world) again))")
    ansi_print("15(indexed white) 196(indexed red) bg_232(dark background)")
    ansi_print("underline(italics(你好 🌈 café))")

    init_windows()
    print(escape_ansi("blue(hello red(world))"))
    print(f"{blue}hello world{escape}")

    for notation in ("unicode", "hex", "octal"):
        print(notation, format_ansi(escape_ansi("red(literal example)"), format=notation))


if __name__ == "__main__":
    main()
