class SystaError(Exception):
    pass


class MultipleMatchingWindowsError(SystaError):
    pass


class NoMatchingWindowError(SystaError):
    pass


class WindowsMessageLoopError(SystaError):
    pass
