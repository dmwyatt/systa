import ctypes
import ctypes.wintypes
import functools
import time
import uuid
from collections import namedtuple
from pprint import pprint
from typing import Iterable, Union

from typing_extensions import Literal

from events.win_event_constants import WinEvents
from exceptions import WindowsMessageLoopError

EVENT_CALLBACKS = {}

EventFilter = Union[int, Literal["*"]]
EventFilters = Iterable[EventFilter]
SingleOrMultipleEventFilters = Union[EventFilter, EventFilters]


def register(events: SingleOrMultipleEventFilters):
    if events == "*":
        events = WinEvents.event_values
    if isinstance(events, int) or isinstance(events, str):
        events = [events]

    def wrapper(func):
        for event in events:
            if event in EVENT_CALLBACKS:
                EVENT_CALLBACKS[event].append(func)
            else:
                EVENT_CALLBACKS[event] = [func]
        return func

    return wrapper


def windows_msg_handler_loop():
    user32 = ctypes.windll.user32
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize(0)

    try:
        # Function
        win_event_proc_type = ctypes.WINFUNCTYPE(
            None,
            ctypes.wintypes.HANDLE,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND,
            ctypes.wintypes.LONG,
            ctypes.wintypes.LONG,
            ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD,
        )

        def win_callback(
            hWinEventHook: int,
            event: int,
            hwnd: Union[int, None],
            idObject: int,
            idChild: int,
            idEventThread: int,
            dwmsEventTime: int,
        ):
            """
            This is the callback that Windows calls for each event we register it for.

            https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nc-winuser-wineventproc

            :param hWinEventHook: Handle to an event hook function. This value is returned by
            SetWinEventHook when the hook function is installed and is specific to each instance of
            the hook function.
            :param event: Specifies the event that occurred. This value is one of
            the event constants specified in `win_event_constants.WinEvents`.
            :param hwnd: Handle to the window that generates the event, or None if no window is
            associated with the event. For example, the mouse pointer is not associated with a window.
            :param idObject: Identifies the object associated with the event. This is one of the
            object identifiers or a custom object ID.
            (https://docs.microsoft.com/en-us/windows/desktop/WinAuto/object-identifiers)
            :param idChild: Identifies whether the event was triggered by an object or a child
            element of the object. If this value is CHILDID_SELF, the event was triggered by the
            object; otherwise, this value is the child ID of the element that triggered the event.
            :param dwEventThread:
            :param dwmsEventTime: Specifies the time, in milliseconds, that the event was generated.
            """

            if event in WinEvents:
                # distribute event to all registered callbacks
                for cb in EVENT_CALLBACKS.get(event, []):
                    cb(event, hwnd)
                # handle the "all events" callback
                for cb in EVENT_CALLBACKS.get("*", []):
                    cb(event, hwnd)

        win_event_proc = win_event_proc_type(win_callback)

        winevent_outofcontext = 0x0000
        user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE
        hook = None
        try:
            # TODO: We need to do some benchmarking on this.
            #   It might be better to not use EVENT_MIN and EVENT_MAX and narrow down which
            #   events we support so that we use less CPU.
            #   We could maybe do multiple threads/processes if we need more event types?
            hook = user32.SetWinEventHook(
                WinEvents.EVENT_MIN,
                WinEvents.EVENT_MAX,
                0,
                win_event_proc,
                0,
                0,
                winevent_outofcontext,
            )
            if hook == 0:
                raise WindowsMessageLoopError("Unable to hook msg events.")

            msg = ctypes.wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessageW(msg)
                user32.DispatchMessageW(msg)

        finally:
            if hook:
                user32.UnhookWinEvent(hook)

    finally:
        ole32.CoUninitialize()


def get_window_title(hwnd: int) -> str:
    user32 = ctypes.windll.user32

    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)

    return buff.value


def on_window_title_appear(expected_title: str, case_sensitive=False, substring=True):
    def decorator(func):
        @register([WinEvents.EVENT_OBJECT_CREATE, WinEvents.EVENT_OBJECT_NAMECHANGE])
        def callback(event, hwnd):
            orig_title = get_window_title(hwnd)
            expected = expected_title
            title = orig_title
            if not case_sensitive:
                expected = expected_title.casefold()
                title = orig_title.casefold()

            if substring:
                match = expected in title
            else:
                match = expected == title
            if match:
                return func(orig_title, event, hwnd)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func

        return wrapper

    return decorator


@on_window_title_appear("Untitled - Notepad")
def print_window(title, event, hwnd):
    print(title)


def do_print_event_stream(title_substrings, print_delay=1):
    EventData = namedtuple("EventData", ["time", "event", "title", "id"])
    event_buffer = {}
    printed_events = set()

    @register("*")
    def print_event(event, hwnd):
        # clear out already printed events
        for h in event_buffer:
            event_buffer[h] = [
                evt for evt in event_buffer[h] if evt.id not in printed_events
            ]

        # add this new event to the event buffer
        data = EventData(time.time(), event, get_window_title(hwnd), uuid.uuid4().hex)
        if hwnd not in event_buffer:
            event_buffer[hwnd] = [data]
        else:
            event_buffer[hwnd].append(data)

        # check if anything is ready to print
        now = time.time()
        for h, event_datas in event_buffer.items():
            # check if any events we have for this window are older than our print delay
            should_print = any([x.time < (now - print_delay) for x in event_datas])
            if should_print:
                titles = [x.title for x in event_datas]
                for ws in title_substrings:
                    if any(ws.lower() in t.lower() for t in titles):
                        print("=" * 50)
                        pprint([(x.title, WinEvents[x.event]) for x in event_datas])
                        print("=" * 50)
                        printed_events.add()
                        event_buffer[h] = [
                            EventData(x.time, x.event, x.title, True)
                            for x in event_buffer[h]
                        ]


if __name__ == "__main__":
    # do_print_event_stream(['firefox', 'explorer', 'notepad', 'settings', 'autoit'])

    windows_msg_handler_loop()
