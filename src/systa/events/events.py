from __future__ import annotations

import ctypes.wintypes
import logging
import time
from typing import Optional

import win32event

from systa.backend.access import get_idle_time
from systa.events.types import EventData

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

logger = logging.getLogger(__name__)

STOP_EVENT = win32event.CreateEvent(None, 0, 0, None)
OTHER_EVENT = win32event.CreateEvent(None, 0, 0, None)

WIN_EVENT_PROC_TYPE = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD,
)
"""The ctypes windows function that we send to `user32.SetWinEventHook`."""


class IdleCheck:
    """
    Event that determines if an idle time has passed.

    :param seconds: The number of seconds the system can idle before we consider the
        user idle.
    :param call_count_limit: Once the user is idle, how many checks will return
        ``True``. The event loop will continually check with this class to see if the
        user is idle. If the user is idle at check 1, we will return ``True``. If the
        user is still idle at check 2, what should we return? What about check 3?
        This parameter determines the answer to those questions.  Defaults to 1.


    Model
    -----
    (See :download:`Excel file <docs/idle_time_model.xlsx>`)

    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | System Time (seconds)  | User Input At  | System Idle Duration  | In Idle Period  | Is Begin Idle Period  | Check Count  | Return Value  |
    +========================+================+=======================+=================+=======================+==============+===============+
    | 0                      | -1             | -1                    | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 1                      | 0.12           | 0.88                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 2                      | 0.12           | 1.88                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 3                      | 0.12           | 2.88                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 4                      | 0.12           | 3.88                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 5                      | 0.12           | 4.88                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 6                      | 0.12           | 5.88                  | TRUE            | TRUE                  | 1            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 7                      | 0.12           | 6.88                  | TRUE            | FALSE                 | 2            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 8                      | 0.12           | 7.88                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 9                      | 0.12           | 8.88                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 10                     | 0.12           | 9.88                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 11                     | 10.32          | 0.68                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 12                     | 10.32          | 1.68                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 13                     | 10.32          | 2.68                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 14                     | 10.32          | 3.68                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 15                     | 10.32          | 4.68                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 16                     | 10.32          | 5.68                  | TRUE            | TRUE                  | 1            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 17                     | 10.32          | 6.68                  | TRUE            | FALSE                 | 2            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 18                     | 10.32          | 7.68                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 19                     | 10.32          | 8.68                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 20                     | 10.32          | 9.68                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 21                     | 20.39          | 0.61                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 22                     | 20.39          | 1.61                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 23                     | 20.39          | 2.61                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 24                     | 20.39          | 3.61                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 25                     | 20.39          | 4.61                  | FALSE           | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 26                     | 20.39          | 5.61                  | TRUE            | TRUE                  | 1            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 27                     | 20.39          | 6.61                  | TRUE            | FALSE                 | 2            | TRUE          |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+
    | 28                     | 20.39          | 7.61                  | TRUE            | FALSE                 | 0            | FALSE         |
    +------------------------+----------------+-----------------------+-----------------+-----------------------+--------------+---------------+


    """

    def __init__(self, seconds: float, call_count_limit: int = 1):
        assert call_count_limit > 0, (
            "`call_count_limit` should be an integer above "
            f"zero. Got {call_count_limit}"
        )
        self.seconds = seconds
        self.check_count = 0
        self.check_count_limit = call_count_limit

        self.previous_in_idle_period = False
        self.previous_begin_idle_period = False

    def check(self):
        sys_time = time.time()

        user_input_at = sys_time - get_idle_time()  # save at end
        sys_idle_duration = sys_time - user_input_at
        in_idle_period = sys_idle_duration > self.seconds
        is_begin_idle_period = (
            in_idle_period
            and not self.previous_in_idle_period
            and not self.previous_begin_idle_period
        )

        if in_idle_period and is_begin_idle_period:
            check_count = 1
        elif in_idle_period:
            if self.check_count + 1 <= self.check_count_limit:
                if self.check_count + 1 == 1 and not is_begin_idle_period:
                    check_count = 0
                else:
                    check_count = self.check_count + 1
            else:
                check_count = 0
        else:
            check_count = 0

        # note stuff for next check
        self.previous_begin_idle_period = is_begin_idle_period
        self.previous_in_idle_period = in_idle_period
        self.check_count = check_count

        return check_count > 0

    # noinspection PyMethodMayBeStatic
    def result(self, data: Optional[EventData] = None) -> EventData:
        if data is None:
            data = EventData.get_empty()
        data.context["idle_for"] = get_idle_time()
        return data
