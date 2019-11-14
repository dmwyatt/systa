import inspect
from enum import IntEnum
from functools import lru_cache, wraps
from typing import Any, Iterator, List, Mapping, Optional, Sequence, Tuple

import win32com.client
from argupdate import ValueUpdater, update_parameter_value
from argupdate.argupdate import Args, Kwargs

from systa.backends import ctype
from systa.backends.win_access import WinAccessBase, MouseControllerBase, MouseButton
from systa.exceptions import NoMatchingWindowError
from systa.utils import (
    cached_property,
    exclude_method_attribute,
    get_value_by_arg_name,
    has_parameter,
    raise_on_return_value,
    method_decorator,
)


class WinState(IntEnum):
    EXISTS = 1
    VISIBLE = 2
    ENABLED = 4
    ACTIVE = 8
    MINIMIZED = 16
    MAXIMIZED = 32


@lru_cache(maxsize=1000)
def is_autoit_str_handle(val: str) -> bool:
    if not isinstance(val, str):
        return False
    return val.startswith("[HANDLE:") and val.endswith("]")


def auto_it_int_to_hex(val: int) -> str:
    return f"{val:#0{10}x}".upper()


def add_handle_str_params(val: str) -> str:
    return f"[HANDLE:{val}]"


@lru_cache(maxsize=1000)
def convert_int_to_autoit_function_handle_format(handle: int) -> str:
    return add_handle_str_params(auto_it_int_to_hex(handle))


def autoit_handle(func):
    class update_handle(ValueUpdater):
        def __call__(
            self,
            original_value: Any,
            signature: inspect.Signature,
            orig_args: Sequence[Any],
            orig_kwargs: Mapping[str, Any],
        ) -> Any:
            if isinstance(original_value, int):
                return convert_int_to_autoit_function_handle_format(original_value)
            if is_autoit_str_handle(original_value):
                return original_value
            raise TypeError(f"Unexpected value `{original_value}` for handle.")

    updated_values = {"handle": update_handle}

    @wraps(func)
    def decorator(*args, **kwargs):
        args, kwargs = update_parameter_value(func, updated_values, args, kwargs)
        return func(*args, **kwargs)

    return decorator


def _get_no_matching_window_exc(
    wrapped, return_value: Any, args: Args, kwargs: Kwargs
) -> NoMatchingWindowError:
    handle = get_value_by_arg_name(wrapped, "handle", args, kwargs)
    return NoMatchingWindowError(f"Cannot find window with handle: {handle}")


raise_on_one = raise_on_return_value(exc=_get_no_matching_window_exc, return_value=1)


@method_decorator(
    autoit_handle, [has_parameter("handle", int), exclude_method_attribute("autoit")]
)
class WinAccess(WinAccessBase):
    """
    Low level access to windows.

    While "low level" might scare you off, this is a perfectly usable class and might be all you
    want to use.
    """

    @cached_property
    def _autoit(self):
        ai = win32com.client.Dispatch("AutoItX3.Control")
        ai.Opt("WinTitleMatchMode", 4)
        ai.Opt("WinWaitDelay", 20)
        ai.Opt("MouseCoordMode", 1)
        return ai

    @cached_property
    def mouse(self) -> "MouseControllerBase":
        return AutoItMouseController(self._autoit)

    def get_title(self, handle: int) -> str:
        title = self._autoit.WinGetTitle(handle)

        # AutoItX will return an empty string if the window does not exist and also for windows
        # that do not have a title.  So, if we get an empty string, we have to check if the
        # window exists before raising.
        if (title == "" and not self.get_exists(handle)) or title == 0:
            raise NoMatchingWindowError(
                f"Window with this handle does not exist: {handle}"
            )

        return title

    def set_title(self, handle: int, title: str) -> None:
        self._autoit.WinSetTitle(handle, "", title)

    def get_handle(self, title: str) -> List[int]:
        value = list(iter_winlist(self._autoit.WinList(title)))

        if not value:
            raise NoMatchingWindowError(f"No windows found with title: {title}")

        return [x[1] for x in value]

    def get_titles_and_handles(
        self, selector: str = "[ALL]"
    ) -> Iterator[Tuple[str, int]]:
        return iter_winlist(self._autoit.WinList(selector))

    def get_is_active(self, handle: int) -> bool:
        return (self._autoit.WinGetState(handle) & WinState.ACTIVE) == WinState.ACTIVE

    def get_exists(self, handle: int) -> bool:
        return self._autoit.WinExists(handle) == 1

    def get_is_visible(self, handle: int) -> bool:
        return (self._autoit.WinGetState(handle) & WinState.VISIBLE) == WinState.VISIBLE

    def get_is_enabled(self, handle: int) -> bool:
        return (self._autoit.WinGetState(handle) & WinState.ENABLED) == WinState.ENABLED

    def get_is_minimized(self, handle: int) -> bool:
        return (
            self._autoit.WinGetState(handle) & WinState.MINIMIZED
        ) == WinState.MINIMIZED

    def set_minimized(self, handle: int) -> None:
        return self._autoit.WinSetState(handle, "", self._autoit.SW_MINIMIZE)

    def get_is_maximized(self, handle: int) -> bool:
        return (
            self._autoit.WinGetState(handle) & WinState.MAXIMIZED
        ) == WinState.MAXIMIZED

    def set_maximized(self, handle: int) -> None:
        return self._autoit.WinSetState(handle, "", self._autoit.SW_MAXIMIZE)

    def restore(self, handle: int) -> None:
        return self._autoit.WinSetState(handle, "", self._autoit.SW_RESTORE)

    def activate_window(self, handle: int) -> None:
        self._autoit.WinActivate(handle)

    @raise_on_one
    def get_win_x_pos(self, handle: int) -> int:
        pos = self._autoit.WinGetPosX(handle)
        return pos

    @raise_on_one
    def get_win_y_pos(self, handle: int) -> int:
        return self._autoit.WinGetPosY(handle)

    def set_win_position(self, handle: int, x: int, y: int) -> None:
        return self._autoit.WinMove(handle, "", x, y)

    @raise_on_one
    def get_win_height(self, handle: int) -> int:
        return self._autoit.WinGetPosHeight(handle)

    @raise_on_one
    def get_win_width(self, handle: int) -> int:
        return self._autoit.WinGetPosWidth(handle)

    def set_win_dimensions(self, handle: int, width: int, height: int) -> None:
        curr_x, curr_y = self.get_win_x_pos(handle), self.get_win_y_pos(handle)
        return self._autoit.WinMove(handle, "", curr_x, curr_y, width, height)

    def close_window(self, handle: int):
        self._autoit.WinClose(handle)

    def get_process_id(self, handle: int) -> int:
        return int(self._autoit.WinGetProcess(handle))

    def set_all_windows_minimized(self) -> None:
        self._autoit.WinMimimizeAll()

    def set_hidden(self, handle: int) -> None:
        self._autoit.WinSetState(handle, "", self._autoit.SW_HIDE)

    def set_shown(self, handle: int) -> None:
        self._autoit.WinSetState(handle, "", self._autoit.SW_SHOW)

    def get_class_name(self, handle: int) -> str:
        return ctype.get_class_name(handle)

    get_class_name.autoit = False

    def set_enabled(self, handle: int) -> None:
        return ctype.set_enabled(handle)

    set_enabled.autoit = False

    def set_disabled(self, handle: int) -> None:
        return ctype.set_disabled(handle)

    set_disabled.autoit = False


WinListReturnType = Tuple[Tuple[str, ...], Tuple[int, ...]]


def iter_winlist(data: WinListReturnType) -> Iterator[Tuple[str, int]]:
    handles: Tuple[int, ...] = tuple(int(f"0x{x}", 16) for x in data[1][1:])
    titles: Tuple[str, ...] = tuple(data[0][1:])
    assert len(handles) == len(titles)

    return zip(titles, handles)


class AutoItMouseController(MouseControllerBase):
    def __init__(self, controller):
        self._controller = controller

    def move_to(self, x: int, y: int) -> None:
        self._controller.MouseMove(x, y, 0)

    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: Optional[MouseButton] = None,
        click_count: int = 1,
    ) -> None:
        if button is None or button == MouseButton.primary:
            click_button = "primary"
        elif button == MouseButton.secondary:
            click_button = "secondary"
        elif button == MouseButton.middle:
            click_button = "middle"
        else:
            raise ValueError(
                f"{button} is not a valid value for the `button` parameter."
            )

        if x is None and y is None:
            x, y = self.x_pos, self.y_pos
        if not all((x, y)):
            raise ValueError(f"Must provide x AND y values.")
        self._controller.MouseClick(click_button, x, y, click_count, 0)

    @property
    def x_pos(self) -> int:
        return self._controller.MouseGetPosX()

    @property
    def y_pos(self) -> int:
        return self._controller.MouseGetPosY()


if __name__ == "__main__":
    WinAccess().boop(1)
