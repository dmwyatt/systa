import abc
from fnmatch import fnmatch, fnmatchcase
from functools import wraps
from inspect import unwrap
from typing import Callable, List, Optional, Tuple

from systa.events.constants import EventType, win_events
from systa.events.store import callback_store
from systa.events.types import EventData, EventFilterCallableType
from systa.types import Rect


class EventTesterBase(abc.ABC):
    """By subclassing this your event tests get registered.

    For most use cases you can just use the :func:`make_filter` decorator instead of
    subclassing this class.
    """

    @abc.abstractmethod
    def event_test(self, event_data):
        ...

    def __call__(self, func):
        unwrapped_func = unwrap(func)

        @wraps(func)
        def wrapper(data):
            if data is None or not self.event_test(data):
                return None
            return func(data)

        # Capture the callable, including all decorators
        callback_store.update_callable(unwrapped_func, wrapper)

        return wrapper


def make_filter(test_func: Callable[[EventData], bool]):
    """Create your own event filter.

    To make your own `filter_by` decorator, write a function that takes one
    :class:`~systa.events.types.EventData` argument and decorate it with this function.

    :param test_func: The function you're decorating.
    """

    @wraps(test_func)
    def decorator(func):
        class _tester(EventTesterBase):
            def event_test(self, event_data) -> bool:
                return test_func(event_data)

        return _tester()(func)

    return decorator


@make_filter
def require_titled_window(data: EventData):
    """Filters out windows that do not have a title."""
    return data.window and data.window.title


@make_filter
def exclude_system_windows(data: EventData):
    """Filters out common, probably uninteresting window titles.

    There's a lot of windows like "OleMainThreadWndName" or "Default IME" that you
    likely you don't care about.  Use this filter to exclude them.
    """
    return data.window and not win_events.is_windows_internal_title(data.window.title)


def require_title(title: str, case_sensitive=True):
    """Filters on window title.

    Accepts wildcards in the style of Unix shell-style wildcards.

    I.e. ``@filter_by.title("*Notepad")`` will match any window title that ends
    in "Notepad".

    +------------+-----------------------------------+
    | Pattern    | Meaning                           |
    +============+===================================+
    | ``*``      | matches everything                |
    +------------+-----------------------------------+
    | ``?``      | matches any single character      |
    +------------+-----------------------------------+
    | ``[seq]``  | matches any character in seq      |
    +------------+-----------------------------------+
    | ``[!seq]`` | matches any character not in seq  |
    +------------+-----------------------------------+

    :param title: The title to match.
    :param case_sensitive: If ``False`` will be case insensitive. Defaults to ``True``
    """

    @make_filter
    def _include_only_titled(data: EventData):
        check = fnmatchcase if case_sensitive else fnmatch
        return data.window and check(data.window.title, title)

    return _include_only_titled


def require_size_is_less_than(x: int, y: int):
    """
    Filter to include only windows with x and y dimensions lower than x, y.

    :param x: Width
    :param y: Height
    """

    @make_filter
    def _size_is_less_than(data: EventData):
        return data.window and (data.window.width < x and data.window.height < y)

    return _size_is_less_than


def any_filter(*filters: EventFilterCallableType):
    """
    Given a list of filters, pass if any of them pass.

    :param filters: Provide all the filters you want to check the event with.
    """

    @make_filter
    def _any_filter(data: EventData):
        return any(unwrap(f)(data) for f in filters)

    return _any_filter


def require_origin_within(rect: Rect):
    """
    Require window's origin (upper left corner) to be within rectangle.
    """

    @make_filter
    def _require_origin_within(data: EventData):
        if not data.window:
            return False
        return rect.contains_point(data.window.position)

    return _require_origin_within


@make_filter
def is_maximized(data: EventData):
    """Filters out windows that are not maximized"""
    return data.window.maximized


def exclude_window_events(window_events: Optional[List[Tuple[str, EventType]]] = None):
    """Given a list of title/event pairs, excludes those events from those windows."""
    if window_events is None:
        window_events = []

    @make_filter
    def _exclude_window_events(data: EventData):
        for window_title, event in window_events:
            if data.window and data.window.title is not None:
                if data.event_info.event == event and fnmatchcase(
                    data.window.title, window_title
                ):
                    return False
        return True

    return _exclude_window_events


@make_filter
def require_window(data: EventData):
    """Exclude events that do not have a window."""
    return bool(data.window)


def touches_monitors(*monitor_numbers: int):
    """Window touches all the provided monitors.

    .. note:: Provide just one monitor number to test if window is on just that monitor.
    .. note:: Combine with :func:`any_filter` to test if a window is fully contained
        on any single monitor:

        .. code-block::

            from systa.events.decorators import filter_by, listen_to

            @filter_by.any_filter(
                [
                    filter_by.touches_monitors(1),
                    filter_by.touches_monitors(2),
                    filter_by.touches_monitors(3),
                ]
            )
            @listen_to.location_change
            def my_func(data: EventData):
                # window moved to a new location that was on just one of 3
                # monitors.
                pass

    :param monitor_numbers: Provide the number of each monitor you want to check.
    """

    @make_filter
    def _touches_monitors(data: EventData):
        if not data.window:
            return False
        screens = data.window.screens

        return set(monitor_numbers) == set(screen.number for screen in screens)

    return _touches_monitors
