import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import escape_colors as colors


class NotationTests(unittest.TestCase):
    def test_python_spellings_are_equal_without_warnings(self):
        self.assertEqual("\u001b[31m", "\x1b[31m")
        self.assertEqual("\u001b[31m", "\033[31m")

    def test_three_literal_formats_preserve_unicode(self):
        text = "\u001b[31m紅 🌈 café\n\u001b[0m"
        for format, spelling in (("unicode", r"\u001b"), ("hex", r"\x1b"), ("octal", r"\033")):
            with self.subTest(format=format):
                literal = colors.format_ansi(text, format=format)
                self.assertEqual(literal, f"{spelling}[31m紅 🌈 café\n{spelling}[0m")
                self.assertEqual(colors.normalize_ansi(literal), text)

    def test_default_is_unicode(self):
        with patch.object(colors, "ESCAPE_COLOR_FORMAT", "unicode"):
            self.assertEqual(colors.format_ansi(colors.blue), r"\u001b[34m")

    def test_package_setting_and_explicit_override(self):
        with patch.object(colors, "ESCAPE_COLOR_FORMAT", "octal"):
            self.assertEqual(colors.format_ansi(colors.blue), r"\033[34m")
            self.assertEqual(colors.format_ansi(colors.blue, format="hex"), r"\x1b[34m")

    def test_environment_before_import(self):
        result = subprocess.run(
            [sys.executable, "-c", "import escape_colors as e; print(e.format_ansi(e.red))"],
            env={**os.environ, "ESCAPE_COLOR_FORMAT": "octal"},
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(result.stdout.strip(), r"\033[31m")

    def test_normalize_mixed_spellings_and_existing_sgr(self):
        text = r"\u001B[1m\x1B[31m\033[0m" + "\u001b[4m"
        self.assertEqual(colors.normalize_ansi(text), "\u001b[1m\u001b[31m\u001b[0m\u001b[4m")
        self.assertEqual(colors.normalize_ansi(r"\033[m"), "\u001b[m")

    def test_normalization_does_not_decode_ordinary_text(self):
        text = r"café \n \t \u263a \x41 \033 \x1b[31 \u001b[31x \\u001b[31m"
        self.assertEqual(colors.normalize_ansi(text), text)

    def test_strip_sgr_only(self):
        text = "\u001b[38;5;15mhello\u001b[0m\u001b[2J"
        self.assertEqual(colors.strip_ansi(text), "hello\u001b[2J")
        self.assertEqual(colors.strip_ansi("\u001b[mplain\u001b[1;4m"), "plain")
        self.assertEqual(colors.strip_ansi(r"\u001b[31mraw"), r"\u001b[31mraw")

    def test_invalid_formats(self):
        for format in ("", "bytes", "UNICODE"):
            with self.subTest(format=format):
                with self.assertRaisesRegex(ValueError, "unicode.*hex.*octal"):
                    colors.format_ansi("hello", format=format)
        for format in (False, 1, []):
            with self.subTest(format=format):
                with self.assertRaises(TypeError):
                    colors.format_ansi("hello", format=format)

    def test_text_type_validation(self):
        for helper in (colors.format_ansi, colors.normalize_ansi, colors.strip_ansi):
            for text in (None, 1, b"text"):
                with self.subTest(helper=helper, text=text):
                    with self.assertRaises(TypeError):
                        helper(text)


if __name__ == "__main__":
    unittest.main()
