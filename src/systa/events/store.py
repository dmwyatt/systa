from __future__ import annotations

import ctypes
import ctypes.wintypes
import inspect
import logging
import time
from _ctypes import CFuncPtr
from collections import defaultdict
from itertools import chain
from typing import Dict, List, Optional, Union

import pythoncom
import win32event
from typeguard import typechecked
from win32con import WINEVENT_OUTOFCONTEXT, WINEVENT_SKIPOWNPROCESS

from systa.events.types import (
    CallbackReturn,
    EventData,
    EventFilterCallableType,
    EventRangeType,
    EventRangesType,
    HookType,
    UserEventCallableType,
    WinEventHookCallbackType,
)
from .constants import EventType, win_events
from ..utils import is_collection_of_collection_of_ints, is_collection_of_ints
from ..windows import Window

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

STOP_EVENT = win32event.CreateEvent(None, 0, 0, None)
OTHER_EVENT = win32event.CreateEvent(None, 0, 0, None)

WIN_EVENT_PROC_TYPE = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)
"""The ctypes windows function that we send to `user32.SetWinEventHook`."""

logger = logging.getLogger(__name__)


class Store:
    msg_loop_timeout = 75

    def __init__(self):
        self._init_store()

    AddUserFuncResultsType = Dict[EventRangeType, bool]

    @typechecked
    def add_user_func(
        self,
        cb: UserEventCallableType,
        events: Union[EventRangesType, EventRangeType, EventType],
    ) -> AddUserFuncResultsType:
        """
        Add a function to the callback store for hooking to WinEvent's.

        :param cb: A user function that takes one argument of type
            :py:class:`systa.events.types.EventData`
        :param events: A single event, a tuple of start/end events, or a sequence of
            tuples indicating multiple ranges.
        :return: A dict indicating which event ranges were or were not added.
        """
        events = coerce_event_types(events)
        assert all(r[0] <= r[1] for r in events), f"{events} are invalid"
        logger.debug("Attempting to register %s to %s.", cb, events)
        results = {}
        for event_range in events:
            if self.is_registered_for(cb, event_range):
                # Prevent duplicate registrations.
                logger.debug(
                    "Prevented attempt to duplicate callback registration of '%s'.",
                    cb.__name__,
                )
                results[event_range] = False
            else:
                _check_user_callback_type(cb)

                self._cb_ranges[cb].append(event_range)
                results[event_range] = True
        return results

    def update_callable(
        self, cb: UserEventCallableType, new_cb: EventFilterCallableType
    ):
        self._derived_callback[cb] = new_cb

    def _init_store(self) -> None:
        # Map user function to it's decorator-wrapped counterpart. The values are what
        # actually get hooked to WinEvents
        self._derived_callback: Dict[
            UserEventCallableType, EventFilterCallableType
        ] = {}

        # Map user function to the event ranges it is interested in. When we run the
        # store, we register the values in _decorated_callbacks to the ranges in here.
        self._cb_ranges: Dict[
            UserEventCallableType, List[EventRangeType]
        ] = defaultdict(list)

        # Need to keep a reference to these so they don't get GC'ed.
        self._ctype_procedure_cache: List[CFuncPtr] = []

        # Store all the hooks for each user function
        self._callback_hooks_handles: Dict[
            UserEventCallableType, List[HookType]
        ] = defaultdict(list)

        # Store the python functions that get called by windows hooks.  AKA, the values
        # here are the functions that get returned from `make_func_hookable`
        self._callback_hooks: Dict[
            UserEventCallableType, List[WinEventHookCallbackType]
        ] = defaultdict(list)

    def clear_store(self) -> None:
        self.unregister_all_hooks()
        self._init_store()

    def is_registered_for(self, cb: UserEventCallableType, event_range: EventRangeType):
        return event_range in self._cb_ranges.get(cb, [])

    def hooks(self):
        return chain.from_iterable(self._callback_hooks_handles.values())

    def get_hookable(self, cb: UserEventCallableType) -> WinEventHookCallbackType:
        return make_func_hookable(self._derived_callback.get(cb, cb))

    def msg_loop(self, stop_in: Optional[float] = None):
        logger.info("Starting message loop...")
        self._running = True

        # if stop_in is not None:
        #     threading.Thread(target=self._stop, args=(stop_in,), daemon=True).start()
        started_at = time.time()
        try:
            # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch06s10.html
            while self._running:
                rc = win32event.MsgWaitForMultipleObjects(
                    (STOP_EVENT,),
                    0,
                    self.msg_loop_timeout,
                    win32event.QS_ALLEVENTS,
                )

                if stop_in is not None and (time.time() - started_at) > stop_in:
                    logger.debug(f"Message loop ending because of user time limit.")
                    break

                if rc != 258:
                    # 258 gets fired every 200ms because of our timeout. Let's not
                    # spam the logs.
                    logger.debug(f"{rc=}")

                if rc == win32event.WAIT_OBJECT_0:
                    logger.debug("all done")
                    break
                elif rc == win32event.WAIT_OBJECT_0 + 1:
                    # noinspection PyBroadException
                    try:
                        if pythoncom.PumpWaitingMessages():
                            logger.debug("WM_QUIT")
                            # received WM_QUIT...which I don't think will ever happen
                            # for this library at least.
                            break
                    except Exception as e:
                        logger.exception("Error in message loop. (%s)", e)
                        break
                elif rc == win32event.WAIT_TIMEOUT:
                    continue
                else:
                    logger.error("Error in message loop.  Unexpected win32wait error.")

        finally:
            self.unregister_all_hooks()

    def unregister_all_hooks(self):
        for hook in self.hooks():
            unregister_hook(hook)
        for callback in self._callback_hooks_handles:
            self._callback_hooks_handles[callback] = []

    def _stop(self, stop_in: float) -> None:
        time.sleep(stop_in)
        self._running = False

    def run(self, stop_in: Optional[float] = None) -> None:
        """
        Runs the message loop after hooking user's callbacks.

        :param stop_in: If provided, will stop message loop in this many seconds.
            Approximately.
        """
        logger.info(
            "Hooking %s callbacks to %s event ranges.",
            len(self._cb_ranges),
            len(list(chain.from_iterable(self._cb_ranges.values()))),
        )

        for callback in self._cb_ranges:
            for event_range in self._cb_ranges[callback]:
                logger.debug("Hooking '%s' to %s.", callback.__name__, event_range)
                hookable_callback = self.get_hookable(callback)
                win_event_proc = WIN_EVENT_PROC_TYPE(hookable_callback)
                self._ctype_procedure_cache.append(win_event_proc)
                hook = user32.SetWinEventHook(
                    event_range[0],
                    event_range[1],
                    0,
                    win_event_proc,
                    0,
                    0,
                    WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
                )
                self._callback_hooks_handles[callback].append(hook)
        self.msg_loop(stop_in)


callback_store = Store()


def unregister_hook(hook: int, raise_on_err: bool = True):
    try:
        user32.UnhookWinEvent(hook)
    except ctypes.ArgumentError:
        # TODO: Sometimes hook ints are too big and we get the following
        #  error: ctypes.ArgumentError: argument 1: <class
        #  'OverflowError'>: int too long to convert
        #  This will cause us to have lingering hooks if the interpreter
        #  doesn't exit.
        if raise_on_err:
            raise
        return False

    return True


def _check_user_callback_type(callback):
    sig = inspect.signature(callback)
    if not (
        (
            len(sig.parameters) == 1
            and sig.parameters[list(sig.parameters.keys())[0]].annotation == EventData
        )
    ):
        raise KeyError(
            f"`{callback.__name__}` is not a callable taking one argument with a type "
            f"of `EventData`"
        )


def make_func_hookable(func: UserEventCallableType) -> WinEventHookCallbackType:
    """
    Creates a function with a signature compatible with :py:data:`WIN_EVENT_PROC_TYPE`

    :param func: The function we want to compatible-ize.
    """

    def _hook_cb(
        hook_handle: int,
        event: int,
        window_handle: int,
        object_id: int,
        child_id: int,
        thread: int,
        time_ms: int,
    ):
        logger.debug(f"'{func.__name__}' hook called")
        return func(
            EventData(
                window=Window(window_handle) if window_handle else window_handle,
                event_info=CallbackReturn(
                    hook_handle=hook_handle,
                    event=event,
                    event_name=win_events.get(event, ""),
                    window_handle=window_handle,
                    object_id=object_id,
                    child_id=child_id,
                    thread=thread,
                    time_ms=time_ms,
                ),
            )
        )

    return _hook_cb


def coerce_event_types(
    events: Union[EventRangesType, EventRangeType, EventType]
) -> EventRangesType:
    if isinstance(events, int):
        return [(events, events)]

    elif is_collection_of_ints(events):
        return [events]

    elif is_collection_of_collection_of_ints(events):
        return events

    else:
        raise TypeError(
            f"`events` arg should be an int, a sequence of ints, "
            f"or a sequence of sequences of ints"
        )
