import ctypes

from backends.win_access import WinAccessBase

user32 = ctypes.windll.user32


def get_class_name(handle: int) -> str:
    print("doingit", handle)
    buffer = ctypes.create_unicode_buffer(100)
    user32.GetClassNameW(handle, buffer, 99)
    return buffer.value


def set_enabled(handle: int) -> None:
    return user32.EnableWindow(handle, 1)


def set_disabled(handle: int) -> None:
    return user32.EnableWindow(handle, 0)


class WinAccess(WinAccessBase):
    def get_class_name(self, handle: int) -> str:
        print("doingit", handle)
        buffer = ctypes.create_unicode_buffer(100)
        user32.GetClassNameW(handle, buffer, 99)
        return buffer.value

    def set_enabled(self, handle: int) -> None:
        return user32.EnableWindow(handle, 1)

    def set_disabled(self, handle: int) -> None:
        return user32.EnableWindow(handle, 0)
