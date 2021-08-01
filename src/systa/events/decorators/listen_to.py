from __future__ import annotations

from functools import wraps
from inspect import unwrap

from systa.events.constants import win_events
from systa.events.events import IdleCheck
from systa.events.store import callback_store, coerce_event_ranges
from systa.events.types import (
    CheckableEvent,
    EventData,
    EventsTypes,
    UserEventCallableType,
)


class specified_events:
    """
    Decorator to register a function to listen to the specified  events.
    """

    def __init__(self, events: EventsTypes) -> None:
        """
        :param events: The event(s) to listen to.
        """
        self.ranges = None
        self.checkable_event = None

        if isinstance(events, CheckableEvent):
            self.checkable_event = events
        else:
            self.ranges = coerce_event_ranges(events)

    def __call__(self, func: UserEventCallableType) -> UserEventCallableType:
        callback_store.add_user_func(unwrap(func), self.checkable_event or self.ranges)

        @wraps(func)
        def wrapper(data: EventData):
            return func(data)

        return wrapper


def idleness(seconds: float, call_count_limit: int = 1):
    """System has been idle for so many seconds.

    :param seconds: Number of seconds to consider system idle.  Maximum resolution of
        :attr:`systa.events.store.Store.msg_loop_timeout`
    :param call_count_limit: How many times to call the function after idle time has
        been reached. The event loop runs every
        :attr:`systa.events.store.Store.msg_loop_timeout` milliseconds. If we didn't
        have this parameter every time the event loop ran and the user was still idle,
        the user's function would be called over and over again.
    """

    def _idleness(func: UserEventCallableType):
        return specified_events(IdleCheck(seconds, call_count_limit))(func)

    return _idleness


def create(func: UserEventCallableType):
    """A window has been created.

    Ok, I lied, it's when all sorts of objects, including windows have been created.

    .. seealso:: :func:`destroy`, :func:`existence_change`
    """
    return specified_events(win_events.EVENT_OBJECT_CREATE)(func)


def destroy(func: UserEventCallableType):
    """A window has been closed.

    Ok, another lie.  It could be other types of objects...not just windows.

    .. seealso:: :func:`create`, :func:`existence_change`
    """
    return specified_events(win_events.EVENT_OBJECT_CREATE)(func)


def existence_change(func: UserEventCallableType):
    """A window has been created or destroyed.

    Ok, I should stop so many lies.  You won't be surprised to hear that we're not
    just talking about windows...

    .. seealso:: :func:`create`, :func:`destroy`
    """
    return specified_events(
        [win_events.EVENT_OBJECT_CREATE, win_events.EVENT_OBJECT_DESTROY]
    )


def restore(func: UserEventCallableType):
    """Window was restored from minimization.

    .. seealso:: :func:`minimize`
    """
    return specified_events(win_events.EVENT_SYSTEM_MINIMIZEEND)(func)


def minimize(func: UserEventCallableType):
    """Window was minimized

    .. seealso:: :func:`restore`
    """
    return specified_events(win_events.EVENT_SYSTEM_MINIMIZESTART)(func)


def maximize(func: UserEventCallableType):
    """There isn't a maximize event! Wrapper of :func:`location_change`.

    Best we can do is listen to :func:`location_change` and then check the window
    state with :any:`Window.maximized`. It's up to the user to check
    the maximized state with :func:`filter_by.is_maximized` or manually with the
    provided :any:`Window` object.
    """
    return location_change(func)


def location_change(func: UserEventCallableType):
    """An object has changed location, shape, or size."""
    return specified_events(win_events.EVENT_OBJECT_LOCATIONCHANGE)(func)


def any_event(func: UserEventCallableType):
    """Any event.

    .. note:: Generally, you'll want to save system resources and use a more
        discerning set of events.
    """
    return specified_events((win_events.EVENT_MIN, win_events.EVENT_MAX))(func)


def capture_mouse(func: UserEventCallableType):
    """A window has captured the mouse.

    Basically, this happens when you click in  a window.

    .. seealso:: :py:func:`lost_mouse_capture`
    """
    return specified_events(win_events.EVENT_SYSTEM_CAPTURESTART)(func)


def lost_mouse_capture(func: UserEventCallableType):
    """A window has lost the mouse capture.

    This is the window that lost mouse capture when you click somewhere else.

    .. seealso:: :py:func:`capture_mouse`
    """
    return specified_events(win_events.EVENT_SYSTEM_CAPTUREEND)(func)


def move_or_sizing_ended(func: UserEventCallableType):
    """A window has been resized.

    .. seealso:: :func:`move_or_sizing_started`
    """
    return specified_events(win_events.EVENT_SYSTEM_MOVESIZEEND)(func)


def move_or_sizing_started(func: UserEventCallableType):
    """A window is getting resized.

    .. seealso:: :func:`move_or_sizing_ended`
    """
    return specified_events(win_events.EVENT_SYSTEM_MOVESIZESTART)(func)
