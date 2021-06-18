from __future__ import annotations

import ctypes.wintypes
import logging

import win32event

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

logger = logging.getLogger(__name__)

STOP_EVENT = win32event.CreateEvent(None, 0, 0, None)
OTHER_EVENT = win32event.CreateEvent(None, 0, 0, None)

WIN_EVENT_PROC_TYPE = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)
"""The ctypes windows function that we send to `user32.SetWinEventHook`."""
