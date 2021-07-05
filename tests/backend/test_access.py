import subprocess

from systa.backend.access import (
    activate_window,
    close_window,
    get_class_name,
    get_exists,
    get_handle,
    get_handles,
    get_is_active,
    get_is_enabled,
    get_is_maximized,
    get_is_minimized,
    get_is_visible,
    get_position,
    get_process_id,
    get_process_path,
    get_sys_tray_handle,
    get_title,
    get_titles_and_handles,
    get_win_height,
    get_win_width,
    get_window_titles,
    restore,
    set_disabled,
    set_enabled,
    set_hidden,
    set_maximized,
    set_minimized,
    set_shown,
    set_title,
    set_win_dimensions,
    set_win_position,
)
from systa.utils import wait_for_it
from systa.windows import Window


def test_get_window_titles(notepad):
    data = get_window_titles()
    assert "Untitled - Notepad" in (d[0] for d in data)
    assert all(isinstance(h[1], int) for h in data)


def test_get_handles():
    assert all(isinstance(h, int) for h in get_handles())


def test_access_sys_tray_handle():
    # Have to gather multiple handles since several parts of the taskbar have this
    # classname
    handles = []
    for title, handle in get_window_titles():
        if get_class_name(handle) == "Shell_TrayWnd":
            handles.append(handle)

    assert any(
        h == get_sys_tray_handle() for h in handles
    ), "Could not find sys tray handle."


def test_set_title(notepad):
    title = "this is a custom window title"
    set_title(notepad.handle, title)
    assert notepad.title == title


def test_get_titles_and_handles():
    assert set((h[0], h[1]) for h in get_titles_and_handles()) == set(
        (y[0], y[1]) for y in get_titles_and_handles()
    )


def test_get_is_active(notepad):
    assert get_is_active(notepad.handle)


def test_get_exists(notepad):
    assert get_exists(notepad.handle)
    notepad.exists = False
    assert wait_for_it(lambda: not get_exists(notepad.handle))


def test_get_is_visible(notepad):
    assert get_is_visible(notepad.handle)
    notepad.visible = False
    assert not get_is_visible(notepad.handle)


def test_set_hidden(notepad):
    set_hidden(notepad.handle)
    assert not get_is_visible(notepad.handle)


def test_set_shown(notepad):
    set_hidden(notepad.handle)
    assert not get_is_visible(notepad.handle)
    set_shown(notepad.handle)
    assert get_is_visible(notepad.handle)


def test_get_is_enabled(notepad):
    assert get_is_enabled(notepad.handle)


def test_enablement(notepad):
    assert notepad.enabled
    set_disabled(notepad.handle)
    assert not notepad.enabled
    set_enabled(notepad.handle)
    assert notepad.enabled


def test_get_is_minimized(notepad):
    notepad.minimized = True
    assert get_is_minimized(notepad.handle)


def test_set_minimized(notepad):
    set_minimized(notepad.handle)
    assert get_is_minimized(notepad.handle)


def test_get_is_maximized(notepad):
    notepad.maximized = True
    assert get_is_maximized(notepad.handle)


def test_set_maximized(notepad):
    set_maximized(notepad.handle)
    assert get_is_maximized(notepad.handle)


def test_restore(notepad):
    notepad.minimized = True
    restore(notepad.handle)
    assert not notepad.minimized


def test_activate_window(notepad):
    # deactivate notepad
    activate_window(next(get_handle("Program Manager")))
    assert not notepad.active
    activate_window(notepad.handle)
    assert wait_for_it(lambda: notepad.active)


def test_bring_to_top(notepad):
    # deactivate notepad
    activate_window(next(get_handle("Program Manager")))
    assert not notepad.active
    activate_window(notepad.handle)
    assert notepad.active


def test_close_window(notepad):
    close_window(notepad.handle)
    assert wait_for_it(lambda: not notepad.exists)


def test_get_position(notepad):
    assert all(isinstance(p, int) for p in get_position(notepad.handle))


def test_set_win_position(notepad):
    set_win_position(notepad.handle, 0, 0)
    assert get_position(notepad.handle) == (0, 0)


def test_dimensions_methods(notepad):
    set_win_dimensions(notepad.handle, 500, 500)
    assert get_win_height(notepad.handle) == 500
    assert get_win_width(notepad.handle) == 500


def test_get_process_id():
    notepad_process = subprocess.Popen(["notepad.exe"])
    notepad = Window.wait_for_window("Untitled - Notepad")
    assert get_process_id(notepad.handle) == notepad_process.pid


def test_get_process_path(notepad):
    assert get_process_path(notepad.handle).endswith(r"\notepad.exe")


def test_get_title(notepad):
    assert get_title(notepad.handle) == "Untitled - Notepad"
