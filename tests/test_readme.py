import contextlib
import io
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import escape_colors


class ReadmeTests(unittest.TestCase):
    def test_python_examples_execute(self):
        readme = Path(__file__).resolve().parents[1] / "README.md"
        blocks = re.findall(r"^```python\n(.*?)^```", readme.read_text(encoding="utf-8"), re.M | re.S)
        self.assertGreaterEqual(len(blocks), 7)
        for number, block in enumerate(blocks, 1):
            with self.subTest(example=number), contextlib.redirect_stdout(io.StringIO()), \
                    patch.dict(os.environ, {}, clear=True), \
                    patch.object(escape_colors, "ESCAPE_COLOR_FORMAT", "unicode"):
                exec(compile(block, f"README.md example {number}", "exec"), {})


if __name__ == "__main__":
    unittest.main()
