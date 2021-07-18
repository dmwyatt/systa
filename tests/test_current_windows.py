import re

import pytest
import win32con
import win32gui

from systa.backend.access import MIN_ALL_UNDO
from systa.windows import (
    ACTIVE_WINDOW,
    CurrentWindows,
    Window,
    current_windows,
    regex_search,
)


@pytest.fixture
def undo_minimize_all():

    yield
    sys_tray_handle = win32gui.FindWindow("Shell_TrayWnd", None)
    win32gui.SendMessage(sys_tray_handle, win32con.WM_COMMAND, MIN_ALL_UNDO, 0)


@pytest.mark.skip
@pytest.mark.usefixtures("undo_minimize_all")
def test_minimize_all():
    # TODO: Figure out how to actually test that this does anything.  Right now it's
    #  just a dummy test

    current_windows.minimize_all()


def test_current_windows():
    assert all(isinstance(w, Window) for w in current_windows.current_windows)


def test_current_handles():
    assert all(h == w.handle for h, w in current_windows.current_handles.items())


def test_current_titles():
    assert all(
        all(isinstance(w, Window) for w in windows)
        for windows in current_windows.current_titles.values()
    )
    assert all(isinstance(t, str) for t in current_windows.current_titles)


def test_containment_exact_title(notepad: Window):
    assert "Untitled - Notepad" in current_windows


def test_containment_window_instance(notepad: Window):
    assert notepad in current_windows


def test_containment_handle(notepad: Window):
    assert notepad.handle in current_windows


def test_containment_predicate(notepad: Window):
    assert regex_search(".* - Notepad") in current_windows


def test_getitem_exact_title(notepad: Window):
    assert notepad in current_windows[notepad.title]


def test_getitem_wildcard(notepad: Window):
    assert notepad in current_windows["*otep*"]


def test_getitem_window_instance(notepad: Window):
    assert notepad in current_windows[notepad]


def test_getitem_predicate(notepad: Window):
    assert notepad in current_windows[regex_search(".* - Note.ad")]


def test_getitem_compiled_regex(notepad: Window):
    assert notepad in current_windows[re.compile(".* - Note.ad")]


def test_getitem_handle(notepad: Window):
    assert notepad in current_windows[notepad.handle]


def test_getitem_active_window(notepad: Window):
    assert current_windows[ACTIVE_WINDOW] == [notepad]


def test_get_active_window(notepad: Window):
    assert current_windows.get_active_window() == notepad
    assert CurrentWindows.get_active_window() == notepad
