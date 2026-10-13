"""Destination-specific terminal detection and Windows VT initialization."""

import ctypes
import os
import sys
from typing import TextIO

_PROCESSED_OUTPUT = 0x0001
_VIRTUAL_TERMINAL_PROCESSING = 0x0004


def init_windows(file: TextIO | None = None) -> bool:
    """Enable Windows VT output on a stream; return False when unavailable."""
    if os.name != "nt":
        return False
    stream = sys.stdout if file is None else file
    try:
        import msvcrt
        from ctypes import wintypes

        handle = msvcrt.get_osfhandle(stream.fileno())
        if handle in (-1, 0):
            return False
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        get_mode = kernel.GetConsoleMode
        get_mode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        get_mode.restype = wintypes.BOOL
        set_mode = kernel.SetConsoleMode
        set_mode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        set_mode.restype = wintypes.BOOL

        mode = wintypes.DWORD()
        if not get_mode(handle, ctypes.byref(mode)):
            return False
        desired = mode.value | _PROCESSED_OUTPUT | _VIRTUAL_TERMINAL_PROCESSING
        if desired == mode.value:
            return True
        return bool(set_mode(handle, desired))
    except (AttributeError, ImportError, OSError, TypeError, ValueError, OverflowError):
        return False


def color_enabled(stream: TextIO, color: bool | None) -> bool:
    if color is not None and not isinstance(color, bool):
        raise TypeError("color must be True, False, or None")
    if color is False:
        return False
    if color is True:
        if os.name == "nt":
            init_windows(stream)
        return True
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    try:
        if not stream.isatty():
            return False
    except (AttributeError, OSError, ValueError):
        return False
    return init_windows(stream) if os.name == "nt" else True
