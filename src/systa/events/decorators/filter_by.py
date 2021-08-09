import abc
from fnmatch import fnmatch, fnmatchcase
from functools import partial, wraps
from inspect import unwrap
from typing import Callable, Iterable, Literal, Optional, Tuple, overload

import pywintypes

from systa.backend.access import get_idle_time
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
                    (require_existing_window and not event_data.window)
                    or (require_existing_window and not event_data.window.exists)
                    or (
                        exclude_sys_windows
                        and not apply_filter(exclude_system_windows, event_data)
                    )
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
        yourself.  Defaults to ``True``.
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
    return bool(data.window.title)


@make_filter
def exclude_system_windows(data: EventData):
    """Filters out common, probably uninteresting window titles.

    There's a lot of windows like "OleMainThreadWndName" or "Default IME" that you
    likely you don't care about.  Use this filter to exclude them.
    """
    if not data.window:
        return True
    return data.window.title and not win_events.is_windows_internal_title(
        data.window.title
    )


def require_title(title: str, case_sensitive=True):
    """Filters on window title.

    Accepts wildcards in the style of Unix shell-style wildcards (via :func:`~fnmatch.fnmatch`).

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
        return check(data.window.title, title)

    return _include_only_titled


@overload
def require_size_is_less_than(
    width: int = None,
    height: int = None,
    area: Literal[None] = None,
):
    # case providing width and height
    ...


@overload
def require_size_is_less_than(
    width: Literal[None] = None,
    height: Literal[None] = None,
    area: int = None,
):
    # case providing area
    ...


def require_size_is_less_than(
    width: int = None,
    height: int = None,
    area: int = None,
):
    """
    Include only windows of width, height dimensions or area less than provided.

    If area is provided, width and height are ignored and are not needed.  You can
    just do:

    .. code-block:: python

        @filter_by.require_size_is_less_than(area=250000)
        def f(data: EventData):
            ...

    :param area: Total area in pixels.
    :param width: Width
    :param height: Height
    """
    if area is None:
        assert (
            width is not None and height is not None
        ), "If not providing an area, you must provide width and height in pixels."

    @make_filter
    def _size_is_less_than(data: EventData):
        if area:
            return (data.window.width * data.window.height) < area
        elif width and height:
            return data.window.width < width and data.window.height < height

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
            if data.window.title is not None:
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


def touches_monitors(*monitor_numbers: int, exclusive: bool = False):
    """Window touches at least all the provided monitors.


    :param exclusive: If ``True`` require window to be *only* on those monitors,
        otherwise window can be on other monitors in addition to ``monitor_numbers``.
    :param monitor_numbers: Provide the number of each monitor you want to check.
    """

    @make_filter
    def _touches_monitors(data: EventData):
        screens = data.window.screens

        if exclusive:
            return set(monitor_numbers) == set(screen.number for screen in screens)

        return set(monitor_numbers) <= set(screen.number for screen in screens)

    return _touches_monitors


def idle_time_gte(seconds: float):
    """System has been idle for at least X seconds.

    :param seconds: Minimum number of seconds we require system to be idle for.
    """

    @make_filter
    def _idle_for(data: EventData):
        return get_idle_time() >= seconds

    return _idle_for


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


def sanity(return_val: bool, output: Optional[str] = None):
    """A filter for testing stuff!

    :param return_val: This value will be returned when the filter is evaluated.
    :param output: If provided, this value will be printed each time the filter is
        evaluated.
    """

    @make_filter(require_existing_window=False)
    def _sanity(data: EventData):
        if output:
            print(output)
        return return_val

    return _sanity
