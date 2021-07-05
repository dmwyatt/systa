from systa.backend.monitors import enumerate_monitors
from systa.types import Rect


def test_monitors():
    monitor = next(enumerate_monitors())

    assert isinstance(monitor.work_area, Rect)

    assert isinstance(monitor.rectangle, Rect)

    assert isinstance(monitor.number, int)
