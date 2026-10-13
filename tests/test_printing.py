import io
import os
import unittest
from unittest.mock import Mock, patch

import escape_colors as colors
from escape_colors import _terminal


class TTY(io.StringIO):
    def isatty(self):
        return True


class PrintingTests(unittest.TestCase):
    def test_redirected_stream_defaults_to_plain(self):
        stream = io.StringIO()
        self.assertIsNone(colors.ansi_print("blue(hello red(world))", file=stream))
        self.assertEqual(stream.getvalue(), "hello world\n")

    def test_force_color(self):
        stream = io.StringIO()
        with patch.dict(os.environ, {"NO_COLOR": "1", "TERM": "dumb"}):
            colors.ansi_print("blue(hello)", file=stream, color=True)
        self.assertEqual(stream.getvalue(), colors.blue + "hello" + colors.escape + "\n")

    def test_explicit_plain_removes_markup_and_existing_sgr(self):
        stream = TTY()
        colors.ansi_print("bold(hello)", colors.red + "world" + colors.escape,
                         sep=colors.blue + "-", end=colors.escape, file=stream, color=False)
        self.assertEqual(stream.getvalue(), "hello-world")

    def test_automatic_posix_tty(self):
        stream = TTY()
        with patch.dict(os.environ, {}, clear=True), patch.object(_terminal.os, "name", "posix"):
            colors.ansi_print("bold(x)", file=stream)
        self.assertEqual(stream.getvalue(), colors.bold + "x" + colors.escape + "\n")

    def test_no_color_and_dumb_terminal(self):
        for env in ({"NO_COLOR": "1"}, {"TERM": "dumb"}):
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True):
                stream = TTY()
                colors.ansi_print("red(x)", file=stream)
                self.assertEqual(stream.getvalue(), "x\n")

    def test_empty_no_color_does_not_disable_color(self):
        stream = TTY()
        with patch.dict(os.environ, {"NO_COLOR": ""}, clear=True), patch.object(_terminal.os, "name", "posix"):
            colors.ansi_print("red(x)", file=stream)
        self.assertEqual(stream.getvalue(), colors.red + "x" + colors.escape + "\n")

    def test_missing_or_failing_isatty(self):
        for stream in (Mock(spec=["write", "flush"]), Mock()):
            if hasattr(stream, "isatty"):
                stream.isatty.side_effect = OSError("not a console")
            colors.ansi_print("blue(x)", file=stream)
            self.assertEqual("".join(call.args[0] for call in stream.write.call_args_list), "x\n")

    def test_multiple_objects_separators_and_flush(self):
        stream = Mock(spec=["write", "flush", "isatty"])
        stream.isatty.return_value = False
        colors.ansi_print("bold(x)", 15, None, sep=" | ", end="!", file=stream, flush=True)
        self.assertEqual("".join(call.args[0] for call in stream.write.call_args_list), "x | 15 | None!")
        stream.flush.assert_called_once_with()

    def test_none_sep_and_end_match_print(self):
        actual = io.StringIO()
        expected = io.StringIO()
        colors.ansi_print("red(a)", "blue(b)", sep=None, end=None, file=actual)
        print("a", "b", sep=None, end=None, file=expected)
        self.assertEqual(actual.getvalue(), expected.getvalue())

    def test_no_objects_and_custom_object(self):
        class Message:
            def __str__(self):
                return "blue(hello)"

        stream = io.StringIO()
        colors.ansi_print(file=stream)
        colors.ansi_print(Message(), file=stream)
        self.assertEqual(stream.getvalue(), "\nhello\n")

    def test_current_stdout_resolved_at_call_time(self):
        stream = io.StringIO()
        with patch("sys.stdout", stream):
            colors.ansi_print("blue(x)")
        self.assertEqual(stream.getvalue(), "x\n")

    def test_disabled_stdout(self):
        with patch("sys.stdout", None):
            self.assertIsNone(colors.ansi_print("red(x)"))

    def test_invalid_separators_end_and_color(self):
        for kwargs in ({"sep": 1}, {"end": []}, {"color": 1}, {"color": "auto"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                colors.ansi_print("blue(x)", file=io.StringIO(), **kwargs)

    def test_invalid_markup_writes_nothing(self):
        stream = io.StringIO()
        with self.assertRaises(ValueError):
            colors.ansi_print("red(valid)", "blue(unclosed", file=stream)
        self.assertEqual(stream.getvalue(), "")

    def test_windows_auto_initialization_success_and_failure(self):
        for success in (True, False):
            stream = TTY()
            with self.subTest(success=success), patch.dict(os.environ, {}, clear=True), \
                    patch.object(_terminal.os, "name", "nt"), \
                    patch.object(_terminal, "init_windows", return_value=success) as init:
                colors.ansi_print("red(x)", file=stream)
                init.assert_called_once_with(stream)
            self.assertEqual(stream.getvalue(), (colors.red + "x" + colors.escape if success else "x") + "\n")

    def test_forced_color_attempts_windows_init_but_keeps_sequences_on_failure(self):
        stream = TTY()
        with patch.object(_terminal.os, "name", "nt"), \
                patch.object(_terminal, "init_windows", return_value=False) as init:
            colors.ansi_print("red(x)", color=True, file=stream)
            init.assert_called_once_with(stream)
        self.assertEqual(stream.getvalue(), colors.red + "x" + colors.escape + "\n")

    def test_plain_and_redirected_output_do_not_initialize_windows(self):
        with patch.object(_terminal.os, "name", "nt"), patch.object(_terminal, "init_windows") as init:
            colors.ansi_print("red(x)", file=io.StringIO())
            colors.ansi_print("red(x)", file=TTY(), color=False)
            init.assert_not_called()


if __name__ == "__main__":
    unittest.main()
