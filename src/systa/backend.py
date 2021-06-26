import ctypes
from typing import Iterator, List, Tuple

import win32api
import win32con
import win32gui
import win32process
from pynput.keyboard import Controller, Key

from systa.exceptions import NoMatchingWindowError

# user32 = ctypes.WinDLL("user32", use_last_error=True)
user32 = ctypes.windll.user32

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


def get_class_name(handle: int) -> str:
    buffer = ctypes.create_unicode_buffer(100)
    user32.GetClassNameW(handle, buffer, 99)
    return buffer.value


def set_enabled(handle: int) -> None:
    return user32.EnableWindow(handle, 1)


def set_disabled(handle: int) -> None:
    return user32.EnableWindow(handle, 0)


class WinAccess:
    @property
    def sys_tray_handle(self) -> int:
        return win32gui.FindWindow("Shell_TrayWnd", None)

    @staticmethod
    def set_title(handle: int, title: str) -> None:
        win32gui.SetWindowText(handle, title)

    @staticmethod
    def get_handle(title: str) -> Iterator[int]:
        found = False
        for title_, handle in get_window_titles():
            if title_ == title:
                found = True
                yield handle

        if not found:
            raise NoMatchingWindowError(f"No window matching title: '{title}'")

    @staticmethod
    def get_titles_and_handles() -> Iterator[Tuple[str, int]]:
        return get_window_titles()

    @staticmethod
    def get_is_active(handle: int) -> bool:
        return win32gui.GetForegroundWindow() == handle

    @staticmethod
    def get_exists(handle: int) -> bool:
        return bool(win32gui.IsWindow(handle))

    @staticmethod
    def get_is_visible(handle: int) -> bool:
        return bool(win32gui.IsWindowVisible(handle))

    @staticmethod
    def set_hidden(handle: int) -> None:
        win32gui.ShowWindow(handle, win32con.SW_HIDE)

    @staticmethod
    def set_shown(handle: int) -> None:
        win32gui.ShowWindow(handle, win32con.SW_SHOW)

    @staticmethod
    def get_is_enabled(handle: int) -> bool:
        return bool(win32gui.IsWindowEnabled(handle))

    @staticmethod
    def get_is_minimized(handle: int) -> bool:
        return bool(win32gui.IsIconic(handle))

    @staticmethod
    def set_minimized(handle: int) -> None:
        return win32gui.ShowWindow(handle, win32con.SW_MINIMIZE)

    @staticmethod
    def get_is_maximized(handle: int) -> bool:
        return win32gui.GetWindowPlacement(handle)[1] == win32con.SW_SHOWMAXIMIZED

    @staticmethod
    def set_maximized(handle: int) -> None:
        win32gui.ShowWindow(handle, win32con.SW_MAXIMIZE)

    @staticmethod
    def restore(handle: int) -> None:
        win32gui.ShowWindow(handle, win32con.SW_RESTORE)

    def activate_window(self, handle: int, force_focus_attempt: bool = True) -> None:
        """Activate/focus a window.  Doesn't always work!"""
        self.bring_to_top(handle)

        if force_focus_attempt:
            force_focus(handle)

    @staticmethod
    def bring_to_top(handle: int):
        win32gui.ShowWindow(handle, win32con.SW_RESTORE)
        Controller().press(Key.alt)
        win32gui.SetForegroundWindow(handle)
        Controller().release(Key.alt)
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

    @staticmethod
    def close_window(handle: int) -> None:
        win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)

    @staticmethod
    def _get_window_rect(handle: int) -> Tuple[int, int, int, int]:
        return win32gui.GetWindowRect(handle)

    def get_position(self, handle: int) -> Tuple[int, int]:
        x, y, _, _ = self._get_window_rect(handle)
        return x, y

    @staticmethod
    def set_win_position(handle: int, x: int, y: int) -> None:
        win32gui.SetWindowPos(
            handle,
            win32con.HWND_NOTOPMOST,  # ignored
            x,
            y,
            4000,  # ignored
            4000,  # ignored
            win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE,
        )

    def get_win_width(self, handle: int) -> int:
        left_x, _, right_x, _ = self._get_window_rect(handle)
        return right_x - left_x

    def get_win_height(self, handle: int) -> int:
        _, top_y, _, bottom_y = self._get_window_rect(handle)
        return bottom_y - top_y

    @staticmethod
    def set_win_dimensions(handle: int, width: int, height: int) -> None:
        win32gui.SetWindowPos(
            handle,
            win32con.HWND_NOTOPMOST,
            0,
            0,
            width,
            height,
            win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE | win32con.SWP_NOMOVE,
        )

    @staticmethod
    def get_process_id(handle: int) -> int:
        return win32process.GetWindowThreadProcessId(handle)[1]

    def get_process_path(self, handle: int) -> str:
        handle = win32api.OpenProcess(
            win32con.PROCESS_ALL_ACCESS, False, self.get_process_id(handle)
        )
        return win32process.GetModuleFileNameEx(handle, 0)

    def set_all_windows_minimized(self) -> None:
        win32gui.SendMessage(self.sys_tray_handle, win32con.WM_COMMAND, MIN_ALL, 0)

    def undo_set_all_windows_minimized(self) -> None:
        win32gui.SendMessage(self.sys_tray_handle, win32con.WM_COMMAND, MIN_ALL_UNDO, 0)

    @staticmethod
    def get_title(handle: int) -> str:
        length = user32.GetWindowTextLengthW(handle)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(handle, buffer, length + 1)
        return buffer.value

    @staticmethod
    def get_class_name(handle: int) -> str:
        print("doingit", handle)
        buffer = ctypes.create_unicode_buffer(100)
        user32.GetClassNameW(handle, buffer, 99)
        return buffer.value

    @staticmethod
    def set_enabled(handle: int) -> None:
        user32.EnableWindow(handle, 1)

    @staticmethod
    def set_disabled(handle: int) -> None:
        user32.EnableWindow(handle, 0)

    @staticmethod
    def flash_window(handle: int, flags: int, count: int, timeout: int):
        win32gui.FlashWindowEx(handle, flags, count, timeout)


# wnd is a HWND
# noinspection PyPep8Naming,SpellCheckingInspection
def force_focus(wnd):
    # https://gist.github.com/EBNull/1419093
    SPI_GETFOREGROUNDLOCKTIMEOUT = 0x2000
    SPI_SETFOREGROUNDLOCKTIMEOUT = 0x2001

    SW_RESTORE = 9
    SPIF_SENDCHANGE = 2

    IsIconic = ctypes.windll.user32.IsIconic
    ShowWindow = ctypes.windll.user32.ShowWindow
    GetForegroundWindow = ctypes.windll.user32.GetForegroundWindow
    GetWindowThreadProcessId = ctypes.windll.user32.GetWindowThreadProcessId
    BringWindowToTop = ctypes.windll.user32.BringWindowToTop
    AttachThreadInput = ctypes.windll.user32.AttachThreadInput
    SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow
    SystemParametersInfo = ctypes.windll.user32.SystemParametersInfoW

    if IsIconic(wnd):
        ShowWindow(wnd, SW_RESTORE)

    if GetForegroundWindow() == wnd:
        return True

    ForegroundThreadID = GetWindowThreadProcessId(GetForegroundWindow(), None)
    ThisThreadID = GetWindowThreadProcessId(wnd, None)
    if AttachThreadInput(ThisThreadID, ForegroundThreadID, True):
        BringWindowToTop(wnd)
        SetForegroundWindow(wnd)
        AttachThreadInput(ThisThreadID, ForegroundThreadID, False)
        if GetForegroundWindow() == wnd:
            return True

    timeout = ctypes.c_int()
    zero = ctypes.c_int(0)
    SystemParametersInfo(SPI_GETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(timeout), 0)
    SystemParametersInfo(
        SPI_SETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(zero), SPIF_SENDCHANGE
    )
    BringWindowToTop(wnd)
    SetForegroundWindow(wnd)
    SystemParametersInfo(
        SPI_SETFOREGROUNDLOCKTIMEOUT, 0, ctypes.byref(timeout), SPIF_SENDCHANGE
    )
    if GetForegroundWindow() == wnd:
        return True

    return False
