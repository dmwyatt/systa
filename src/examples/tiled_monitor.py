"""
This example "sucks" a window to the upper or lower half of monitor number 3 if a
window is moved or resized in such a manner to make it "touch" monitor number 3.
"""
from typing import Final

from systa.events.decorators import filter_by, listen_to
from systa.events.store import callback_store
from systa.events.types import EventData

MONITOR_OF_INTEREST: Final = 3


@filter_by.touches_monitors(MONITOR_OF_INTEREST)
@filter_by.require_titled_window
@listen_to.restore
@listen_to.create
@listen_to.move_or_sizing_ended
def tile_monitor(event_data: EventData):
    # We know we've got a window because most @filter_by decorators don't pass if
    # there is not a window object. (Not all events have an associated window).
    window = event_data.window

    # get the monitor object
    monitor = window.get_monitor(MONITOR_OF_INTEREST)

    if monitor is None:
        # Window was moved off of the monitor too quickly for us to react to.
        return

    # Get amounts window overlaps top half and bottom half of monitor area
    upper_overlap = monitor.work_area.upper_rect.intersection_rect(window.rectangle)
    lower_overlap = monitor.work_area.lower_rect.intersection_rect(window.rectangle)

    # Choose whether to move window to top half or bottom half
    if upper_overlap.area >= lower_overlap.area:
        window.position = monitor.rectangle.upper_rect
    else:
        window.position = monitor.rectangle.lower_rect


if __name__ == "__main__":
    callback_store.run()
