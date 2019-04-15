import abc
import inspect
import json
import os
import re
import time
from pprint import pprint
from typing import Dict, Iterator, List, Optional, Pattern, Tuple, TypeVar, Union

import zmq

from backends import class_path_to_backend_name, import_backend
from backends.win_access import WinAccessBase
from exceptions import MousePositionError, NoMatchingWindowError, SystaError
from utils import (
    cached_property,
    class_to_dotted,
    get_process_name,
    import_string,
    update_parameter_value,
)

SYSTA_BACKEND_ENV = 'SYSTA_BACKEND'

Backend = TypeVar('Backend')


def get_backend(backend: Optional[Union[str, Backend]] = None) -> Backend:
    """ Helper function for getting a backend by name.

    :param backend: The name of the backend to get and return an instance of.
    """

    # We don't need to import anything, this is already an instance of the class...
    if isinstance(backend, WinAccessBase):
        return backend

    # Attempt to import the provided string.
    elif isinstance(backend, str):
        return import_backend(backend)()

    # Attempt to get the backend to use from the environment
    elif backend is None:
        env = os.environ.get(SYSTA_BACKEND_ENV)
        if env is None:
            raise SystaError(f'If no backend is provided, the environment variable '
                             f'{SYSTA_BACKEND_ENV} must be set to the name of the backend to use.')
        else:
            try:
                return import_string(env)()
            except ImportError:
                return import_string(f'backends.{env}.WinAccess')()


class Window:
    """ The main class for handling windows.

    Each window can be represented by this class.  Note that, just because you have an instance
    of this class does not mean the window still exists!  You can use the `exists` property to
    determine if the window is still around.
    """

    def __init__(self, handle: int, backend: Optional[Union[str, WinAccessBase]] = None,
                 title: Optional[str] = None) -> None:
        """
        :param handle:  The handle to the window.  This is the one source of truth linking this
            object to a real window.
        :param backend: One of: an instance of :py:class:`backends.win_access.WinAccessBase`,
            a string indicating which backend to use (e.g. "autoit"). If not provided, we'll get
            it from the environment. See :py:func:`get_backend` for more details on how we get
            the backend.
        :param title: If you know the current title at time of creating this object, pass it in
            so we don't do time-consuming queries to get the window title later.
        """
        self.handle = handle
        self._title = title

        self._backend = backend
        self._backend_name = backend if isinstance(backend, str) else None

    def __str__(self):
        return self.title

    def __repr__(self):
        if self._backend_name is None:
            # We don't generate this unless we need it
            self._backend_name = class_path_to_backend_name(
                    class_to_dotted(self._backend.__class__))
        if self._title is not None:
            title = f'"{self.title}"'
        else:
            # If we don't have a title, lets not do an expensive lookup to get it just for a repr
            title = None
        return f'Window(handle={self.handle}, backend="{self._backend_name}", title={title})'

    @cached_property
    def backend(self) -> WinAccessBase:
        """ The backend for communicating with windows of the window-handling backend.
        """
        return get_backend(self._backend)

    @property
    def title(self):
        """ The title of the window.

        Note that, unlike most other window attributes, we  cache the title to save
        time-consuming requests for the title.

        Just re-instantiate if you want to see if title has changed.

        Check for window title change:

        >>> old_instance = Window(123456)
        >>> new_instance = Window(old_instance.handle, backend=old_instance.backend)

        Or we can do it this way:

        >>> current_windows = CurrentWindows()
        >>> new_instance = current_windows.get(old_instance)

        We do this because during bulk operations like getting all windows, we often also already
        have the title.  When we're doing operations on large collections of this class it's very
        time consuming to constantly be re-retrieving the title, and since the title does not
        often change, and it is commonly used, it seems best to just cache it.
        """
        if self._title is None:
            self._title = self.backend.get_title(self.handle)
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self.backend.set_title(self.handle, value)

    @property
    def active(self) -> bool:
        """ Reports and controls if the window is active.

        If :python:`True`, the window is active and if :python:`False`, the window is not active.

        This property is also a setter.  Setting to :python:`False` deactivates the window by
        activating the desktop "window".  Of course, setting to :python:`True` activates the window.
        """
        return self.backend.get_is_active(self.handle)

    @active.setter
    def active(self, value: bool) -> None:
        if value:
            self.activate()
        else:
            desktop_handle = self.backend.get_handle("Program Manager")
            if len(desktop_handle) != 1:
                raise NoMatchingWindowError('Cannot activate desktop to "deactivate" window.')

            self.backend.activate_window(desktop_handle[0])

    @property
    def exists(self) -> bool:
        """Reports and controls if the window exists.

        There is no real-time correspondence between a :class:`Window` object and a real Windows
        window.  If you want to check if the window still exists, this will tell you.

        Because we're crazy people you can also set this to :python:`False` to close a window.

        Setting to :python:`True` has no effect.
        """
        return self.backend.get_exists(self.handle)

    @exists.setter
    def exists(self, value: bool) -> None:
        if not value:
            self.close()

    @property
    def visible(self) -> bool:
        """Reports and controls if the window is visible.

        If set to :python:`True` sets the window to be visible. If set to :python:`False` sets
        the window to be hidden.

        .. warning:: This concept of visibility does not have to do with the window being hidden
            by other windows. See here_ for more info.

        .. _here: https://docs.microsoft.com/en-us/windows/desktop/winmsg/window-features#window-visibility
        """
        return self.backend.get_is_visible(self.handle)

    @visible.setter
    def visible(self, value: bool) -> None:
        if value:
            self.show()
        else:
            self.hide()

    @property
    def enabled(self) -> bool:
        """Reports and controls if the window is enabled.

        If set to :python:`True`, the user can accept user input. If set to :python:`False` the
        window will not accept user input.
        """
        return self.backend.get_is_enabled(self.handle)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if value:
            self.enable()
        else:
            self.disable()

    @property
    def minimized(self) -> bool:
        """Reports and controls if the window is minimized.

        IF set to :python:`True`, the window is minimized. If set to :python:`False`, the window
        is restored.
        """
        return self.backend.get_is_minimized(self.handle)

    @minimized.setter
    def minimized(self, value: bool) -> None:
        if value:
            self.backend.set_minimized(self.handle)
        else:
            self.backend.restore(self.handle)

    @property
    def maximized(self) -> bool:
        """Reports and controls if the window is maximized.

        IF set to :python:`True`, the window is maximized. If set to :python:`False`, the window
        is restored.
        """
        return self.backend.get_is_maximized(self.handle)

    @maximized.setter
    def maximized(self, value: bool) -> None:
        if value:
            self.backend.set_maximized(self.handle)
        else:
            self.backend.restore(self.handle)

    @property
    def x_pos(self) -> int:
        """Reports and controls the windows origin coordinate X position.

        If set to an integer the window is instantaneously moved on the x axis to that position.
        """
        return self.backend.get_win_x_pos(self.handle)

    @x_pos.setter
    def x_pos(self, value: int) -> None:
        self.backend.set_win_position(self.handle, value, self.y_pos)

    @property
    def y_pos(self) -> int:
        """Reports and controls the windows origin coordinate Y position.

        If set to an integer the window is instantaneously moved on the y axis to that position.
        """

        return self.backend.get_win_y_pos(self.handle)

    @y_pos.setter
    def y_pos(self, value: int) -> None:
        self.backend.set_win_position(self.handle, self.x_pos, value)

    @property
    def position(self) -> Tuple[int, int]:
        """Reports and controls the windows origin coordinate X, Y position.

        If set to a sequence containing two ints, the window is instantaneously moved to those
        coordinates.
        """
        return self.x_pos, self.y_pos

    @position.setter
    def position(self, pos: Tuple[int, int]) -> None:
        self.backend.set_win_position(self.handle, *pos)

    @property
    def width(self) -> int:
        """Reports and controls the windows width in pixels."""
        return self.backend.get_win_width(self.handle)

    @width.setter
    def width(self, width: int) -> None:
        self.backend.set_win_dimensions(self.handle, width, self.height)

    @property
    def height(self) -> int:
        """Reports and controls the window's height in pixels."""
        return self.backend.get_win_height(self.handle)

    @height.setter
    def height(self, height: int) -> None:
        self.backend.set_win_dimensions(self.handle, self.width, height)

    def bring_mouse_to(self, win_x: int = None, win_y: int = None):
        """
        Moves mouse into window area.  Does not activate window.

        :param win_x: Specify the X position for the mouse.  If not provided, centers the mouse
            on the X-axis of the window.
        :param win_y: Specify the Y position for the mouse.  If not provided, centers the mouse
            on the Y-axis of the window.
        """
        if win_x is not None:
            x = self.x_pos + win_x
        else:
            x = int(self.width / 2) + self.x_pos

        if win_y is not None:
            y = self.y_pos + win_y
        else:
            y = int(self.height / 2) + self.y_pos

        self.backend.mouse.move_to(x, y)

    @property
    def mouse_x_pos(self) -> int:
        x_relative = self.backend.mouse.x_pos - self.x_pos
        contained = (x_relative < self.x_pos + self.width) and x_relative > self.x_pos
        if not contained:
            raise MousePositionError('Mouse not located within window coordinates.')
        return x_relative

    @property
    def mouse_y_pos(self) -> int:
        y_relative = self.backend.mouse.y_pos - self.y_pos
        contained = (y_relative < self.y_pos + self.height) and y_relative > self.y_pos
        if not contained:
            raise MousePositionError('Mouse not located within window coordinates.')
        return y_relative

    @cached_property
    def process_id(self) -> int:
        return self.backend.get_process_id(self.handle)

    @property
    def pid(self) -> int:
        return self.process_id

    @cached_property
    def process_name(self) -> str:
        return get_process_name(self.pid)

    # //////////////
    # Control methods
    # ---------------
    # The following methods offer an alternative API that uses callable methods rather than
    # get/set properties.
    # //////////////

    def show(self) -> None:
        self.backend.set_shown(self.handle)

    def hide(self) -> None:
        self.backend.set_hidden(self.handle)

    def activate(self) -> None:
        self.backend.activate_window(self.handle)

    def close(self) -> None:
        self.backend.close_window(self.handle)

    def minimize(self) -> None:
        self.backend.set_minimized(self.handle)

    def enable(self) -> None:
        self.backend.set_enabled(self.handle)

    def disable(self) -> None:
        self.backend.set_disabled(self.handle)


class WindowSearchPredicate(abc.ABC):
    @abc.abstractmethod
    def predicate(self, *args, **kwargs) -> bool: ...

    def __call__(self, window: Window) -> bool:
        return self.predicate(window)


class RegexTitleSearch(WindowSearchPredicate):
    def __init__(self, pattern: Union[Pattern, str]) -> None:
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern)
        elif isinstance(pattern, Pattern):
            self.pattern = pattern
        else:
            raise TypeError("Expected a compiled regex or a string.")

    def predicate(self, window: Window) -> bool:
        return bool(self.pattern.match(window.title))


class TitleSubStrSearch(WindowSearchPredicate):
    """Case sensitive title substring search"""

    def __init__(self, title_substr: str) -> None:
        self.title_substr = title_substr

    def predicate(self, window: Window) -> bool:
        return self.title_substr in window.title


class CaseInsensitiveTitleSearch(WindowSearchPredicate):
    """Case insensitive title substring search."""

    def __init__(self, title_substr: str) -> None:
        self.title_substr = title_substr.casefold()

    def predicate(self, window: Window) -> bool:
        return self.title_substr in window.title.casefold()


class CurrentWindows:
    def __init__(self, backend: Union[str, WinAccessBase] = None):
        self._backend = backend

    def minimize_all(self):
        self.backend.set_all_windows_minimized()

    @cached_property
    def backend(self) -> WinAccessBase:
        return get_backend(self._backend)

    @property
    def current_windows(self) -> Iterator[Window]:
        for title, handle in self.backend.get_titles_and_handles():
            yield Window(handle, backend=self.backend, title=title)

    @property
    def current_handles(self) -> Dict[int, Window]:
        return {x.handle: x for x in self.current_windows}

    @property
    def current_titles(self) -> Dict[str, List[Window]]:
        """
        Can have multiple windows with same title, so for each title we
        return a list of windows.
        """
        by_title = {}
        for window in self.current_windows:
            if window.title in by_title:
                by_title[window.title].append(window)
            else:
                by_title[window.title] = [window]
        return by_title

    GetTypes = Union[Window, str, int, WindowSearchPredicate]

    def __contains__(self, item: GetTypes) -> bool:
        try:
            return bool(self[item])
        except KeyError:
            return False

    def __getitem__(self, item: GetTypes) -> List[Window]:
        if isinstance(item, WindowSearchPredicate):
            return [window for window in self.current_windows if item(window)]

        # We'll just get by Window.handle in the case we pass a window in.
        if isinstance(item, Window):
            item = item.handle

        if isinstance(item, str):
            # a string is treated as exact window title
            try:
                handles = self.backend.get_handle(item)
            except NoMatchingWindowError as e:
                raise KeyError(str(e))
            return [Window(handle, backend=self.backend, title=item) for handle in handles]

        elif isinstance(item, int):
            # an int is treated as a window handle
            if not self.backend.get_exists(item):
                raise KeyError(f'Window with this handle does not exist: {item}')

            return [Window(item, backend=self.backend)]

    def get(self, item: GetTypes,
            default: Optional[GetTypes] = None
            ) -> Optional[List[Window]]:
        try:
            return self[item]
        except KeyError:
            return default

    def __iter__(self):
        return iter(self.current_windows)


def setup():
    import win32com.client
    ai = win32com.client.Dispatch("AutoItX3.Control")
    ai.Opt("WinTitleMatchMode", 2)
    ai.Opt("WinWaitDelay", 20)

    title = "Untitled - Notepad"

    return ai, title


def timeit(method):
    """Quick and dirty function timing decorator."""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed


@timeit
def get_all_windows(number):
    cw = CurrentWindows('autoit')
    for i in range(number):
        windows = [w for w in cw]


def window_event_server():
    cw = CurrentWindows('autoit')
    old = cw.current_handles

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://127.0.0.1:59123')
    while True:
        time.sleep(1)
        new = cw.current_handles
        if old.keys() != new.keys():
            changes = {
                'created': [(handle, new[handle].title) for handle in new if handle not in old],
                'destroyed': [(handle, old[handle].title) for handle in old if handle not in new]
            }
            for key, value in changes.items():
                socket.send_multipart(
                        (bytes(key.encode('utf8')),
                         bytes(json.dumps(value).encode('utf8'))
                         )
                )

            # print('created:', changes['created'])
            # print('destroyed:', changes['destroyed'])
            # print('=' * 30)
            old = new


def window_event_client():
    context = zmq.Context()
    created_socket = context.socket(zmq.SUB)
    created_socket.subscribe('created')
    created_socket.connect('tcp://127.0.0.1:59123')

    destroyed_socket = context.socket(zmq.SUB)
    destroyed_socket.subscribe('destroyed')
    destroyed_socket.connect('tcp://127.0.0.1:59123')

    while True:
        print('receiving...')

        # our server always sends created and destroyed topics
        # together even if one of them is empty
        created = created_socket.recv_multipart()[1]
        destroyed = destroyed_socket.recv_multipart()[1]
        created = json.loads(created.decode('utf8'))
        destroyed = json.loads(destroyed.decode('utf8'))

        print('created')
        pprint(created)
        print('destroyed')
        pprint(destroyed)

        print('*' * 50)


if __name__ == '__main__':
    os.environ[SYSTA_BACKEND_ENV] = 'autoit'


    # get_all_windows(100)
    # processes = [
    #     Process(target=window_event_server),
    #     Process(target=window_event_client)
    # ]
    #
    # for process in processes:
    #     process.daemon = `True`
    #     process.start()
    #
    # try:
    #     for process in processes:
    #         process.join()
    # except KeyboardInterrupt:
    #     for process in processes:
    #         process.terminate()

    windows = CurrentWindows()
    notepad = windows['Untitled - Notepad'][0]
    notepad.bring_mouse_to()
    print(notepad.mouse_x_pos, notepad.mouse_y_pos)

