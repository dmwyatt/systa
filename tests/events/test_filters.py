from systa.events.decorators import filter_by
from systa.events.types import EventData


def test_all_filters_decorator(event_data):
    func_ran = False

    @filter_by.all_filters(
        filter_by.require_title("Untitled - Notepad"),
        filter_by.exclude_system_windows,
        filter_by.require_window,
    )
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_all_filters_decorator_fail(event_data):
    func_not_run = True

    @filter_by.all_filters(
        filter_by.require_title("Untitled - Notepad"),
        filter_by.exclude_system_windows,
        filter_by.require_window,
        filter_by.require_size_is_less_than(5, 5),
    )
    def f(data: EventData):
        nonlocal func_not_run
        func_not_run = True

    f(event_data)
    assert func_not_run
