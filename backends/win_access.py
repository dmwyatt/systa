import abc
from enum import Enum, auto
from typing import Iterator, Optional, Tuple


class WinAccessBase(abc.ABC):
    """
    Low level access to windows.

    While "low level" might scare you off, this is a perfectly usable class and might be all you
    want to use.
    """

    @property
    @abc.abstractmethod
    def mouse(self) -> "MouseControllerBase":
        ...

    @abc.abstractmethod
    def get_title(self, handle: int) -> str:
        ...

    @abc.abstractmethod
    def set_title(self, handle: int, title: str) -> None:
        ...

    @abc.abstractmethod
    def get_handle(self, title: str) -> Iterator[int]:
        ...

    @abc.abstractmethod
    def get_titles_and_handles(self) -> Iterator[Tuple[str, int]]:
        ...

    @abc.abstractmethod
    def get_is_active(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def get_exists(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def get_is_visible(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def set_hidden(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def set_shown(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def get_is_enabled(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def set_enabled(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def set_disabled(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def get_is_minimized(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def set_minimized(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def get_is_maximized(self, handle: int) -> bool:
        ...

    @abc.abstractmethod
    def set_maximized(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def restore(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def activate_window(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def close_window(self, handle: int) -> None:
        ...

    @abc.abstractmethod
    def get_win_x_pos(self, handle: int) -> int:
        ...

    @abc.abstractmethod
    def get_win_y_pos(self, handle: int) -> int:
        ...

    @abc.abstractmethod
    def set_win_position(self, handle: int, x: int, y: int) -> None:
        ...

    @abc.abstractmethod
    def get_win_width(self, handle: int) -> int:
        ...

    @abc.abstractmethod
    def get_win_height(self, handle: int) -> int:
        ...

    @abc.abstractmethod
    def set_win_dimensions(self, handle: int, x: int, y: int) -> None:
        ...

    @abc.abstractmethod
    def get_process_id(self, handle: int) -> int:
        ...

    def get_pid(self, handle: int) -> int:
        return self.get_process_id(handle)

    @abc.abstractmethod
    def set_all_windows_minimized(self) -> None:
        ...

    @abc.abstractmethod
    def get_class_name(self, handle: int) -> str:
        ...


class MouseButton(Enum):
    primary = auto()
    secondary = auto()
    middle = auto()


class MouseControllerBase(abc.ABC):
    @abc.abstractmethod
    def move_to(self, x: int, y: int) -> None:
        ...

    @abc.abstractmethod
    def click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: Optional[MouseButton] = None,
        click_count: int = 1,
    ) -> None:
        ...

    @property
    @abc.abstractmethod
    def x_pos(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def y_pos(self) -> int:
        ...
