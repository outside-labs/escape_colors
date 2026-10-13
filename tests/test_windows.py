import ctypes
import io
import os
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

from escape_colors import _terminal, init_windows


class WindowsTests(unittest.TestCase):
    def setUp(self):
        self.stream = Mock()
        self.stream.fileno.return_value = 1
        self.msvcrt = Mock()
        self.msvcrt.get_osfhandle.return_value = 123
        self.kernel = Mock()
        self.mode = 0x0020

        def get_mode(handle, pointer):
            pointer._obj.value = self.mode
            return 1

        self.kernel.GetConsoleMode.side_effect = get_mode
        self.kernel.SetConsoleMode.return_value = 1
        self.contexts = (
            patch.object(_terminal.os, "name", "nt"),
            patch.dict(sys.modules, {"msvcrt": self.msvcrt}),
            patch.object(ctypes, "WinDLL", return_value=self.kernel, create=True),
        )
        for context in self.contexts:
            context.start()
            self.addCleanup(context.stop)

    def test_enable_both_flags_and_preserve_original_bits(self):
        self.assertTrue(init_windows(self.stream))
        self.msvcrt.get_osfhandle.assert_called_once_with(1)
        self.kernel.GetConsoleMode.assert_called_once()
        self.kernel.SetConsoleMode.assert_called_once_with(123, 0x0025)

    def test_already_initialized_does_not_set_mode_again(self):
        self.mode = 0x0025
        self.assertTrue(init_windows(self.stream))
        self.assertTrue(init_windows(self.stream))
        self.kernel.SetConsoleMode.assert_not_called()

    def test_vt_without_processed_output_adds_processed_flag(self):
        self.mode = 0x0004
        self.assertTrue(init_windows(self.stream))
        self.kernel.SetConsoleMode.assert_called_once_with(123, 0x0005)

    def test_stdout_and_stderr_are_independent(self):
        stderr = Mock()
        stderr.fileno.return_value = 2
        self.msvcrt.get_osfhandle.side_effect = lambda fd: 100 + fd
        with patch("sys.stdout", self.stream):
            self.assertTrue(init_windows())
        self.assertTrue(init_windows(stderr))
        self.assertEqual([call.args for call in self.kernel.SetConsoleMode.call_args_list], [(101, 0x0025), (102, 0x0025)])

    def test_invalid_handles(self):
        for handle in (-1, 0):
            with self.subTest(handle=handle):
                self.msvcrt.get_osfhandle.return_value = handle
                self.assertFalse(init_windows(self.stream))
        self.kernel.GetConsoleMode.assert_not_called()

    def test_missing_or_invalid_file_descriptor(self):
        self.assertFalse(init_windows(io.StringIO()))
        self.stream.fileno.side_effect = OSError("closed")
        self.assertFalse(init_windows(self.stream))
        self.kernel.GetConsoleMode.assert_not_called()

    def test_handle_lookup_failure(self):
        self.msvcrt.get_osfhandle.side_effect = OSError("invalid descriptor")
        self.assertFalse(init_windows(self.stream))
        self.kernel.GetConsoleMode.assert_not_called()

    def test_redirected_handle_and_api_failure(self):
        self.kernel.GetConsoleMode.side_effect = None
        self.kernel.GetConsoleMode.return_value = 0
        self.assertFalse(init_windows(self.stream))
        self.kernel.SetConsoleMode.assert_not_called()

    def test_set_mode_failure(self):
        self.kernel.SetConsoleMode.return_value = 0
        self.assertFalse(init_windows(self.stream))

    def test_api_load_failure(self):
        ctypes.WinDLL.side_effect = OSError("unavailable")
        self.assertFalse(init_windows(self.stream))

    def test_non_windows_is_a_noop(self):
        with patch.object(_terminal.os, "name", "posix"):
            self.assertFalse(init_windows(self.stream))
        self.kernel.GetConsoleMode.assert_not_called()


class PlatformIntegrationTests(unittest.TestCase):
    def test_import_does_not_load_windows_console_api(self):
        program = """
import ctypes
def fail(*args, **kwargs):
    raise AssertionError('console initialized at import')
ctypes.WinDLL = fail
import escape_colors
"""
        result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(os.name == "nt", "requires Windows")
    def test_actual_windows_apis_and_stream(self):
        import msvcrt

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.assertTrue(callable(kernel.GetConsoleMode))
        self.assertTrue(callable(kernel.SetConsoleMode))
        self.assertIsInstance(msvcrt.get_osfhandle(sys.stdout.fileno()), int)
        self.assertIsInstance(init_windows(sys.stdout), bool)
        self.assertFalse(init_windows(io.StringIO()))


if __name__ == "__main__":
    unittest.main()
