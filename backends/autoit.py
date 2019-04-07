import inspect
from enum import IntEnum
from functools import lru_cache, wraps
from typing import Iterator, List, Optional, Tuple

import win32com.client

from exceptions import NoMatchingWindowError
from utils import cached_property
from backends.win_access import MouseButton, MouseControllerBase, WinAccessBase


class WinState(IntEnum):
    EXISTS = 1
    VISIBLE = 2
    ENABLED = 4
    ACTIVE = 8
    MINIMIZED = 16
    MAXIMIZED = 32


@lru_cache(maxsize=1000)
def auto_it_int_to_hex(val: int) -> str:
    return f'{val:#0{10}x}'.upper()


@lru_cache(maxsize=1000)
def add_handle_str_params(val: str) -> str:
    return f'[HANDLE:{val}]'


@lru_cache(maxsize=1000)
def convert_int_to_autoit_function_handle_format(handle: int) -> str:
    return add_handle_str_params(auto_it_int_to_hex(handle))


def autoit_handle(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_sig = inspect.signature(func)

        pos = 0
        for param in func_sig.parameters:
            # find the parameter called 'handle' and format it for autoit
            if param == 'handle' and isinstance(args[pos], int):
                args = list(args)
                args[pos] = convert_int_to_autoit_function_handle_format(args[pos])
                break
            pos += 1

        return func(*args, **kwargs)

    return wrapper


class WinAccess(WinAccessBase):
    """
    Low level access to windows.

    While "low level" might scare you off, this is a perfectly usable class and might be all you
    want to use.
    """

    @cached_property
    def _accessor(self):
        ai = win32com.client.Dispatch("AutoItX3.Control")
        ai.Opt("WinTitleMatchMode", 3)
        ai.Opt("WinWaitDelay", 20)
        return ai

    @cached_property
    def mouse(self) -> 'MouseControllerBase':
        return AutoItMouseController(self._accessor)

    @autoit_handle
    def get_title(self, handle: int) -> str:
        title = self._accessor.WinGetTitle(handle)

        # AutoItX will return an empty string if the window does not exist and also for windows
        # that do not have a title.  So, if we get an empty string, we have to check if the
        # window exists before raising.
        if title == "" and not self.get_exists(handle):
            raise NoMatchingWindowError(f'Window with this handle does not exist: {handle}')

        return title

    def get_handle(self, title: str) -> List[int]:
        value = list(iter_winlist(self._accessor.WinList(title)))

        if not value:
            raise NoMatchingWindowError(f'No windows found with title: {title}')

        return [x[1] for x in value]

    def get_titles_and_handles(self, selector: str = "[ALL]"
                               ) -> Iterator[Tuple[str, int]]:
        return iter_winlist(self._accessor.WinList(selector))

    @autoit_handle
    def get_is_active(self, handle: int) -> bool:
        return (self._accessor.WinGetState(handle) & WinState.ACTIVE) == WinState.ACTIVE

    @autoit_handle
    def get_exists(self, handle: int) -> bool:
        return self._accessor.WinExists(handle) == 1

    @autoit_handle
    def get_is_visible(self, handle: int) -> bool:
        return (self._accessor.WinGetState(handle) & WinState.VISIBLE) == WinState.VISIBLE

    @autoit_handle
    def get_is_enabled(self, handle: int) -> bool:
        return (self._accessor.WinGetState(handle) & WinState.ENABLED) == WinState.ENABLED

    @autoit_handle
    def get_is_minimized(self, handle: int) -> bool:
        return (self._accessor.WinGetState(handle) & WinState.MINIMIZED) == WinState.MINIMIZED

    @autoit_handle
    def get_is_maximized(self, handle: int) -> bool:
        return (self._accessor.WinGetState(handle) & WinState.MAXIMIZED) == WinState.MAXIMIZED

    @autoit_handle
    def activate_window(self, handle: int) -> None:
        self._accessor.WinActivate(handle)

    @autoit_handle
    def get_win_x_pos(self, handle: int) -> int:
        return self._accessor.WinGetPosX(handle)

    @autoit_handle
    def get_win_y_pos(self, handle: int) -> int:
        return self._accessor.WinGetPosY(handle)

    @autoit_handle
    def get_win_height(self, handle: int) -> int:
        return self._accessor.WinGetPosHeight(handle)

    @autoit_handle
    def get_win_width(self, handle: int) -> int:
        return self._accessor.WinGetPosWidth(handle)

    @autoit_handle
    def close_window(self, handle: int):
        self._accessor.WinClose(handle)

    @autoit_handle
    def get_process_id(self, handle: int) -> int:
        return int(self._accessor.WinGetProcess(handle))


WinListReturnType = Tuple[Tuple[str, ...], Tuple[int, ...]]


def iter_winlist(data: WinListReturnType) -> Iterator[Tuple[str, int]]:
    handles: Tuple[int, ...] = tuple(int(f'0x{x}', 16) for x in data[1][1:])
    titles: Tuple[str, ...] = tuple(data[0][1:])
    assert len(handles) == len(titles)

    return zip(titles, handles)


class AutoItMouseController(MouseControllerBase):
    def __init__(self, controller):
        self._controller = controller

    def move_to(self, x: int, y: int) -> None:
        self._controller.MouseMove(x, y, 0)

    def click(self, x: Optional[int] = None,
              y: Optional[int] = None,
              button: Optional[MouseButton] = None,
              click_count: int = 1) -> None:
        if button is None or button == MouseButton.primary:
            click_button = "primary"
        elif button == MouseButton.secondary:
            click_button = "secondary"
        elif button == MouseButton.middle:
            click_button = "middle"
        else:
            raise ValueError(f'{button} is not a valid value for the `button` parameter.')

        if x is None and y is None:
            x, y = self.x_pos, self.y_pos
        if not all((x, y)):
            raise ValueError(f'Must provide x AND y values.')
        self._controller.MouseClick(click_button, x, y, click_count, 0)

    @property
    def x_pos(self) -> int:
        return self._controller.MouseGetPosX()

    @property
    def y_pos(self) -> int:
        return self._controller.MouseGetPosY()
