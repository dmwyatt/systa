import abc
import json
import os
import re
import time
from pprint import pprint
from typing import Dict, Iterator, List, Optional, Pattern, Union

import zmq

from exceptions import NoMatchingWindowError, SystaError
from utils import cached_property, class_to_dotted, get_process_name, import_string

SYSTA_BACKEND_ENV = 'SYSTA_BACKEND'


def get_backend(backend: Optional[Union[str, WinAccessBase]] = None
                ) -> WinAccessBase:
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
                             f'{SYSTA_BACKEND_ENV} must be set to the dotted path of the backend '
                             f'to use.')
        else:
            return import_string(env)()


class Window:
    """ The main class for handling windows.

    Each window can be represented by this class.  Note that, just because you have an instance
    of this class does not mean the window still exists!  You can use the `exists` property to
    determine if the window is still around.
    """

    def __init__(self, backend: Union[str, WinAccessBase],
                 handle: int, title: Optional[str] = None) -> None:
        """
        :param backend: An instance of `win_access.WinAccessBase` or a string indicating which
        backend to use (e.g. "autoit")
        :param handle:  The handle to the window.  This is the one source of truth linking this
        object to a real window.
        :param title: If you know the current title at time of creating this object, pass it in
        so we don't do time-consuming queries to get the window title later.
        """
        self.handle = handle
        self._title = title

        self._backend = backend

    def __str__(self):
        return self.title

    def __repr__(self):
        if self._backend_name is None:
            self._backend_name = class_path_to_backend_name(
                    class_to_dotted(self._backend.__class__))
        if self._title is not None:
            title = f'"{self.title}"'
        else:
            title = None
        return f'Window(handle={self.handle}, backend="{self._backend_name}", title={title})'

    @cached_property
    def backend(self) -> WinAccessBase:
        """ A property giving you an instance of the window-handling backend.
        """
        return get_backend(self._backend)

    @property
    def title(self):
        """ The title of the window.

        Note that, unlike most other window attributes, we  cache the title to save
        time-consuming requests for the title.

        Just re-instantiate if you want to see if title has changed:

        >>> old_instance = Window('autoit', 123456)
        >>> new_instance = Window(old_instance.backend, old_instance.handle)

        # Alternatively you could:
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

    @property
    def active(self) -> bool:
        return self.backend.get_is_active(self.handle)

    @property
    def exists(self) -> bool:
        return self.backend.get_exists(self.handle)

    @property
    def visible(self) -> bool:
        return self.backend.get_is_visible(self.handle)

    @property
    def enabled(self) -> bool:
        return self.backend.get_is_enabled(self.handle)

    @property
    def minimized(self) -> bool:
        return self.backend.get_is_minimized(self.handle)

    @property
    def maximized(self) -> bool:
        return self.backend.get_is_maximized(self.handle)

    def activate(self) -> None:
        self.backend.activate_window(self.handle)

    def close(self) -> None:
        self.backend.close_window(self.handle)

    @property
    def x_pos(self) -> int:
        return self.backend.get_win_x_pos(self.handle)

    @property
    def y_pos(self) -> int:
        return self.backend.get_win_y_pos(self.handle)

    @property
    def width(self) -> int:
        return self.backend.get_win_width(self.handle)

    @property
    def height(self) -> int:
        return self.backend.get_win_height(self.handle)

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

    @cached_property
    def process_id(self) -> int:
        return self.backend.get_process_id(self.handle)

    @property
    def pid(self) -> int:
        return self.process_id

    @cached_property
    def process_name(self) -> str:
        return get_process_name(self.pid)


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
        self.backend.minimize_all_windows()

    @cached_property
    def backend(self) -> WinAccessBase:
        return get_backend(self._backend)

    @property
    def current_windows(self) -> Iterator[Window]:
        for title, handle in self.backend.get_titles_and_handles():
            yield Window(self.backend, handle, title=title)

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
            return [Window(self.backend, handle, title=item) for handle in handles]

        elif isinstance(item, int):
            # an int is treated as a window handle
            if not self.backend.get_exists(item):
                raise KeyError(f'Window with this handle does not exist: {item}')

            return [Window(self.backend, item)]

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
    # get_all_windows(100)
    # processes = [
    #     Process(target=window_event_server),
    #     Process(target=window_event_client)
    # ]
    #
    # for process in processes:
    #     process.daemon = True
    #     process.start()
    #
    # try:
    #     for process in processes:
    #         process.join()
    # except KeyboardInterrupt:
    #     for process in processes:
    #         process.terminate()

    print('hi')
