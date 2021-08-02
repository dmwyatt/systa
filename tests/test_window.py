from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import Pattern

import pytest
from pynput.mouse import Controller

from systa.backend.access import close_window, set_hidden
from systa.backend.monitors import SystaMonitor, enumerate_monitors
from systa.types import Point, Rect
from systa.utils import wait_for_it
from systa.windows import (
    Window,
    WindowRelativeMouseController,
    classname_search,
    current_windows,
    regex_search,
)


def test_create_with_title(notepad: Window):
    assert isinstance(Window("Untitled - Notepad"), Window)


def test_create_with_window(notepad: Window):
    assert isinstance(notepad, Window)
    assert isinstance(Window(notepad), Window)


def test_create_with_handle(notepad: Window):
    assert isinstance(Window(notepad.handle), Window)


def test_create_with_regex_search_predicate(notepad: Window):
    assert isinstance(Window(regex_search(".* - N.tepad")), Window)


def test_create_with_classname_search_predicate(notepad: Window):
    assert isinstance(Window(classname_search("N?tepad")), Window)


def test_str(notepad: Window):
    assert str(notepad) == "Untitled - Notepad"


def test_repr_without_title(notepad: Window):
    assert re.match(r"Window\(handle=\d+\)", repr(notepad))


def test_repr_with_title(notepad: Window):
    _ = notepad.title  # force lookup and caching of title
    assert re.match(r'^Window\(handle=\d+, title="Untitled - Notepad"\)', repr(notepad))


def test_mouse_type(notepad: Window):
    assert isinstance(notepad.mouse, WindowRelativeMouseController)


def test_title(notepad: Window):
    assert notepad.title == "Untitled - Notepad"


def test_title_is_cached(notepad: Window):
    assert notepad.title == "Untitled - Notepad"
    notepad.title = "I've changed!"

    # title is still cached
    assert notepad.title == "Untitled - Notepad"


def test_title_is_changeable(notepad: Window):
    notepad.title = "I've changed!"
    assert Window(notepad).title == "I've changed!"


def test_active(notepad: Window):
    assert notepad.active


def test_active_is_changeable(notepad: Window):
    assert notepad.active
    notepad.active = False
    assert wait_for_it(lambda: not notepad.active)
    notepad.active = True
    assert wait_for_it(lambda: notepad.active)


def test_exists(notepad: Window):
    assert notepad.exists
    close_window(notepad.handle)
    assert wait_for_it(lambda: not notepad.exists)


def test_exists_closes(notepad: Window):
    assert notepad.exists
    notepad.exists = False
    assert wait_for_it(lambda: not notepad.exists)


def test_exists_does_not_raise_on_closed_window():
    notepad_process = subprocess.Popen(["notepad.exe"])
    np = Window.wait_for_window("Untitled - Notepad")
    notepad_process.kill()
    assert wait_for_it(lambda: not np.exists)


def test_visible(notepad: Window):
    assert notepad.visible
    set_hidden(notepad.handle)
    assert not notepad.visible


def test_visible_can_hide(notepad: Window):
    assert notepad.visible
    notepad.visible = False
    assert not notepad.visible


def test_visible_does_not_mean_minimized(notepad: Window):
    assert notepad.visible
    notepad.minimized = True
    # give it 3/10 of a second to minimize
    assert not wait_for_it(lambda: not notepad.visible, max_wait=0.3)


def test_enabled(notepad: Window):
    assert notepad.enabled
    notepad.enabled = False
    assert not Window(notepad).enabled


def test_minimized(notepad: Window):
    assert not notepad.minimized
    notepad.minimized = True
    assert notepad.minimized


def test_maximized(notepad: Window):
    assert not notepad.maximized
    notepad.maximized = True
    assert notepad.maximized


def test_position(notepad: Window):
    assert isinstance(notepad.position, Point)


def test_can_set_position_with_tuple(notepad: Window):
    notepad.position = (0, 0)
    assert notepad.position == Point(0, 0)


def test_can_set_position_with_point(notepad: Window):
    notepad.position = Point(0, 0)
    assert notepad.position == Point(0, 0)


def test_can_set_position_with_rect(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.position == Point(0, 0)


def test_position_raises_on_invalid_type(notepad: Window):
    with pytest.raises(
        TypeError, match="Must provide a 2-element collection, a Point, or a Rect."
    ):
        notepad.position = "0,0"


def test_rectangle(notepad: Window):
    assert isinstance(notepad.rectangle, Rect)


def test_rectangle_settable(notepad: Window):
    notepad.rectangle = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.rectangle == Rect(origin=Point(0, 0), end=Point(300, 300))


def test_width(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.width == 300


def test_width_settable(notepad: Window):
    notepad.width = 1000
    assert notepad.width == 1000


def test_height(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.height == 300


def test_height_settable(notepad: Window):
    notepad.height = 500
    assert notepad.height == 500


def test_bring_mouse_to(notepad: Window, mouse: Controller):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    notepad.bring_mouse_to()
    assert Controller().position == (150, 150)


def test_bring_mouse_to_positioned(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    pos = (75, 75)
    notepad.bring_mouse_to(*pos)
    assert Controller().position == pos


def test_bring_to_mouse_center(notepad: Window, mouse: Controller):
    pos = (150, 150)
    mouse.position = pos
    notepad.bring_to_mouse(center=True)
    assert notepad.absolute_center_coords == Point(*pos)


def test_bring_to_mouse(notepad: Window, mouse: Controller):
    notepad.bring_to_mouse()
    assert tuple(notepad.position) == mouse.position


def test_absolute_center_coords(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.absolute_center_coords == Point(150, 150)


def test_absolute_center_coords_settable(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    notepad.absolute_center_coords = (300, 300)
    assert notepad.position == Point(150, 150)


def test_relative_center_coords(notepad: Window):
    notepad.position = Rect(origin=Point(0, 0), end=Point(300, 300))
    assert notepad.relative_center_coords == Point(150, 150)


def test_process_id(notepad: Window):
    assert isinstance(notepad.process_id, int)
    found_pids = []
    for window in current_windows:
        if window.title == notepad.title:
            found_pids.append(window.process_id)
            break
    assert notepad.process_id in found_pids


def test_pid(notepad: Window):
    assert notepad.process_id == notepad.pid


def test_get_process_path(notepad: Window):
    assert notepad.process_path.endswith("notepad.exe")


def test_classname(notepad: Window):
    assert notepad.classname == "Notepad"


def test_screens(notepad: Window):
    # TODO: come up with better test for this that works on different systems with
    #    different number of screens
    assert all(isinstance(s, SystaMonitor) for s in notepad.screens)


def test_send_to_monitor(notepad: Window):
    monitor_numbers = [m.number for m in enumerate_monitors()]

    for monitor_number in monitor_numbers:
        assert notepad.send_to_monitor(monitor_number)


def test_classname_search_predicate():
    class fake_window:
        classname = "Window Title"

    assert classname_search("Window Title")(fake_window)


def test_classname_search_predicate_case_sensitivity():
    class fake_window:
        classname = "Window Title"

    assert classname_search("window title", case_sensitive=False)(fake_window)


@dataclass
class PredicateData:
    search: str | Pattern
    expected: bool
    classname: str = "Window Classname"
    case_sensitive: bool = True


predicate_data = [
    PredicateData(search="Window Classname", expected=True),
    PredicateData(search="Window classname", expected=False),
    PredicateData(search="window classname", expected=True, case_sensitive=False),
    PredicateData(search="Window Classname", expected=True, case_sensitive=False),
    PredicateData(search="W?ndow Class*", expected=True),
    PredicateData(search="w?ndow class*", expected=False),
    PredicateData(search="w?ndow class*", expected=True, case_sensitive=False),
    PredicateData(search="*", expected=True, case_sensitive=False),
    PredicateData(search="*", expected=True),
    PredicateData(search=re.compile(".*"), expected=True),
    PredicateData(
        search=re.compile(r"^W.ndow Classname$"), expected=True, case_sensitive=False
    ),
    PredicateData(search=re.compile(r"^W.ndow Classname$"), expected=True),
    PredicateData(
        search=re.compile(r"^W.ndow classname$"), expected=True, case_sensitive=False
    ),
]


@pytest.mark.parametrize("data", predicate_data)
def test_classname_search(data: PredicateData):
    class fake_window:
        classname = data.classname

    assert (
        classname_search(data.search, case_sensitive=data.case_sensitive)(fake_window)
        == data.expected
    )
