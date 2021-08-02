from __future__ import annotations

import abc
import re
from collections import defaultdict
from enum import Enum
from fnmatch import fnmatch, fnmatchcase
from functools import cached_property
from typing import Dict, Final, Iterator, List, Optional, Pattern, Tuple, Union

import pywintypes
import win32con
from boltons.iterutils import is_collection
from pynput.mouse._win32 import Button, Controller

from systa.backend import access
from systa.backend.monitors import SystaMonitor, enumerate_monitors, get_monitor
from systa.exceptions import NoMatchingWindowError
from systa.types import Point, Rect
from systa.utils import wait_for_it


class Window:
    """The main class for getting info from and manipulating windows.

    Each window can be represented by this class.  Note that, just because you have
    an instance of this class does not mean the window still exists!  You can use the
    `exists` property to determine if the window is still around.

    :param ref:  The handle to the window.  This is the one source of truth
            linking this object to a real window.

    :param title: If you know the current title at time of creating this object,
        pass it in so we don't do time-consuming queries to get the window title
        later.

        .. note:: Generally you can ignore this parameter.  It's mostly useful when
            doing batch operations with dozens of windows.
    """

    def __init__(
        self,
        ref: "WindowLookupType",
        title: Optional[str] = None,
    ) -> None:
        if isinstance(ref, int):
            self.handle = ref
        else:
            matching_windows = current_windows[ref]

            if not matching_windows:
                raise ValueError("Cannot find matching window.")
            elif len(matching_windows) == 1:
                self.handle = matching_windows[0].handle
            else:
                raise ValueError("Too many matching windows.")
        self._title = title

        self.backend = access

    def __str__(self):
        return self.title

    def __repr__(self):
        if self._title is not None:
            return f'Window(handle={self.handle}, title="{self._title}")'
        else:
            # If we don't have a title, lets not do an expensive lookup to get it
            # just for the repr
            return f"Window(handle={self.handle})"

    def __eq__(self, other: Window):
        """Window equality is determined by the window's handle."""
        return isinstance(other, Window) and other.handle == self.handle

    @staticmethod
    def wait_for_window(lookup: "WindowLookupType", max_wait: float = 5):
        """Waits for a lookup to return a window.


        :param lookup:  The lookup to use to find a window.
        :param max_wait: Wait for up to this many seconds.
        :return: The Window for the lookup.
        :raises ValueError: If the window is not found within ``max_wait`` seconds.
        """
        if not wait_for_it(lambda: lookup in current_windows, max_wait):
            raise ValueError(f"Cannot find window with lookup: {lookup}")
        return Window(lookup)

    @cached_property
    def mouse(self) -> "WindowRelativeMouseController":
        """Returns a modified :class:`WindowRelativeMouseController` that operates
        relative to the windows coordinates."""
        return WindowRelativeMouseController(self)

    @property
    def title(self) -> Optional[str]:
        """The title of the window.

        Note that, unlike most other window attributes, we  cache the title to save
        time-consuming requests for the title.

        Just re-instantiate if you want to see if title has changed.

        Check for window title change:

        >>> from systa.windows import current_windows, Window
        >>> old_instance = Window(123456)
        >>> new_instance = Window(old_instance.handle)

        Or we can do it this way:

        >>> new_instance = current_windows[old_instance]

        We do this because during bulk operations like getting all windows, we often
        also already have the title.  When we're doing operations on large
        collections of this class it's very time consuming to constantly be
        re-retrieving the title, and since the title does not often change, and it is
        commonly used, it seems best to just cache it.
        """
        if self._title is None:
            self._title = self.backend.get_title(self.handle)
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self.backend.set_title(self.handle, value)

    @property
    def active(self) -> bool:
        """Reports and controls if the window is active.

        If ``True``, the window is active and if ``False``, the window is
        not active.

        Setting to ``False`` deactivates the window by activating the desktop
        "window".  Of course, setting to ``True`` activates the window.
        """
        return self.backend.get_is_active(self.handle)

    @active.setter
    def active(self, value: bool) -> None:
        if value:
            self.backend.activate_window(self.handle)
            if not wait_for_it(lambda: self.active, max_wait=1):
                self.bring_mouse_to()
                self.mouse.click(Button.left)
        else:
            # The One Weird Trick to "unfocus" a window is to focus the window called
            # "Program Manager"
            desktop_handle = list(self.backend.get_handle("Program Manager"))
            if len(desktop_handle) != 1:
                raise NoMatchingWindowError(
                    'Cannot activate desktop to "deactivate" window.'
                )

            self.backend.activate_window(desktop_handle[0])

    @property
    def exists(self) -> bool:
        """Reports and controls if the window exists.

        There is no real-time, live  correspondence between a :class:`Window` object
        and a real Microsoft Windows window.  If you want to check if the window
        still exists, this will tell you.

        Because we're crazy you can also set this to ``False`` to close
        a window.

        Setting to ``True`` has no effect.
        """
        return self.backend.get_exists(self.handle)

    @exists.setter
    def exists(self, value: bool) -> None:
        try:
            if not value:
                self.backend.close_window(self.handle)
        except pywintypes.error as e:
            # ignore error about window not existing if we were attempting to close
            # it anyway.
            if e.winerror == 1400 and not value:
                pass
            else:
                raise

    @property
    def visible(self) -> bool:
        """Reports and controls if the window is visible.

        If set to ``True`` sets the window to be visible. If set to
        ``False`` sets the window to be hidden.

        .. warning:: This concept of visibility does not have to do with the window
            being covered by other windows. See here_ for more info.

        .. _here: https://docs.microsoft.com/en-us/windows/desktop/winmsg/window-features#window-visibility

        """
        return self.backend.get_is_visible(self.handle)

    @visible.setter
    def visible(self, value: bool) -> None:
        if value:
            self.backend.set_shown(self.handle)
        else:
            self.backend.set_hidden(self.handle)

    @property
    def enabled(self) -> bool:
        """Reports and controls if the window is enabled.

        If set to ``True``, the window can accept user input. If set to
        ``False`` the window will not accept user input.
        """
        return self.backend.get_is_enabled(self.handle)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if value:
            self.backend.set_enabled(self.handle)
        else:
            self.backend.set_disabled(self.handle)

    @property
    def minimized(self) -> bool:
        """Reports and controls if the window is minimized.

        IF set to ``True``, the window is minimized. If set to ``False``,
        the window is restored.
        """
        return self.backend.get_is_minimized(self.handle)

    @minimized.setter
    def minimized(self, value: bool) -> None:
        if value:
            self.backend.set_minimized(self.handle)
        else:
            self.backend.restore(self.handle)

    @property
    def maximized(self) -> bool:
        """Reports and controls if the window is maximized.

        If set to ``True``, the window is maximized. If set to ``False``,
        the window is restored.
        """
        return self.backend.get_is_maximized(self.handle)

    @maximized.setter
    def maximized(self, value: bool) -> None:
        if value:
            self.backend.set_maximized(self.handle)
        else:
            self.backend.restore(self.handle)

    @property
    def position(self) -> Point:
        """Reports and controls the windows origin coordinate X, Y position.

        If set to a tuple containing two ints or a :class:`Point`, the window is
        instantaneously moved to those coordinates.

        If set to a :class:`Rect`, the window is moved and sized accordingly.
        """
        pos = self.backend.get_position(self.handle)
        return Point(*pos)

    @position.setter
    def position(self, pos: Union[Tuple[int, int], Point, Rect]) -> None:
        if is_collection(pos) and not isinstance(pos, Rect):
            # Point is a collection because it has __iter__
            self.backend.set_win_position(self.handle, *pos)
        elif isinstance(pos, Rect):
            self.backend.set_win_position(self.handle, *pos.origin)
            self.width = pos.width
            self.height = pos.height
        else:
            raise TypeError("Must provide a 2-element collection, a Point, or a Rect.")

    @property
    def rectangle(self) -> Rect:
        position = self.position
        return Rect(
            origin=Point(*position),
            end=Point(x=position.x + self.width, y=position.y + self.height),
        )

    # nr end: 2694, 1181

    @rectangle.setter
    def rectangle(self, rect: Rect):
        self.position = rect

    @property
    def width(self) -> int:
        """Reports and controls the windows width in pixels."""
        return self.backend.get_win_width(self.handle)

    @width.setter
    def width(self, width: int) -> None:
        self.backend.set_win_dimensions(self.handle, width, self.height)

    @property
    def height(self) -> int:
        """Reports and controls the window's height in pixels."""
        return self.backend.get_win_height(self.handle)

    @height.setter
    def height(self, height: int) -> None:
        self.backend.set_win_dimensions(self.handle, self.width, height)

    def bring_mouse_to(self, win_x: int = None, win_y: int = None):
        """
        Moves mouse into window area.  Does not activate window.

        :param win_x: Specify the X position for the mouse.  If not provided, centers
            the mouse on the X-axis of the window.

        :param win_y: Specify the Y position for the mouse.  If not provided, centers
            the mouse on the Y-axis of the window.
        """
        center_x, center_y = self.relative_center_coords
        if win_x is None:
            win_x = center_x

        if win_y is None:
            win_y = center_y

        self.mouse.position = (win_x, win_y)

    def bring_to_mouse(self, center: bool = False) -> None:
        """
        Bring window to mouse's position.

        :param center: If ``True``, then move so that center of window is at
            mouse's position, otherwise it's the top left corner.  Defaults to
            ``False``.
        """
        if center:
            self.absolute_center_coords = Controller().position
            return
        else:
            new_position = Controller().position
            self.position = new_position

    @property
    def absolute_center_coords(self) -> Point:
        """
        The absolute coordinates of the center of the window.

        Set to a ``(x, y)`` tuple  or a :class:`~systa.types.Point` to center window
        at the provided coords.
        """
        x, y = self.position
        return Point(int(self.width / 2) + x, int(self.height / 2) + y)

    @absolute_center_coords.setter
    def absolute_center_coords(self, coords: Union[Tuple[int, int], Point]):
        if not isinstance(coords, Point):
            coords = Point(*coords)

        center_coords = self.relative_center_coords
        self.position = coords.x - center_coords.x, coords.y - center_coords.y

    @property
    def relative_center_coords(self) -> Point:
        """The coordinates of the window's center.

        This is relative to the window's origin point.
        """
        return Point(int(self.width / 2), int(self.height / 2))

    @cached_property
    def process_id(self) -> int:
        """Return the PID of the window's process."""
        return self.backend.get_process_id(self.handle)

    @property
    def pid(self) -> int:
        """Alias for :attr:`process_id`."""
        return self.process_id

    @cached_property
    def process_path(self) -> str:
        """Full path to the process that this window belongs to."""
        return self.backend.get_process_path(self.handle)

    @property
    def classname(self) -> str:
        """Classname of the window.

        See Microsoft's `docs <https://docs.microsoft.com/en-us/windows/win32/winmsg/about-window-classes>`_
        for more info about window class names.
        """
        return self.backend.get_class_name(self.handle)

    def flash(
        self,
        times: int = 4,
        interval: int = 750,
        flags: int = win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG,
    ):
        """Flashes a window to get your attention.

        :param times: The number of times to flash. Defaults to 4.
        :param interval: The flash rate in milliseconds. Defaults to 750ms
        :param flags: One or more of the ``win32con.FLASHW_*`` flags.  Combine with
            the ``|`` operator. Defaults to ``win32con.FLASHW_ALL | win32con.FLASHW_TIMERNOFG``.

            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | Constant              | Meaning                                                                                                                  |
            +=======================+==========================================================================================================================+
            | ``FLASHW_ALL``        | Flash both the window caption and taskbar button. This is equivalent to setting the FLASHW_CAPTION | FLASHW_TRAY flags.  |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | ``FLASHW_CAPTION``    | Flash the window caption.                                                                                                |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | ``FLASHW_STOP``       | Stop flashing. The system restores the window to its original state.                                                     |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | ``FLASHW_TIMER``      | Flash continuously, until the FLASHW_STOP flag is set.                                                                   |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | ``FLASHW_TIMERNOFG``  | Flash continuously until the window comes to the foreground.                                                             |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
            | ``FLASHW_TRAY``       | Flash the taskbar button.                                                                                                |
            +-----------------------+--------------------------------------------------------------------------------------------------------------------------+


        """
        self.backend.flash_window(self.handle, flags, times, interval)

    @property
    def screens(self) -> List[SystaMonitor]:
        windows_monitors = []

        for monitor in enumerate_monitors():
            if self.rectangle.intersects_rect(monitor.rectangle):
                windows_monitors.append(monitor)

        return windows_monitors

    def get_monitor(self, number: int) -> Optional[SystaMonitor]:
        """Get the specified monitor.

        This method only gets monitors that this window is on.

        To get any monitor regardless if you have an instance of a window on it,
        see :func:`systa.monitors.get_monitor`.

        :returns: ``None`` if the monitor does not exist or the window is not on it.
        """
        for screen in self.screens:
            if screen.number == number:
                return screen

    def send_to_monitor(self, number: int) -> bool:
        """Moves window to the specified monitor.

        Window is sized to fill whole monitor.

        :returns: ``True`` if move successful, ``False`` if not.
        """
        monitor = get_monitor(number)
        if monitor is None:
            return False
        self.position = monitor.work_area.origin.x, monitor.work_area.origin.y
        return bool(self.get_monitor(number))


class WindowSearchPredicate(abc.ABC):
    """Inherit from this class to make custom window searching logic.

    At the minimum, you just inherit and override the predicate method with your
    custom logic.


    """

    @abc.abstractmethod
    def predicate(self, window: Window) -> bool:
        """Do logic on the window object to determine if we want to match it.

        :param window: The :class:`Window` we're checking.
        :returns: ``True`` if the window matches, ``False`` if does not.
        """
        ...

    def __call__(self, window: Window) -> bool:
        return self.predicate(window)


class classname_search(WindowSearchPredicate):
    """Search windows with a classname."""

    def __init__(self, search: str | Pattern, case_sensitive: bool = True) -> None:
        """

        :param search: The classname to look for.  Can be one of:

            * str: Interpreted as an :func:`~fnmatch.fnmatch` style wildcard lookup.
            * re.pattern: A regex match against window classname.

        :param case_sensitive: Whether the match has to be case sensitive or not.
            Defaults to ``True``.
        """
        if isinstance(search, str):
            matcher = fnmatchcase if case_sensitive else fnmatch
            self.matcher = lambda x: matcher(x, search)
        else:
            compiled_re = search

            if not case_sensitive and not compiled_re.flags & re.IGNORECASE:
                # user wants case insensitive matching but didn't provide
                # re.IGNORECASE on their regex.  Let's fix that for them.
                compiled_re = re.compile(
                    compiled_re.pattern, compiled_re.flags | re.IGNORECASE
                )
            self.matcher = lambda x: bool(compiled_re.match(x))

    def predicate(self, window: Window) -> bool:
        return self.matcher(window.classname)


class regex_search(WindowSearchPredicate):
    """Search windows with a regex. Provide a string or a compiled regex."""

    def __init__(self, pattern: Union[Pattern, str]) -> None:
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        elif isinstance(pattern, Pattern):
            self.pattern = pattern
        else:
            raise TypeError("Expected a compiled regex or a string.")

    def predicate(self, window: Window) -> bool:
        if window.title is None:
            return False
        return bool(self.pattern.match(window.title))


class WindowActiveness(Enum):
    active = 0


ACTIVE_WINDOW: Final = WindowActiveness.active

WindowLookupType = Union[Window, str, int, WindowSearchPredicate, WindowActiveness]
"""The types you can use to lookup windows.

+------------------------------------------------+--------------------------------------------------+
| Type                                           | Match method                                     |
+================================================+==================================================+
| :class:`Window`                                | Compares handle to current windows handles       |
+------------------------------------------------+--------------------------------------------------+
| ``str``                                        | Wildcard-accepting title match.                  |
+------------------------------------------------+--------------------------------------------------+
| ``int``                                        | Window with handle exists.                       |
+------------------------------------------------+--------------------------------------------------+
| :class:`~systa.windows.WindowSearchPredicate`  | Matches windows with the logic of the predicate. |
+------------------------------------------------+--------------------------------------------------+
| :data:`systa.windows.ACTIVE_WINDOW`            | Matches the active window.                       |
+------------------------------------------------+--------------------------------------------------+
"""


class CurrentWindows:
    """Represent all windows on a system as a dict-like object.

    Behaves similar to  :class:`collections.defaultdict` with a :any:`list` default
    factory. This means that if there are no matching windows, you'll get an empty
    list. Otherwise you'll get a list of at least one :class:`Window` instance.
    """

    @classmethod
    def minimize_all(cls):
        """Minimizes all windows."""
        access.set_all_windows_minimized()

    @classmethod
    def undo_minimize_all(cls):
        access.undo_set_all_windows_minimized()

    @property
    def current_windows(self) -> Iterator[Window]:
        """Iterates over all current windows."""
        for title, handle in access.get_titles_and_handles():
            yield Window(handle, title=title)

    @property
    def current_handles(self) -> Dict[int, Window]:
        """A dictionary mapping window handles to their corresponding Window"""
        return {x.handle: x for x in self.current_windows}

    @property
    def current_titles(self) -> Dict[str, List[Window]]:
        """
        A dictionary mapping title to lists of windows having that title.
        """
        by_title = defaultdict(list)
        for window in self.current_windows:
            by_title[window.title].append(window)
        return by_title

    @classmethod
    def get_active_window(cls) -> Window:
        return Window(ACTIVE_WINDOW)

    def __contains__(self, item: WindowLookupType) -> bool:
        """Membership checks with :const:`WindowLookupType`.

        Using exact title:

        >>> from systa.windows import current_windows
        >>> "Untitled - Notepad" in current_windows
        True

        Using :class:`Window` instance:

        >>> from systa.windows import Window
        >>> np = Window("Untitled - Notepad")
        >>> np in current_windows
        True

        Using handle:

        >>> np.handle in current_windows
        True

        Using search predicate:

        >>> from systa.windows import regex_search
        >>> regex_search(".* - Notepad") in current_windows
        True

        :param: The window lookup you want to use.
        """
        return bool(self[item])

    def __getitem__(self, item: WindowLookupType) -> List[Window]:
        """Get a :class:`Window`.

        See :meth:`~CurrentWindows.__contains__` for the types of values you can
        use to look up windows.

        >>> from systa.windows import current_windows
        >>> current_windows['Untitled - Notepad']
        [Window(handle=..., title="Untitled - Notepad")]

        >>> from systa.windows import regex_search
        >>> current_windows[regex_search(".* - Notepad")]
        [Window(handle=..., title="Untitled - Notepad")]

        :param: The window lookup you want to use.
        """
        if item is ACTIVE_WINDOW:
            return [Window(access.get_foreground_window())]

        if isinstance(item, str):
            # a string is treated as an fnmatch pattern
            return [
                window
                for window in self.current_windows
                if fnmatchcase(window.title, item)
            ]

        elif isinstance(item, WindowSearchPredicate):
            return [window for window in self.current_windows if item(window)]

        elif isinstance(item, Pattern):
            return [
                window for window in self.current_windows if item.match(window.title)
            ]

        elif isinstance(item, Window):
            if item.exists:
                return [item]
            else:
                return []

        elif isinstance(item, int):
            # an int is treated as a window handle
            if not access.get_exists(item):
                return []

            return [Window(item)]

    def __iter__(self):
        return iter(self.current_windows)


current_windows = CurrentWindows()
"""A representation of all windows on the system.  

An instance of :class:`CurrentWindows`. 

.. warning:: Prefer this over your own instantiation of ``CurrentWindows``."""


class WindowRelativeMouseController(Controller):
    """A version of :class:`pynput.mouse.Controller` operating  relative to window.

    See the `pynput docs <https://pynput.readthedocs.io/en/latest/mouse.html>`_ for
    more information. The only difference is that moves and positioning are relative
    to the :class:`Window` provided.
    """

    def __init__(self, window: Window):
        """
        :param window: The :class:`Window` we're operating relative to.
        """
        self.window = window
        super().__init__()

    def _position_get(self):
        x, y = super()._position_get()
        win_x, win_y = self.window.position
        return x - win_x, y - win_y

    def _position_set(self, pos):
        x, y = pos
        win_x, win_y = self.window.position
        super()._position_set((win_x + x, win_y + y))
