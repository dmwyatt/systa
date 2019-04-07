import csv

import io
import abc
import subprocess
from enum import Enum, auto
from typing import Iterator, Optional, Tuple

from exceptions import SystaError
from utils import import_string


def import_backend(backend_name: str):
    return import_string(f'{backend_name}.WinAccess')


def class_path_to_backend_name(class_path: str) -> str:
    return class_path.split('.')[0]


class WinAccessBase(abc.ABC):
    """
    Low level access to windows.

    While "low level" might scare you off, this is a perfectly usable class and might be all you
    want to use.
    """

    @property
    @abc.abstractmethod
    def mouse(self) -> 'MouseControllerBase': ...

    @abc.abstractmethod
    def get_title(self, handle: int) -> str: ...

    @abc.abstractmethod
    def get_handle(self, title: str) -> Iterator[int]: ...

    @abc.abstractmethod
    def get_titles_and_handles(self) -> Iterator[Tuple[str, int]]: ...

    @abc.abstractmethod
    def get_is_active(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def get_exists(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def get_is_visible(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def get_is_enabled(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def get_is_minimized(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def get_is_maximized(self, handle: int) -> bool: ...

    @abc.abstractmethod
    def activate_window(self, handle: int) -> None: ...

    @abc.abstractmethod
    def close_window(self, handle: int) -> None: ...

    @abc.abstractmethod
    def get_win_x_pos(self, handle: int) -> int: ...

    @abc.abstractmethod
    def get_win_y_pos(self, handle: int) -> int: ...

    @abc.abstractmethod
    def get_win_width(self, handle: int) -> int: ...

    @abc.abstractmethod
    def get_win_height(self, handle: int) -> int: ...

    @abc.abstractmethod
    def get_process_id(self, handle: int) -> int: ...

    def get_pid(self, handle: int):
        return self.get_process_id(handle)


class MouseButton(Enum):
    primary = auto()
    secondary = auto()
    middle = auto()


class MouseControllerBase(abc.ABC):
    @abc.abstractmethod
    def move_to(self, x: int, y: int) -> None: ...

    @abc.abstractmethod
    def click(self, x: Optional[int] = None,
              y: Optional[int] = None,
              button: Optional[MouseButton] = None,
              click_count: int = 1) -> None: ...

    @property
    @abc.abstractmethod
    def x_pos(self) -> int: ...

    @property
    @abc.abstractmethod
    def y_pos(self) -> int: ...
