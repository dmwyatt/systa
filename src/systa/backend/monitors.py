import re
from dataclasses import dataclass
from typing import Any, Iterator, Optional

import win32con

from systa.types import Point, Rect


@dataclass
class SystaMonitor:
    """Info about a monitor.

    Lifted and modified from `screeninfo`_.

    .. _screeninfo: https://github.com/rr-/screeninfo/blob/ba870d067f8acf5943b58898c7e3199819092731/screeninfo/common.py#L7
    """

    x: int
    y: int
    width: int
    height: int
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    name: Optional[str] = None

    work_area: Optional[Rect] = None
    """This should be the desktop coordinates *excluding the taskbar*."""

    def __repr__(self) -> str:
        return (
            f"Monitor("
            f"x={self.x}, y={self.y}, "
            f"width={self.width}, height={self.height}, "
            f"width_mm={self.width_mm}, height_mm={self.height_mm}, "
            f"name={self.name!r}"
            f")"
        )

    @property
    def rectangle(self) -> Rect:
        return Rect(
            origin=Point(x=self.x, y=self.y),
            end=Point(x=self.x + self.width, y=self.y + self.height),
        )

    @property
    def number(self) -> int:
        if match := re.search(r"\d+$", self.name):
            return int(match.group())
        else:
            raise ValueError(f"Cannot find number of monitor: {self.name}")


# noinspection PyPep8Naming
def enumerate_monitors() -> Iterator[SystaMonitor]:
    """
    Get all the monitors on the system.

    Slightly modified from screeninfo_ to return work area.
    """
    import ctypes
    import ctypes.wintypes

    MonitorEnumProc = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.wintypes.RECT),
        ctypes.c_double,
    )

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("rcMonitor", ctypes.wintypes.RECT),
            ("rcWork", ctypes.wintypes.RECT),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szDevice", ctypes.wintypes.WCHAR * win32con.CCHDEVICENAME),
        ]

    monitors = []

    def callback(monitor: Any, dc: Any, rect: Any, _: Any) -> int:
        info = MONITORINFOEXW()
        info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            name = info.szDevice
        else:
            name = None

        h_size = ctypes.windll.gdi32.GetDeviceCaps(dc, win32con.HORZSIZE)
        v_size = ctypes.windll.gdi32.GetDeviceCaps(dc, win32con.VERTSIZE)

        rct = rect.contents
        monitors.append(
            SystaMonitor(
                x=rct.left,
                y=rct.top,
                width=rct.right - rct.left,
                height=rct.bottom - rct.top,
                width_mm=h_size,
                height_mm=v_size,
                name=name,
                work_area=Rect(
                    Point(info.rcWork.left, info.rcWork.top),
                    Point(info.rcWork.right, info.rcWork.bottom),
                ),
            )
        )
        return 1

    # Make the process DPI aware so it will detect the actual
    # resolution and not a virtualized resolution reported by
    # Windows when DPI virtualization is in use.
    #
    # benshep 2020-03-31: this gives the correct behaviour on Windows 10 when
    # multiple monitors have different DPIs.
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

    # On Python 3.8.X GetDC randomly fails returning an invalid DC.
    # To workaround this request a number of DCs until a valid DC is returned.
    for retry in range(100):
        # Create a Device Context for the full virtual desktop.
        dc_full = ctypes.windll.user32.GetDC(None)
        if dc_full > 0:
            # Got a valid DC, break.
            break
        ctypes.windll.user32.ReleaseDC(dc_full)
    else:
        # Fallback to device context 0 that is the whole
        # desktop. This allows fetching resolutions
        # but monitor specific device contexts are not
        # passed to the callback which means that physical
        # sizes can't be read.
        dc_full = 0
    # Call EnumDisplayMonitors with the non-NULL DC
    # so that non-NULL DCs are passed onto the callback.
    # We want monitor specific DCs in the callback.
    ctypes.windll.user32.EnumDisplayMonitors(
        dc_full, None, MonitorEnumProc(callback), 0
    )
    ctypes.windll.user32.ReleaseDC(dc_full)

    yield from monitors


def get_monitor(number: int) -> Optional[SystaMonitor]:
    """Helper function to get a specific monitor by its number."""
    for monitor in enumerate_monitors():
        if monitor.number == number:
            return monitor
