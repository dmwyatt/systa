import abc
from fnmatch import fnmatch, fnmatchcase
from functools import partial, wraps
from inspect import unwrap
from typing import Callable, Iterable, Literal, Optional, Tuple, overload

import pywintypes

from systa.events.constants import win_events
from systa.events.store import callback_store
from systa.events.types import EventData, EventFilterCallableType, EventType
from systa.types import Rect


class EventTesterBase(abc.ABC):
    """By subclassing this your event tests get registered.

    For most use cases you can just use the :func:`make_filter` decorator instead of
    subclassing this class.
    """

    # TODO: Probably just replace this class with a Protocol and maybe runtime_checkable
    @abc.abstractmethod
    def event_test(self, event_data):
        ...

    def __call__(self, func) -> Callable[[EventData], Optional[EventData]]:
        """
        Instances can be used as decorators.

        The decorator returns a function that returns ``None`` if the
        :meth:`event_test` method returns False, or  returns the return value of the
        wrapped function.

        :param func:
        :return:
        """
        unwrapped_func = unwrap(func)

        @wraps(func)
        def wrapper(data):
            if data is None or not self.event_test(data):
                return None
            return func(data)

        # Capture the callable, including all decorators
        callback_store.update_callable(unwrapped_func, wrapper)

        return wrapper


FilterFunctionType = Callable[[EventData], bool]
FilterFunctionDecoratorType = Callable[[FilterFunctionType], FilterFunctionType]


def _make_filter(
    test_func: FilterFunctionType,
    require_existing_window: bool,
    exclude_sys_windows: bool,
    capture_invalid_window_handle: bool,
) -> FilterFunctionDecoratorType:
    @wraps(test_func)
    def decorator(func: FilterFunctionType) -> FilterFunctionType:
        class _tester(EventTesterBase):
            def event_test(self, event_data: EventData) -> bool:
                if (
                    require_existing_window
                    and event_data.window
                    and not event_data.window.exists
                ) or (
                    exclude_sys_windows
                    and not apply_filter(exclude_system_windows, event_data)
                ):
                    return False

                try:
                    return test_func(event_data)
                except pywintypes.error as e:
                    if capture_invalid_window_handle and e.winerror == 1400:
                        return False
                    else:
                        raise

        return _tester()(func)

    return decorator


def make_filter(
    test_func=None,
    *,
    exclude_sys_windows=True,
    require_existing_window=True,
    capture_invalid_window_handle_error=True,
) -> FilterFunctionDecoratorType:
    """
    Decorator to make a function into a filter on an event's data.

    Using the default values for the arguments:

    .. code-block:: python

        @make_filter
        def some_func(data: eventData)

    Changing argument values:

    .. code-block:: python

        @make_filter(capture_invalid_window_handle_error=False)
        def some_other_func(data: EventData):
            pass


    :param test_func: The decorated function.
    :param exclude_sys_windows: If ``True``, will use built-in heuristics to filter
        out events for windows used by Windows internally. Defaults to ``True``.
    :param require_existing_window:  If ``True``, will filter out events for windows
        that no longer exist. Note that this *doesn't* guarantee that the window
        doesn't disappear between the time your function starts and you want to do
        something with the window in your function. It *does* guarantees your function
        won't get called if the window disappears between the time the event happens and
        Windows calls our code...which is what seems to be the most likely case.
        Defaults to ``True``.
    :param capture_invalid_window_handle_error:  If a window disappears by the time
        you try to do something with it, we'll automatically handle the error for
        you.  Note that if you need to do some sort of cleanup action in your
        function, you want to set this option to ``False`` and handle the error
        yourself.  Defaults to ``True``..
    """
    if test_func is None:
        return partial(
            make_filter,
            exclude_sys_windows=exclude_sys_windows,
            require_existing_window=require_existing_window,
            capture_invalid_window_handle_error=capture_invalid_window_handle_error,
        )

    return _make_filter(
        test_func,
        require_existing_window,
        exclude_sys_windows,
        capture_invalid_window_handle_error,
    )


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
    return (
        data.window
        and data.window.title
        and not win_events.is_windows_internal_title(data.window.title)
    )


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


@overload
def require_size_is_less_than(
    x: int = None,
    y: int = None,
    area: Literal[None] = None,
):
    # case providing x and y
    ...


@overload
def require_size_is_less_than(
    x: Literal[None] = None,
    y: Literal[None] = None,
    area: int = None,
):
    # case providing area
    ...


def require_size_is_less_than(
    x: int = None,
    y: int = None,
    area: int = None,
):
    """
    Include only windows of x, y dimensions or area less than provided.

    If area is provided, x and y are ignored and are not needed.  You can just do:

    .. code-block:: python

        @filter_by.require_size_is_less_than(area=250000)
        def f(data: EventData):
            ...

    :param area: Total area in pixels.
    :param x: Width
    :param y: Height
    """
    if area is None:
        assert x is not None and y is not None

    @make_filter
    def _size_is_less_than(data: EventData):
        if data.window:
            if area:
                return (data.window.width * data.window.height) < area
            elif x and y:
                return data.window.width < x and data.window.height < y

    return _size_is_less_than


def any_filter(*filters: EventFilterCallableType):
    """
    Given a list of filters, pass if any of them pass.

    :param filters: Provide all the filters you want to check the event with.
    """

    @make_filter
    def _any_filter(data: EventData):
        return any(apply_filter(f, data) for f in filters)

    return _any_filter


def all_filters(*filters: EventFilterCallableType):
    """Given a list of filters, pass if all of them pass

    :param filters: Provide all the filters you want to check the event with.
    """

    @make_filter
    def _all_filters(data: EventData):
        return all(apply_filter(f, data) for f in filters)

    return _all_filters


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


def exclude_window_events(window_events: Iterable[Tuple[str, EventType]]):
    """Given a list of title/event pairs, excludes those events from those windows."""

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
    """Exclude events that do not have a window.

    Most likely you won't need this since the default :func:`make_filter` decorator
    already does this check, but this is provided for cases when not using that
    decorator.
    """
    return bool(data.window)


def touches_monitors(*monitor_numbers: int):
    """Window touches at least all the provided monitors.

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
        return set(monitor_numbers) <= set(screen.number for screen in screens)

    return _touches_monitors


def apply_filter(f: FilterFunctionType, data: EventData):
    """Use a filter as a simple boolean test function.

    If you want to use one of the filters in the
    :mod:`~systa.events.decorators.filter_by` module as a simple boolean test of a
    :class:`~systa.types.EventData` object, you can use this function.

    >>>
    >> apply_filter(require_size_is_less_than, your_data_object)
    True
    """
    return unwrap(f)(data)
