import unittest
from unittest.mock import patch

import escape_colors as colors


class ParserTests(unittest.TestCase):
    def test_requested_examples(self):
        self.assertEqual(colors.escape_ansi("blue(hello world)"), "\u001b[34mhello world\u001b[0m")
        self.assertEqual(
            colors.escape_ansi("blue(hello red(world))"),
            "\u001b[34mhello \u001b[31mworld\u001b[0m\u001b[34m\u001b[0m",
        )

    def test_color_restores_for_remaining_text(self):
        self.assertEqual(
            colors.escape_ansi("blue(before red(inner) after)"),
            "\u001b[34mbefore \u001b[31minner\u001b[0m\u001b[34m after\u001b[0m",
        )

    def test_restore_every_parent_attribute(self):
        self.assertEqual(
            colors.escape_ansi("bold(bg_blue(underline(red(x) y) z) done)"),
            "\u001b[1m\u001b[44m\u001b[4m\u001b[31mx\u001b[0m"
            "\u001b[1m\u001b[44m\u001b[4m y\u001b[0m\u001b[1m\u001b[44m z"
            "\u001b[0m\u001b[1m done\u001b[0m",
        )

    def test_all_named_colors_and_styles(self):
        for name in colors.__all__:
            code = getattr(colors, name)
            if isinstance(code, str) and code.startswith("\u001b[") and name not in ("escape", "reset"):
                with self.subTest(name=name):
                    self.assertEqual(colors.escape_ansi(f"{name}(text)"), code + "text" + colors.escape)

    def test_every_numeric_foreground_and_background(self):
        for index in range(256):
            with self.subTest(index=index):
                self.assertEqual(colors.escape_ansi(f"{index}(x)"), f"\u001b[38;5;{index}mx\u001b[0m")
                self.assertEqual(colors.escape_ansi(f"bg_{index}(x)"), f"\u001b[48;5;{index}mx\u001b[0m")

    def test_numeric_example_is_palette_color_not_sgr_parameter(self):
        self.assertEqual(colors.escape_ansi("15(white)"), "\u001b[38;5;15mwhite\u001b[0m")
        self.assertEqual(colors.escape_ansi("00015(white)"), "\u001b[38;5;15mwhite\u001b[0m")

    def test_out_of_range_colors_report_position(self):
        for token in ("256", "999", "-1", "bg_256", "bg_-1", "9" * 5000):
            with self.subTest(token=token[:20]):
                with self.assertRaisesRegex(ValueError, "0 and 255 at position 7"):
                    colors.escape_ansi(f"prefix {token}(x)")

    def test_large_leading_zero_color(self):
        self.assertEqual(colors.escape_ansi("0" * 5000 + "15(x)"), colors.color(15) + "x" + colors.escape)

    def test_plain_parentheses_inside_styles(self):
        self.assertEqual(colors.escape_ansi("blue(hello (world))"), colors.blue + "hello (world)" + colors.escape)

    def test_unknown_expressions_are_preserved(self):
        self.assertEqual(colors.escape_ansi("unknown(hello (world))"), "unknown(hello (world))")
        self.assertEqual(colors.escape_ansi("unknown(red(x))"), "unknown(" + colors.red + "x" + colors.escape + ")")
        self.assertEqual(colors.escape_ansi("unknown(unclosed"), "unknown(unclosed")

    def test_only_standalone_tokens_are_styles(self):
        text = "lightblue(x) caféblue(y) _blue(z) x15(t) α15(a) blue (spaced) BLUE(case)"
        self.assertEqual(colors.escape_ansi(text), text)

    def test_parentheses_and_backslash_quoting(self):
        self.assertEqual(colors.escape_ansi(r"blue\(hello\)"), "blue(hello)")
        self.assertEqual(colors.escape_ansi(r"blue(a\) b\( c\\d)"), colors.blue + "a) b( c\\d" + colors.escape)
        self.assertEqual(colors.escape_ansi(r"\n \t \u263a C:\Users\name"), r"\n \t \u263a C:\Users\name")
        self.assertEqual(colors.escape_ansi("trailing\\"), "trailing\\")

    def test_unclosed_recognized_expression(self):
        for text, position in (("red(x", 0), ("hello bold(red(x)", 6), ("unknown(blue(x", 8), ("red((x)", 0)):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, f"unclosed style expression at position {position}"):
                    colors.escape_ansi(text)

    def test_unmatched_literal_closing_parentheses(self):
        self.assertEqual(colors.escape_ansi("a) red(x))"), "a) " + colors.red + "x" + colors.escape + ")")

    def test_adjacent_styles_empty_styles_and_plain_text(self):
        self.assertEqual(colors.escape_ansi("red()blue(x) plain"), colors.red + colors.escape + colors.blue + "x" + colors.escape + " plain")
        self.assertEqual(colors.escape_ansi(""), "")
        self.assertEqual(colors.escape_ansi("plain"), "plain")

    def test_unicode_and_multiline_content(self):
        self.assertEqual(colors.escape_ansi("blue(你好 🌈\n\tcafé é)"), colors.blue + "你好 🌈\n\tcafé é" + colors.escape)

    def test_deep_nesting_avoids_recursion_limit(self):
        depth = 1100
        rendered = colors.escape_ansi("bold(" * depth + "deep" + ")" * depth)
        self.assertEqual(colors.strip_ansi(rendered), "deep")
        self.assertTrue(rendered.endswith(colors.escape))

    def test_runtime_equal_for_all_formats(self):
        for format in ("unicode", "hex", "octal"):
            with self.subTest(format=format):
                self.assertEqual(colors.escape_ansi("red(x)", format=format), colors.red + "x" + colors.escape)

    def test_literal_output_and_format_precedence(self):
        with patch.object(colors, "ESCAPE_COLOR_FORMAT", "octal"):
            self.assertEqual(colors.escape_ansi("blue(你好)", literal=True), r"\033[34m你好\033[0m")
            self.assertEqual(colors.escape_ansi("blue(你好)", format="hex", literal=True), r"\x1b[34m你好\x1b[0m")

    def test_decoding_is_opt_in(self):
        text = r"\u001b[31m紅\033[0m"
        self.assertEqual(colors.escape_ansi(text), text)
        self.assertEqual(colors.escape_ansi(text, decode=True), colors.red + "紅" + colors.escape)
        self.assertEqual(colors.escape_ansi(text, decode=True, literal=True, format="hex"), r"\x1b[31m紅\x1b[0m")

    def test_invalid_arguments(self):
        for text in (None, b"red(x)", 1):
            with self.assertRaises(TypeError):
                colors.escape_ansi(text)
        with self.assertRaises(ValueError):
            colors.escape_ansi("plain", format="invalid")
        with self.assertRaises(TypeError):
            colors.escape_ansi("plain", literal=1)
        with self.assertRaises(TypeError):
            colors.escape_ansi("plain", decode="yes")


if __name__ == "__main__":
    unittest.main()
