import unittest

import escape_colors as colors


class CodesTests(unittest.TestCase):
    def test_requested_f_string(self):
        from escape_colors import blue, escape

        self.assertEqual(f"{blue}hello world{escape}", "\u001b[34mhello world\u001b[0m")

    def test_normal_and_bright_foregrounds_and_backgrounds(self):
        names = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
        for index, name in enumerate(names):
            for prefix, start in (("", 30), ("bright_", 90), ("bg_", 40), ("bg_bright_", 100)):
                with self.subTest(name=prefix + name):
                    self.assertEqual(getattr(colors, prefix + name), f"\u001b[{start + index}m")

    def test_font_attributes(self):
        expected = {
            "bold": 1, "faint": 2, "dim": 2, "italic": 3, "italics": 3,
            "underline": 4, "double_underline": 21, "blink": 5, "reverse": 7,
            "conceal": 8, "strike": 9, "strikethrough": 9, "overline": 53,
        }
        for name, code in expected.items():
            with self.subTest(name=name):
                self.assertEqual(getattr(colors, name), f"\u001b[{code}m")
        for font in range(10):
            with self.subTest(font=font):
                self.assertEqual(getattr(colors, f"font{font}"), f"\u001b[{10 + font}m")

    def test_every_indexed_color(self):
        for index in range(256):
            with self.subTest(index=index):
                self.assertEqual(colors.color(index), f"\u001b[38;5;{index}m")
                self.assertEqual(colors.background(index), f"\u001b[48;5;{index}m")

    def test_invalid_palette_indices(self):
        for helper in (colors.color, colors.background):
            for value in (True, False, None, "15", 15.0, [], object()):
                with self.subTest(helper=helper, value=value):
                    with self.assertRaises(TypeError):
                        helper(value)
            for value in (-1, 256, 10**100):
                with self.subTest(helper=helper, value=value):
                    with self.assertRaises(ValueError):
                        helper(value)

    def test_reset_aliases(self):
        self.assertEqual(colors.escape, "\u001b[0m")
        self.assertEqual(colors.reset, colors.escape)

    def test_all_public_names_exist(self):
        self.assertEqual(len(colors.__all__), len(set(colors.__all__)))
        for name in colors.__all__:
            self.assertTrue(hasattr(colors, name), name)


if __name__ == "__main__":
    unittest.main()
