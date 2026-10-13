import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "tools" / "review_source.py"


class SourceReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="source-review-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "src").mkdir()

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def run_review(self, format="json"):
        return subprocess.run([sys.executable, "-I", str(TOOL), "--root", str(self.root), "--format", format],
                              capture_output=True, text=True, encoding="utf-8")

    def test_valid_unicode_source_and_standard_imports(self):
        self.write("src/example/__init__.py", "from .helper import message\nimport sys\n")
        self.write("src/example/helper.py", "import msvcrt\nmessage = '你好 🌈 café'\n")
        self.write("tools/example.py", "import ast\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"checked": 3, "findings": []})

    def test_syntax_and_scope_errors(self):
        self.write("src/example/broken.py", "def broken(\n")
        self.write("examples/scope.py", "return 1\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(finding["code"] == "SYNTAX" for finding in findings))
        self.assertEqual({finding["path"] for finding in findings}, {"src/example/broken.py", "examples/scope.py"})

    def test_invalid_escape_warning(self):
        self.write("src/example/__init__.py", "text = '\\q'\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 1, result.stderr)
        finding = json.loads(result.stdout)["findings"][0]
        self.assertEqual(finding["code"], "SYNTAX_WARNING")
        self.assertEqual(finding["line"], 1)
        self.assertIn("escape", finding["message"])

    def test_external_imports_are_flagged_in_runtime_only(self):
        self.write("src/example/__init__.py", "import requests\nfrom third_party.client import Client\n")
        self.write("tests/example.py", "import optional_test_tool\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(finding["code"] == "NON_STDLIB_IMPORT" for finding in findings))
        self.assertTrue(all(finding["path"] == "src/example/__init__.py" for finding in findings))

    def test_missing_local_modules_and_relative_boundaries(self):
        self.write("src/example/__init__.py", "from .missing import value\nfrom ..outside import value\nimport example.absent\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)["findings"]
        self.assertEqual(len(findings), 3)
        self.assertTrue(all(finding["code"] == "MISSING_MODULE" for finding in findings))
        self.assertEqual([finding["line"] for finding in findings], [1, 2, 3])

    def test_imported_attributes_and_namespace_packages(self):
        self.write("src/example/__init__.py", "red = 'red'\nfrom . import red\n")
        self.write("src/example/nested/helper.py", "from .. import red\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["findings"], [])

    def test_review_does_not_execute_source(self):
        sentinel = self.root / "executed.txt"
        self.write("src/example/__init__.py", f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')\n")
        result = self.run_review()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())

    def test_text_diagnostics_and_exit_status(self):
        self.write("src/example/__init__.py", "import third_party\n")
        result = self.run_review(format="text")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("src/example/__init__.py:1:", result.stdout)
        self.assertIn("NON_STDLIB_IMPORT", result.stdout)
        self.assertIn("findings: 1", result.stdout)

    def test_invalid_root_is_an_invocation_error(self):
        (self.root / "src").rmdir()
        result = self.run_review()
        self.assertEqual(result.returncode, 2)
        self.assertIn("root must contain a src directory", result.stderr)

    def test_unicode_columns_count_characters(self):
        source = "text = '红 🌈'; import third_party\n"
        self.write("src/example/__init__.py", source)
        result = self.run_review()
        self.assertEqual(result.returncode, 1, result.stderr)
        finding = json.loads(result.stdout)["findings"][0]
        self.assertEqual(finding["column"], source.index("third_party") + 1)


if __name__ == "__main__":
    unittest.main()
