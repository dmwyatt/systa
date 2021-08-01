from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pprint import pformat
from typing import (
    Any,
    Callable,
    Dict,
    Literal,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

from systa.windows import Window


@dataclass
class CallbackReturn:
    """The data given to us by Windows when it calls our callback."""

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
    """The data structure returned to the user's function.

    :param window: A :class:`systa.windows.Window` instance associated with the event.
    :param event_info: The raw data provided to us by Windows when the event fired.
    :param context: A general purpose dict for transferring info between users of
        this data.
    """

    window: Optional[Window] = None
    event_info: Optional[CallbackReturn] = None
    context: Optional[Dict[Any, Any]] = field(default_factory=dict)

    def is_empty_data(self):
        return (
            self.window is None and self.event_info is None and len(self.context) == 0
        )

    def pformat(self, **kwargs):
        return pformat(asdict(self), **kwargs)

    @classmethod
    def get_empty(cls) -> "EventData":
        return cls()


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


EventAiaStartType = Literal[0xA000]
EventAiaEndType = Literal[0xAFFF]
EventMinType = Literal[0x00000001]
EventMaxType = Literal[0x7FFFFFFF]
EventObjectAcceleratorChangeType = Literal[0x8012]
EventObjectCloakedType = Literal[0x8017]
EventObjectContentScrolledType = Literal[0x8015]
EventObjectCreateType = Literal[0x8000]
EventObjectDefActionChangeType = Literal[0x8011]
EventObjectDescriptionChangeType = Literal[0x800D]
EventObjectDestroyType = Literal[0x8001]
EventObjectDragStartType = Literal[0x8021]
EventObjectDragCancelType = Literal[0x8022]
EventObjectDragCompleteType = Literal[0x8023]
EventObjectDragEnterType = Literal[0x8024]
EventObjectDragLeaveType = Literal[0x8025]
EventObjectDragDroppedType = Literal[0x8026]
EventObjectEndType = Literal[0x80FF]
EventObjectFocusType = Literal[0x8005]
EventObjectHelpChangeType = Literal[0x8010]
EventObjectHideType = Literal[0x8003]
EventObjectHostedObjectsInvalidatedType = Literal[0x8020]
EventObjectIMEHideType = Literal[0x8028]
EventObjectIMEShowType = Literal[0x8027]
EventObjectIMEChangeType = Literal[0x8029]
EventObjectInvokedType = Literal[0x8013]
EventObjectLiveRegionChangedType = Literal[0x8019]
EventObjectLocationChangeType = Literal[0x800B]
EventObjectNameChangeType = Literal[0x800C]
EventObjectParentChangeType = Literal[0x800F]
EventObjectReorderType = Literal[0x8004]
EventObjectSelectionType = Literal[0x8006]
EventObjectSelectionAddType = Literal[0x8007]
EventObjectSelectionRemoveType = Literal[0x8008]
EventObjectSelectionWithinType = Literal[0x8009]
EventObjectShowType = Literal[0x8002]
EventObjectStateChangeType = Literal[0x800A]
EventObjectTextEditConversionTargetChangedType = Literal[0x8030]
EventObjectTextSelectionChangedType = Literal[0x8014]
EventObjectUncloakedType = Literal[0x8018]
EventObjectValueChangeType = Literal[0x800E]
EventOemDefinedStartType = Literal[0x0101]
EventOemDefinedEndType = Literal[0x01FF]
EventSystemAlertType = Literal[0x0002]
EventSystemArrangmentPreviewType = Literal[0x8016]
EventSystemCaptureEndType = Literal[0x0009]
EventSystemCaptureStartType = Literal[0x0008]
EventSystemContextHelpEndType = Literal[0x000D]
EventSystemContextHelpStartType = Literal[0x000C]
EventSystemDesktopSwitchType = Literal[0x0020]
EventSystemDialogEndType = Literal[0x0011]
EventSystemDialogStartType = Literal[0x0010]
EventSystemDragDropEndType = Literal[0x000F]
EventSystemDragDropStartType = Literal[0x000E]
EventSystemEndType = Literal[0x00FF]
EventSystemForegroundType = Literal[0x0003]
EventSystemMenuPopupEndType = Literal[0x0007]
EventSystemMenuPopupStartType = Literal[0x0006]
EventSystemMenuEndType = Literal[0x0005]
EventSystemMenuStartType = Literal[0x0004]
EventSystemMinimizeEndType = Literal[0x0017]
EventSystemMinimizeStartType = Literal[0x0016]
EventSystemMoveSizeEndType = Literal[0x000B]
EventSystemMoveSizeStartType = Literal[0x000A]
EventSystemScrollingEndType = Literal[0x0013]
EventSystemScrollingStartType = Literal[0x0012]
EventSystemSoundType = Literal[0x0001]
EventSystemSwitchEndType = Literal[0x0015]
EventSystemSwitchStartType = Literal[0x0014]
EventUiaEventIdStartType = Literal[0x4E00]
EventUiaEventIdEndType = Literal[0x4EFF]
EventUiaPropIdStartType = Literal[0x7500]
EventUiaPropIdEndType = Literal[0x75FF]
EventTypeNamesType = Literal[
    "EVENT_OBJECT_ACCELERATORCHANGE",
    "EVENT_OBJECT_CLOAKED",
    "EVENT_OBJECT_CONTENTSCROLLED",
    "EVENT_OBJECT_CREATE",
    "EVENT_OBJECT_DEFACTIONCHANGE",
    "EVENT_OBJECT_DESCRIPTIONCHANGE",
    "EVENT_OBJECT_DESTROY",
    "EVENT_OBJECT_DRAGSTART",
    "EVENT_OBJECT_DRAGCANCEL",
    "EVENT_OBJECT_DRAGCOMPLETE",
    "EVENT_OBJECT_DRAGENTER",
    "EVENT_OBJECT_DRAGLEAVE",
    "EVENT_OBJECT_DRAGDROPPED",
    "EVENT_OBJECT_END",
    "EVENT_OBJECT_FOCUS",
    "EVENT_OBJECT_HELPCHANGE",
    "EVENT_OBJECT_HIDE",
    "EVENT_OBJECT_HOSTEDOBJECTSINVALIDATED",
    "EVENT_OBJECT_IME_HIDE",
    "EVENT_OBJECT_IME_SHOW",
    "EVENT_OBJECT_IME_CHANGE",
    "EVENT_OBJECT_INVOKED",
    "EVENT_OBJECT_LIVEREGIONCHANGED",
    "EVENT_OBJECT_LOCATIONCHANGE",
    "EVENT_OBJECT_NAMECHANGE",
    "EVENT_OBJECT_PARENTCHANGE",
    "EVENT_OBJECT_REORDER",
    "EVENT_OBJECT_SELECTION",
    "EVENT_OBJECT_SELECTIONADD",
    "EVENT_OBJECT_SELECTIONREMOVE",
    "EVENT_OBJECT_SELECTIONWITHIN",
    "EVENT_OBJECT_SHOW",
    "EVENT_OBJECT_STATECHANGE",
    "EVENT_OBJECT_TEXTEDIT_CONVERSIONTARGETCHANGED",
    "EVENT_OBJECT_TEXTSELECTIONCHANGED",
    "EVENT_OBJECT_UNCLOAKED",
    "EVENT_OBJECT_VALUECHANGE",
    "EVENT_OEM_DEFINED_START",
    "EVENT_OEM_DEFINED_END",
    "EVENT_SYSTEM_ALERT",
    "EVENT_SYSTEM_ARRANGMENTPREVIEW",
    "EVENT_SYSTEM_CAPTUREEND",
    "EVENT_SYSTEM_CAPTURESTART",
    "EVENT_SYSTEM_CONTEXTHELPEND",
    "EVENT_SYSTEM_CONTEXTHELPSTART",
    "EVENT_SYSTEM_DESKTOPSWITCH",
    "EVENT_SYSTEM_DIALOGEND",
    "EVENT_SYSTEM_DIALOGSTART",
    "EVENT_SYSTEM_DRAGDROPEND",
    "EVENT_SYSTEM_DRAGDROPSTART",
    "EVENT_SYSTEM_END",
    "EVENT_SYSTEM_FOREGROUND",
    "EVENT_SYSTEM_MENUPOPUPEND",
    "EVENT_SYSTEM_MENUPOPUPSTART",
    "EVENT_SYSTEM_MENUEND",
    "EVENT_SYSTEM_MENUSTART",
    "EVENT_SYSTEM_MINIMIZEEND",
    "EVENT_SYSTEM_MINIMIZESTART",
    "EVENT_SYSTEM_MOVESIZEEND",
    "EVENT_SYSTEM_MOVESIZESTART",
    "EVENT_SYSTEM_SCROLLINGEND",
    "EVENT_SYSTEM_SCROLLINGSTART",
    "EVENT_SYSTEM_SOUND",
    "EVENT_SYSTEM_SWITCHEND",
    "EVENT_SYSTEM_SWITCHSTART",
    "EVENT_UIA_EVENTID_START",
    "EVENT_UIA_EVENTID_END",
    "EVENT_UIA_PROPID_START",
    "EVENT_UIA_PROPID_END",
]
ObjIdAlertType = Literal[-10]
ObjIdCaretType = Literal[-8]
ObjIdClientType = Literal[-4]
ObjIdCursorType = Literal[-9]
ObjIdHscrollType = Literal[-6]
ObjIdNativeOmType = Literal[-16]
ObjIdQueryClassNameIdxListBoxType = Literal[65536]
ObjIdQueryClassNameIdxButtonType = Literal[65538]
ObjIdQueryClassNameIdxStaticType = Literal[65539]
ObjIdQueryClassNameIdxEditType = Literal[65540]
ObjIdQueryClassNameIdxComboBoxType = Literal[65541]
ObjIdQueryClassNameIdxScrollBarType = Literal[65546]
ObjIdQueryClassNameIdxStatusType = Literal[65547]
ObjIdQueryClassNameIdxToolBarType = Literal[65548]
ObjIdQueryClassNameIdxProgressType = Literal[65578]
ObjIdQueryClassNameIdxAnimateType = Literal[65550]
ObjIdQueryClassNameIdxTabType = Literal[65551]
ObjIdQueryClassNameIdxHotKeyType = Literal[65552]
ObjIdQueryClassNameIdxHeaderType = Literal[65553]
ObjIdQueryClassNameIdxTrackBarType = Literal[65554]
ObjIdQueryClassNameIdxListViewType = Literal[65555]
ObjIdQueryClassNameIdxUpDownType = Literal[65558]
ObjIdQueryClassNameIdxToolTipsType = Literal[65560]
ObjIdQueryClassNameIdxTreeViewType = Literal[65561]
ObjIdQueryClassNameIdxRichEditType = Literal[65564]
ObjIdType = Literal[
    ObjIdQueryClassNameIdxListBoxType,
    ObjIdQueryClassNameIdxButtonType,
    ObjIdQueryClassNameIdxStaticType,
    ObjIdQueryClassNameIdxEditType,
    ObjIdQueryClassNameIdxComboBoxType,
    ObjIdQueryClassNameIdxScrollBarType,
    ObjIdQueryClassNameIdxStatusType,
    ObjIdQueryClassNameIdxToolBarType,
    ObjIdQueryClassNameIdxProgressType,
    ObjIdQueryClassNameIdxAnimateType,
    ObjIdQueryClassNameIdxTabType,
    ObjIdQueryClassNameIdxHotKeyType,
    ObjIdQueryClassNameIdxHeaderType,
    ObjIdQueryClassNameIdxTrackBarType,
    ObjIdQueryClassNameIdxListViewType,
    ObjIdQueryClassNameIdxUpDownType,
    ObjIdQueryClassNameIdxToolTipsType,
    ObjIdQueryClassNameIdxTreeViewType,
    ObjIdQueryClassNameIdxRichEditType,
]
ObjIdNameType = Literal[
    "OBJID_ALERT",
    "OBJID_CARET",
    "OBJID_CLIENT",
    "OBJID_CURSOR",
    "OBJID_HSCROLL",
    "OBJID_NATIVEOM",
    "OBJID_MENU",
    "OBJID_QUERYCLASSNAMEIDX_Listbox",
    "OBJID_QUERYCLASSNAMEIDX_Button",
    "OBJID_QUERYCLASSNAMEIDX_Static",
    "OBJID_QUERYCLASSNAMEIDX_Edit",
    "OBJID_QUERYCLASSNAMEIDX_Combobox",
    "OBJID_QUERYCLASSNAMEIDX_Scrollbar",
    "OBJID_QUERYCLASSNAMEIDX_Status",
    "OBJID_QUERYCLASSNAMEIDX_Toolbar",
    "OBJID_QUERYCLASSNAMEIDX_Progress",
    "OBJID_QUERYCLASSNAMEIDX_Animate",
    "OBJID_QUERYCLASSNAMEIDX_Tab",
    "OBJID_QUERYCLASSNAMEIDX_Hotkey",
    "OBJID_QUERYCLASSNAMEIDX_Header",
    "OBJID_QUERYCLASSNAMEIDX_Trackbar",
    "OBJID_QUERYCLASSNAMEIDX_Listview",
    "OBJID_QUERYCLASSNAMEIDX_Updown",
    "OBJID_QUERYCLASSNAMEIDX_Tooltips",
    "OBJID_QUERYCLASSNAMEIDX_Treeview",
    "OBJID_QUERYCLASSNAMEIDX_RichEdit",
    "OBJID_SIZEGRIP",
    "OBJID_SOUND",
    "OBJID_SYSMENU",
    "OBJID_VSCROLL",
    "OBJID_WINDOW",
]

EventType = Literal[
    EventAiaStartType,
    EventAiaEndType,
    EventMinType,
    EventMaxType,
    EventObjectAcceleratorChangeType,
    EventObjectCloakedType,
    EventObjectContentScrolledType,
    EventObjectCreateType,
    EventObjectDefActionChangeType,
    EventObjectDescriptionChangeType,
    EventObjectDestroyType,
    EventObjectDragStartType,
    EventObjectDragCancelType,
    EventObjectDragCompleteType,
    EventObjectDragEnterType,
    EventObjectDragLeaveType,
    EventObjectDragDroppedType,
    EventObjectEndType,
    EventObjectFocusType,
    EventObjectHelpChangeType,
    EventObjectHideType,
    EventObjectHostedObjectsInvalidatedType,
    EventObjectIMEHideType,
    EventObjectIMEShowType,
    EventObjectIMEChangeType,
    EventObjectInvokedType,
    EventObjectLiveRegionChangedType,
    EventObjectLocationChangeType,
    EventObjectNameChangeType,
    EventObjectParentChangeType,
    EventObjectReorderType,
    EventObjectSelectionType,
    EventObjectSelectionAddType,
    EventObjectSelectionRemoveType,
    EventObjectSelectionWithinType,
    EventObjectShowType,
    EventObjectStateChangeType,
    EventObjectTextEditConversionTargetChangedType,
    EventObjectTextSelectionChangedType,
    EventObjectUncloakedType,
    EventObjectValueChangeType,
    EventOemDefinedStartType,
    EventOemDefinedEndType,
    EventSystemAlertType,
    EventSystemArrangmentPreviewType,
    EventSystemCaptureEndType,
    EventSystemCaptureStartType,
    EventSystemContextHelpEndType,
    EventSystemContextHelpStartType,
    EventSystemDesktopSwitchType,
    EventSystemDialogEndType,
    EventSystemDialogStartType,
    EventSystemDragDropEndType,
    EventSystemDragDropStartType,
    EventSystemEndType,
    EventSystemForegroundType,
    EventSystemMenuPopupEndType,
    EventSystemMenuPopupStartType,
    EventSystemMenuEndType,
    EventSystemMenuStartType,
    EventSystemMinimizeEndType,
    EventSystemMinimizeStartType,
    EventSystemMoveSizeEndType,
    EventSystemMoveSizeStartType,
    EventSystemScrollingEndType,
    EventSystemScrollingStartType,
    EventSystemSoundType,
    EventSystemSwitchEndType,
    EventSystemSwitchStartType,
    EventUiaEventIdStartType,
    EventUiaEventIdEndType,
    EventUiaPropIdStartType,
    EventUiaPropIdEndType,
]
"""Literal values used to select events."""

CheckableEventResultType = TypeVar("CheckableEventResultType")


@runtime_checkable
class CheckableEvent(Protocol[CheckableEventResultType]):
    def check(self) -> bool:
        ...

    def result(self, data: Optional[EventData] = None) -> CheckableEventResultType:
        ...


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
