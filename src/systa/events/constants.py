from fnmatch import fnmatchcase
from typing import (
    Any,
    Dict,
    ItemsView,
    KeysView,
    Literal,
    Tuple,
    Union,
    ValuesView,
    get_args,
)

from win32con import (
    OBJID_ALERT,
    OBJID_CARET,
    OBJID_CLIENT,
    OBJID_CURSOR,
    OBJID_HSCROLL,
    OBJID_MENU,
    OBJID_SIZEGRIP,
    OBJID_SOUND,
    OBJID_SYSMENU,
    OBJID_VSCROLL,
    OBJID_WINDOW,
)

# region Event type literals
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
# endregion

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

EventTypeNamesType = Literal[
    "EventAiaStartType",
    "EventAiaEndType",
    "EventMinType",
    "EventMaxType",
    "EventObjectAcceleratorChangeType",
    "EventObjectCloakedType",
    "EventObjectContentScrolledType",
    "EventObjectCreateType",
    "EventObjectDefActionChangeType",
    "EventObjectDescriptionChangeType",
    "EventObjectDestroyType",
    "EventObjectDragStartType",
    "EventObjectDragCancelType",
    "EventObjectDragCompleteType",
    "EventObjectDragEnterType",
    "EventObjectDragLeaveType",
    "EventObjectDragDroppedType",
    "EventObjectEndType",
    "EventObjectFocusType",
    "EventObjectHelpChangeType",
    "EventObjectHideType",
    "EventObjectHostedObjectsInvalidatedType",
    "EventObjectIMEHideType",
    "EventObjectIMEShowType",
    "EventObjectIMEChangeType",
    "EventObjectInvokedType",
    "EventObjectLiveRegionChangedType",
    "EventObjectLocationChangeType",
    "EventObjectNameChangeType",
    "EventObjectParentChangeType",
    "EventObjectReorderType",
    "EventObjectSelectionType",
    "EventObjectSelectionAddType",
    "EventObjectSelectionRemoveType",
    "EventObjectSelectionWithinType",
    "EventObjectShowType",
    "EventObjectStateChangeType",
    "EventObjectTextEditConversionTargetChangedType",
    "EventObjectTextSelectionChangedType",
    "EventObjectUncloakedType",
    "EventObjectValueChangeType",
    "EventOemDefinedStartType",
    "EventOemDefinedEndType",
    "EventSystemAlertType",
    "EventSystemArrangmentPreviewType",
    "EventSystemCaptureEndType",
    "EventSystemCaptureStartType",
    "EventSystemContextHelpEndType",
    "EventSystemContextHelpStartType",
    "EventSystemDesktopSwitchType",
    "EventSystemDialogEndType",
    "EventSystemDialogStartType",
    "EventSystemDragDropEndType",
    "EventSystemDragDropStartType",
    "EventSystemEndType",
    "EventSystemForegroundType",
    "EventSystemMenuPopupEndType",
    "EventSystemMenuPopupStartType",
    "EventSystemMenuEndType",
    "EventSystemMenuStartType",
    "EventSystemMinimizeEndType",
    "EventSystemMinimizeStartType",
    "EventSystemMoveSizeEndType",
    "EventSystemMoveSizeStartType",
    "EventSystemScrollingEndType",
    "EventSystemScrollingStartType",
    "EventSystemSoundType",
    "EventSystemSwitchEndType",
    "EventSystemSwitchStartType",
    "EventUiaEventIdStartType",
    "EventUiaEventIdEndType",
    "EventUiaPropIdStartType",
    "EventUiaPropIdEndType",
]

EVENT_VALUES = []
for literal_type in get_args(EventType):
    EVENT_VALUES.append(get_args(literal_type)[0])


class _WinEvent:
    # https://docs.microsoft.com/en-us/windows/win32/winauto/event-constants

    _event_prefixes = ("EVENT_",)

    _EVENT_AIA_START = 0xA000
    _EVENT_AIA_END = 0xAFFF
    ALL_AIA_EVENTS_RANGE = (
        _EVENT_AIA_START,
        _EVENT_AIA_END,
    )

    EVENT_MIN = 0x00000001
    EVENT_MAX = 0x7FFFFFFF
    ALL_EVENTS_RANGE = (EVENT_MIN, EVENT_MAX)

    EVENT_OBJECT_ACCELERATORCHANGE = 0x8012
    EVENT_OBJECT_CLOAKED = 0x8017
    EVENT_OBJECT_CONTENTSCROLLED = 0x8015
    EVENT_OBJECT_CREATE = 0x8000
    EVENT_OBJECT_DEFACTIONCHANGE = 0x8011
    EVENT_OBJECT_DESCRIPTIONCHANGE = 0x800D
    EVENT_OBJECT_DESTROY = 0x8001
    EVENT_OBJECT_DRAGSTART = 0x8021
    EVENT_OBJECT_DRAGCANCEL = 0x8022
    EVENT_OBJECT_DRAGCOMPLETE = 0x8023
    EVENT_OBJECT_DRAGENTER = 0x8024
    EVENT_OBJECT_DRAGLEAVE = 0x8025
    EVENT_OBJECT_DRAGDROPPED = 0x8026
    EVENT_OBJECT_END = 0x80FF
    EVENT_OBJECT_FOCUS = 0x8005
    EVENT_OBJECT_HELPCHANGE = 0x8010
    EVENT_OBJECT_HIDE = 0x8003
    EVENT_OBJECT_HOSTEDOBJECTSINVALIDATED = 0x8020
    EVENT_OBJECT_IME_HIDE = 0x8028
    EVENT_OBJECT_IME_SHOW = 0x8027
    EVENT_OBJECT_IME_CHANGE = 0x8029
    EVENT_OBJECT_INVOKED = 0x8013
    EVENT_OBJECT_LIVEREGIONCHANGED = 0x8019
    EVENT_OBJECT_LOCATIONCHANGE = 0x800B
    EVENT_OBJECT_NAMECHANGE = 0x800C
    EVENT_OBJECT_PARENTCHANGE = 0x800F
    EVENT_OBJECT_REORDER = 0x8004
    EVENT_OBJECT_SELECTION = 0x8006
    EVENT_OBJECT_SELECTIONADD = 0x8007
    EVENT_OBJECT_SELECTIONREMOVE = 0x8008
    EVENT_OBJECT_SELECTIONWITHIN = 0x8009
    EVENT_OBJECT_SHOW = 0x8002
    EVENT_OBJECT_STATECHANGE = 0x800A
    EVENT_OBJECT_TEXTEDIT_CONVERSIONTARGETCHANGED = 0x8030
    EVENT_OBJECT_TEXTSELECTIONCHANGED = 0x8014
    EVENT_OBJECT_UNCLOAKED = 0x8018
    EVENT_OBJECT_VALUECHANGE = 0x800E
    EVENT_OEM_DEFINED_START = 0x0101
    EVENT_OEM_DEFINED_END = 0x01FF
    EVENT_SYSTEM_ALERT = 0x0002
    EVENT_SYSTEM_ARRANGMENTPREVIEW = 0x8016
    EVENT_SYSTEM_CAPTUREEND = 0x0009
    EVENT_SYSTEM_CAPTURESTART = 0x0008
    EVENT_SYSTEM_CONTEXTHELPEND = 0x000D
    EVENT_SYSTEM_CONTEXTHELPSTART = 0x000C
    EVENT_SYSTEM_DESKTOPSWITCH = 0x0020
    EVENT_SYSTEM_DIALOGEND = 0x0011
    EVENT_SYSTEM_DIALOGSTART = 0x0010
    EVENT_SYSTEM_DRAGDROPEND = 0x000F
    EVENT_SYSTEM_DRAGDROPSTART = 0x000E
    EVENT_SYSTEM_END = 0x00FF
    EVENT_SYSTEM_FOREGROUND = 0x0003
    EVENT_SYSTEM_MENUPOPUPEND = 0x0007
    EVENT_SYSTEM_MENUPOPUPSTART = 0x0006
    EVENT_SYSTEM_MENUEND = 0x0005
    EVENT_SYSTEM_MENUSTART = 0x0004
    EVENT_SYSTEM_MINIMIZEEND = 0x0017
    EVENT_SYSTEM_MINIMIZESTART = 0x0016
    EVENT_SYSTEM_MOVESIZEEND = 0x000B
    EVENT_SYSTEM_MOVESIZESTART = 0x000A
    EVENT_SYSTEM_SCROLLINGEND = 0x0013
    EVENT_SYSTEM_SCROLLINGSTART = 0x0012
    EVENT_SYSTEM_SOUND = 0x0001
    EVENT_SYSTEM_SWITCHEND = 0x0015
    EVENT_SYSTEM_SWITCHSTART = 0x0014
    EVENT_UIA_EVENTID_START = 0x4E00
    EVENT_UIA_EVENTID_END = 0x4EFF
    EVENT_UIA_PROPID_START = 0x7500
    EVENT_UIA_PROPID_END = 0x75FF

    WINDOWS_INTERNALS_TITLES = [
        "OLEChannelWnd",
        "OleMainThreadWndName",
        "Default IME",
        "MSCTFIME UI",
        "DDE Server Window",
        "CicMarshalWnd",
        "OfficePowerManagerWindow",
        "System Clock, *",
        "System Promoted Notification Area",
        "Tray Input Indicator",
        "Action Center, *",
    ]

    @classmethod
    def _is_event_attr(cls, attr: str) -> bool:
        exclude = ["EVENT_MIN", "EVENT_MAX"]
        return (
            attr not in exclude
            and attr.isupper()
            and any(attr.startswith(y) for y in cls._event_prefixes)
        )

    def __init__(self):
        self.events: Dict[EventTypeNamesType, EventType] = {
            k: v for k, v in vars(self.__class__).items() if self._is_event_attr(k)
        }
        self.events_by_val = {v: k for k, v in self.events.items()}

    @classmethod
    def is_windows_internal_title(cls, title: str) -> bool:
        """
        Check if the provided title is for a Windows "internal" window.

        Windows has multiple "windows" that users probably do not care about like
        "OLEChannelWnd".

        :param title: The title we want to check.
        :return:
        """

        return any(
            fnmatchcase(title, internal_title)
            for internal_title in cls.WINDOWS_INTERNALS_TITLES
        )

    def values(self) -> ValuesView[EventType]:
        return self.events.values()

    def keys(self) -> KeysView[EventTypeNamesType]:
        return self.events.keys()

    def get(
        self,
        item: Union[EventType, EventTypeNamesType],
        default: Any = None,
    ) -> Union[EventType, str]:
        try:
            return self[item]
        except KeyError:
            return default

    def items(self) -> ItemsView[EventTypeNamesType, EventType]:
        return self.events.items()

    def is_valid_range(self, rng: Tuple[EventType, EventType]) -> bool:
        return (
            len(rng) == 2
            and (rng[0] < rng[1] or rng[0] == rng[1])
            and rng[0] in self
            and rng[1] in self
        )

    def __iter__(self):
        return iter(self.events)

    def __getitem__(
        self, item: Union[EventType, EventTypeNamesType]
    ) -> Union[EventType, EventTypeNamesType]:
        if isinstance(item, int):
            # Doing a "reverse" lookup by the actual event value
            return self.events_by_val[item]
        # Doing a standard lookup by event name...or it's an invalid key anyway
        return self.events[item]

    def __contains__(self, item: EventType) -> bool:
        return (
            item in self.ALL_EVENTS_RANGE
            or item in self.ALL_AIA_EVENTS_RANGE
            or item in self.values()
        )


win_events = _WinEvent()

# https://stackoverflow.com/a/34023457/23972
_OBJID_NATIVEOM = -16

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


class _ObjectIds:
    _OBJ_PREFIXES = ("OBJID_",)
    OBJID_ALERT = OBJID_ALERT
    OBJID_CARET = OBJID_CARET
    OBJID_CLIENT = OBJID_CLIENT
    OBJID_CURSOR = OBJID_CURSOR
    OBJID_HSCROLL = OBJID_HSCROLL

    OBJID_NATIVEOM = _OBJID_NATIVEOM
    OBJID_MENU = OBJID_MENU

    OBJID_QUERYCLASSNAMEIDX_Listbox = get_args(ObjIdQueryClassNameIdxListBoxType)[0]
    OBJID_QUERYCLASSNAMEIDX_Button = get_args(ObjIdQueryClassNameIdxButtonType)[0]
    OBJID_QUERYCLASSNAMEIDX_Static = get_args(ObjIdQueryClassNameIdxStaticType)[0]
    OBJID_QUERYCLASSNAMEIDX_Edit = get_args(ObjIdQueryClassNameIdxEditType)[0]
    OBJID_QUERYCLASSNAMEIDX_Combobox = get_args(ObjIdQueryClassNameIdxComboBoxType)[0]
    OBJID_QUERYCLASSNAMEIDX_Scrollbar = get_args(ObjIdQueryClassNameIdxScrollBarType)[0]
    OBJID_QUERYCLASSNAMEIDX_Status = get_args(ObjIdQueryClassNameIdxStatusType)[0]
    OBJID_QUERYCLASSNAMEIDX_Toolbar = get_args(ObjIdQueryClassNameIdxToolBarType)[0]
    OBJID_QUERYCLASSNAMEIDX_Progress = get_args(ObjIdQueryClassNameIdxProgressType)[0]
    OBJID_QUERYCLASSNAMEIDX_Animate = get_args(ObjIdQueryClassNameIdxAnimateType)[0]
    OBJID_QUERYCLASSNAMEIDX_Tab = get_args(ObjIdQueryClassNameIdxTabType)[0]
    OBJID_QUERYCLASSNAMEIDX_Hotkey = get_args(ObjIdQueryClassNameIdxHotKeyType)[0]
    OBJID_QUERYCLASSNAMEIDX_Header = get_args(ObjIdQueryClassNameIdxHeaderType)[0]
    OBJID_QUERYCLASSNAMEIDX_Trackbar = get_args(ObjIdQueryClassNameIdxTrackBarType)[0]
    OBJID_QUERYCLASSNAMEIDX_Listview = get_args(ObjIdQueryClassNameIdxListViewType)[0]
    OBJID_QUERYCLASSNAMEIDX_Updown = get_args(ObjIdQueryClassNameIdxUpDownType)[0]
    OBJID_QUERYCLASSNAMEIDX_Tooltips = get_args(ObjIdQueryClassNameIdxToolTipsType)[0]
    OBJID_QUERYCLASSNAMEIDX_Treeview = get_args(ObjIdQueryClassNameIdxTreeViewType)[0]
    OBJID_QUERYCLASSNAMEIDX_RichEdit = get_args(ObjIdQueryClassNameIdxRichEditType)[0]

    OBJID_SIZEGRIP = OBJID_SIZEGRIP
    OBJID_SOUND = OBJID_SOUND
    OBJID_SYSMENU = OBJID_SYSMENU
    OBJID_VSCROLL = OBJID_VSCROLL
    OBJID_WINDOW = OBJID_WINDOW

    def _is_object_id(self, x: str):
        return (x.isupper() or x.startswith("OBJID_QUERYCLASSNAMEIDX_")) and any(
            x.startswith(y) for y in self._OBJ_PREFIXES
        )

    def __init__(self):
        self.object_ids = {
            k: v for k, v in vars(self.__class__).items() if self._is_object_id(k)
        }
        self.object_ids_by_val = {v: k for k, v in self.object_ids.items()}

    def values(self) -> ValuesView[ObjIdType]:
        return self.object_ids.values()

    def keys(self) -> KeysView[ObjIdNameType]:
        return self.object_ids.keys()

    def get(
        self, item: Union[ObjIdType, ObjIdNameType], default: Any = None
    ) -> Union[ObjIdType, ObjIdNameType]:
        try:
            return self[item]
        except KeyError:
            return default

    def __iter__(self):
        return iter(self.object_ids)

    def __getitem__(
        self, item: Union[ObjIdType, ObjIdNameType]
    ) -> Union[ObjIdType, ObjIdNameType]:
        if isinstance(item, int):
            return self.object_ids_by_val[item]
        return self.object_ids[item]

    def __contains__(self, item: ObjIdType) -> bool:
        return item in self.values()


win_obj_ids = _ObjectIds()
