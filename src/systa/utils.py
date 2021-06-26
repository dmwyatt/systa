import dataclasses
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

import screeninfo
from boltons.iterutils import is_collection
from boltons.typeutils import make_sentinel
from screeninfo import Monitor

from systa.types import Point, Rect

AnyCallable = Callable[..., Any]
PredicateCallable = Callable[[AnyCallable], bool]

DecoratedClass = TypeVar("DecoratedClass")


dontcheck = make_sentinel("dontcheck", "dontcheck")


def timeit(method):
    """Quick and dirty function timing decorator."""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        op_time = (te - ts) * 1000
        print("%r  %2.2f ms" % (method.__name__, op_time))
        return result

    return timed


def is_int(val):
    return isinstance(val, int)


def is_collection_of_ints(val):
    return is_collection(val) and all(is_int(v) for v in val)


def is_collection_of_collection_of_ints(val):
    return is_collection(val) and all(is_collection_of_ints(v) for v in val)


def get_monitors():
    return [SystaMonitor.from_monitor(m) for m in screeninfo.get_monitors()]


@dataclass
class SystaMonitor(Monitor):
    """Wraps a :class:`screeninfo.Monitor` and add some features we need."""

    @staticmethod
    def from_monitor(monitor: Monitor) -> "SystaMonitor":
        return SystaMonitor(**dataclasses.asdict(monitor))

    @property
    def rectangle(self) -> Rect:
        return Rect(
            origin=Point(x=self.x, y=self.y),
            end=Point(x=self.x + self.width, y=self.y + self.width),
        )

    @property
    def number(self) -> int:
        if match := re.search(r"\d+$", self.name):
            return int(match.group())
        else:
            raise ValueError(f"Cannot find number of monitor: {self.name}")


def wait_for_it(condition: Callable[..., bool], max_wait=5):
    """Waits for up to ``max_wait`` seconds for ``condition`` to be truthy."""
    start = time.time()
    while not condition() and (time.time() - start) <= max_wait:
        time.sleep(0.1)
    return condition()
