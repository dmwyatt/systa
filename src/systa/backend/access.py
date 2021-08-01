import ctypes
from typing import Iterator, List, Tuple

import win32api
import win32con
import win32gui
import win32process
from pynput.keyboard import Controller, Key

from systa.exceptions import NoMatchingWindowError

user32 = ctypes.WinDLL("user32", use_last_error=True)

MIN_ALL = 419
MIN_ALL_UNDO = 416


def get_window_titles() -> Iterator[Tuple[str, int]]:
    for hwnd in get_handles():
        length = user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        yield buffer.value, hwnd


def get_handles() -> List[int]:
    # noinspection PyPep8Naming
    EnumWindowsProc = ctypes.WINFUNCTYPE(
        ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    )
    handles = []

    def foreach_win(hwnd: int, _):
        handles.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(foreach_win), 0)

    return handles


TASKBAR_CLASSNAME = "Shell_TrayWnd"


def flash_window(handle: int, flags: int, count: int, timeout: int):
    win32gui.FlashWindowEx(handle, flags, count, timeout)


def set_disabled(handle: int) -> None:
    user32.EnableWindow(handle, 0)


def set_enabled(handle: int) -> None:
    user32.EnableWindow(handle, 1)


def get_class_name(handle: int) -> str:
    buffer = ctypes.create_unicode_buffer(100)
    user32.GetClassNameW(handle, buffer, 99)
    return buffer.value


def get_title(handle: int) -> str:
    length = user32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(handle, buffer, length + 1)
    return buffer.value


def undo_set_all_windows_minimized() -> None:
    win32gui.SendMessage(get_sys_tray_handle, win32con.WM_COMMAND, MIN_ALL_UNDO, 0)


def set_all_windows_minimized() -> None:
    win32gui.SendMessage(get_sys_tray_handle(), win32con.WM_COMMAND, MIN_ALL, 0)


def get_process_path(handle: int) -> str:
    handle = win32api.OpenProcess(
        win32con.PROCESS_ALL_ACCESS, False, get_process_id(handle)
    )
    return win32process.GetModuleFileNameEx(handle, 0)


def set_win_dimensions(handle: int, width: int, height: int) -> None:
    win32gui.SetWindowPos(
        handle,
        win32con.HWND_TOP,
        0,
        0,
        width,
        height,
        win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE,
    )


def get_win_height(handle: int) -> int:
    _, top_y, _, bottom_y = _get_window_rect(handle)
    return bottom_y - top_y


def get_win_width(handle: int) -> int:
    left_x, _, right_x, _ = _get_window_rect(handle)
    return right_x - left_x


def set_win_position(handle: int, x: int, y: int) -> None:
    win32gui.SetWindowPos(
        handle,
        win32con.HWND_TOP,  # ignored
        x,
        y,
        4000,  # ignored
        4000,  # ignored
        win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE,
    )


def get_position(handle: int) -> Tuple[int, int]:
    x, y, _, _ = _get_window_rect(handle)
    return x, y


def _get_window_rect(handle: int) -> Tuple[int, int, int, int]:
    return win32gui.GetWindowRect(handle)


def close_window(handle: int) -> None:
    win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)


def bring_to_top(handle: int):
    win32gui.ShowWindow(handle, win32con.SW_RESTORE)
    kb = Controller()
    kb.press(Key.alt)
    win32gui.SetForegroundWindow(handle)
    kb.release(Key.alt)
    # win32gui.SetWindowPos(
    #     handle,
    #     win32con.HWND_NOTOPMOST,
    #     0,
    #     0,
    #     0,
    #     0,
    #     win32con.SWP_NOMOVE + win32con.SWP_NOSIZE,
    # )
    # win32gui.SetWindowPos(
    #     handle,
    #     win32con.HWND_TOPMOST,
    #     0,
    #     0,
    #     0,
    #     0,
    #     win32con.SWP_NOMOVE + win32con.SWP_NOSIZE,
    # )
    # win32gui.SetWindowPos(
    #     handle,
    #     win32con.HWND_NOTOPMOST,
    #     0,
    #     0,
    #     0,
    #     0,
    #     win32con.SWP_SHOWWINDOW + win32con.SWP_NOMOVE + win32con.SWP_NOSIZE,
    # )


def activate_window(handle: int) -> None:
    """Activate/focus a window.  Doesn't always work!
    :rtype: object
    """
    bring_to_top(handle)


def restore(handle: int) -> None:
    win32gui.ShowWindow(handle, win32con.SW_RESTORE)


def set_maximized(handle: int) -> None:
    win32gui.ShowWindow(handle, win32con.SW_MAXIMIZE)


def get_is_maximized(handle: int) -> bool:
    return win32gui.GetWindowPlacement(handle)[1] == win32con.SW_SHOWMAXIMIZED


def set_minimized(handle: int) -> None:
    return win32gui.ShowWindow(handle, win32con.SW_MINIMIZE)


def get_is_minimized(handle: int) -> bool:
    return bool(win32gui.IsIconic(handle))


def get_is_enabled(handle: int) -> bool:
    return bool(win32gui.IsWindowEnabled(handle))


def set_shown(handle: int) -> None:
    win32gui.ShowWindow(handle, win32con.SW_SHOW)


def set_hidden(handle: int) -> None:
    win32gui.ShowWindow(handle, win32con.SW_HIDE)


def get_is_visible(handle: int) -> bool:
    return bool(win32gui.IsWindowVisible(handle))


def get_exists(handle: int) -> bool:
    return bool(win32gui.IsWindow(handle))


def get_is_active(handle: int) -> bool:
    return win32gui.GetForegroundWindow() == handle


def get_titles_and_handles() -> Iterator[Tuple[str, int]]:
    return get_window_titles()


def get_handle(title: str) -> Iterator[int]:
    found = False
    for title_, handle in get_window_titles():
        if title_ == title:
            found = True
            yield handle

    if not found:
        raise NoMatchingWindowError(f"No window matching title: '{title}'")


def set_title(handle: int, title: str) -> None:
    win32gui.SetWindowText(handle, title)


def get_process_id(handle: int) -> int:
    return win32process.GetWindowThreadProcessId(handle)[1]


def get_sys_tray_handle() -> int:
    return win32gui.FindWindow(TASKBAR_CLASSNAME, None)


def get_foreground_window() -> int:
    return win32gui.GetForegroundWindow()


def get_last_input_time():
    return win32api.GetLastInputInfo()


def get_ms_since_system_start():
    # TODO: Need to use GetTickCount64 so we're not limited to 49.7 days. Though,
    #  note that apparently hybrid sleep messes this up.  Hrmph...
    return win32api.GetTickCount()


def get_idle_time() -> float:
    """Returns number of seconds system has been idle"""
    return (get_ms_since_system_start() - get_last_input_time()) / 1000.0
