from __future__ import annotations

from dataclasses import asdict, dataclass
from pprint import pformat
from typing import Callable, Optional, Sequence, Tuple, Union

from systa.events.constants import EventType, EventTypeNamesType, ObjIdType
from systa.windows import Window


@dataclass
class CallbackReturn:
    hook_handle: int
    event: EventType
    event_name: EventTypeNamesType
    window_handle: int
    object_id: ObjIdType
    child_id: int
    thread: int
    time_ms: int

    def pformat(self, **kwargs):
        return pformat(asdict(self), **kwargs)


@dataclass
class EventData:
    """The data structure returned to the user's function."""

    window: Optional[Window]
    """A :class:`Window` instance associated with the event."""
    event_info: CallbackReturn
    """The raw data provided to us by Windows when the event fired."""

    def pformat(self, **kwargs):
        return pformat(asdict(self), **kwargs)


WinEventHookCallbackType = Callable[[int, int, int, int, int, int, int], None]
"""
The type of python function that can be registered as a Windows Hook.

The arguments are basically the same as the Windows WINEVENTPROC callback function.  (
See :func:`systa.events.events.WIN_EVENT_PROC_TYPE`)

The arguments, in definition order:

:param hWinEventHook: Handle to an event hook function. This value is returned by
  SetWinEventHook when the hook function is installed and is specific to each
  instance of the hook function.
:type hWinEventHook: int
  
:param event: Specifies the event that occurred. This value is one of the event
  constants.
:type event: int  
  
:param hwnd: Handle to the window that generates the event, or NULL if no window is
  associated with the event. For example, the mouse pointer is not associated with a
  window.
:type hwnd: int
  
:param idObject: Identifies the object associated with the event. This is one of
  the object identifiers or a custom object ID.
:type idObject: int
  
:param idChild: Identifies whether the event was triggered by an object or a child
  element of the object. If this value is CHILDID_SELF, the event was triggered by
  the object; otherwise, this value is the child ID of the element that triggered
  the event.
:type idChild: int
  
:param idEventThread: Thread of the event.
:type idEventThread: int

:param dwmsEventTime: Specifies the time, in milliseconds, that the event was
  generated.
:type dwmsEventTime: int
"""

EventRangeType = Tuple[EventType, EventType]
"""Type indicating beginning and ending of a range of WinEvent's.

If a user wants just a single event, then the start and end should just be that event.
"""
EventRangesType = Sequence[EventRangeType]
"""
This is the type of value the callback store takes. The callback gets hooked for 
events falling in the range described for each 2-tuple `EventRangeType`.
"""
UserEventCallableType = Callable[[EventData], None]
"""Type of a user function that is called by a WinEvent hook."""
HookType = int
EventFilterCallableType = Callable[[EventData], bool]

EventsTypes = Union[EventRangesType, EventRangeType, EventType]
"""All of the different ways of specifying events."""
