from systa.backend.monitors import enumerate_monitors
from systa.events.constants import win_events
from systa.events.decorators import filter_by
from systa.events.types import EventData
from systa.types import Rect
from tests.helpers import temp_append


def test_any_filter_passes(event_data):
    func_ran = False

    @filter_by.any_filter(
        filter_by.require_title("Untitled - Notepad"),
        filter_by.require_title("Microsoft Word"),
        filter_by.require_title("Google Chrome"),
    )
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_any_filter_no_pass(event_data):
    func_ran = False

    @filter_by.any_filter(
        filter_by.require_title("Microsoft Word"),
        filter_by.require_title("Google Chrome"),
    )
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert not func_ran


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
        func_not_run = False

    f(event_data)
    assert func_not_run


def test_require_titled_window(event_data):
    func_ran = False

    @filter_by.require_titled_window
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_exclude_system_windows_excludes_system_window(event_data):
    with temp_append(win_events.WINDOWS_INTERNALS_TITLES, event_data.window.title):
        func_not_run = True

        @filter_by.exclude_system_windows
        def f(data: EventData):
            nonlocal func_not_run
            func_not_run = False

        f(event_data)
        assert func_not_run


def test_exclude_system_windows_passes_non_system_window(event_data):
    func_ran = False

    @filter_by.exclude_system_windows
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_require_title_matches_exact_title(event_data):
    func_ran = False

    @filter_by.require_title("Untitled - Notepad")
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_requires_title_matches_exact_title_no_pass(event_data):
    func_ran = False

    @filter_by.require_title("I R NOT NOTEPAD")
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert not func_ran


def test_requires_title_matches_wildcard_pass(event_data):
    func_ran = False

    @filter_by.require_title("Untitled - *")
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_requires_title_matches_wildcard_no_pass(event_data):
    func_ran = False

    @filter_by.require_title("Untitled - No??tepad")
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert not func_ran


def test_require_size_is_less_than_dimensions(event_data):
    x, y = 500, 500

    func_ran = False

    @filter_by.require_size_is_less_than(x, y)
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.width = 499
    event_data.window.height = 499
    f(event_data)
    assert func_ran


def test_require_size_is_less_than_dimensions_no_pass(event_data):
    x, y = 500, 500

    func_ran = False

    @filter_by.require_size_is_less_than(x, y)
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.width = 501
    event_data.window.height = 501
    f(event_data)
    assert not func_ran


def test_require_size_is_less_than_area(event_data):
    area = 250000
    func_ran = False

    @filter_by.require_size_is_less_than(area=area)
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.width = 499
    event_data.window.height = 499
    f(event_data)
    assert func_ran


def test_require_size_is_less_than_area_no_pass(event_data):
    area = 250000

    func_ran = False

    @filter_by.require_size_is_less_than(area=area)
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.width = 501
    event_data.window.height = 501
    f(event_data)
    assert not func_ran


def test_origin_within_passes(event_data):
    func_ran = False

    @filter_by.require_origin_within(Rect.from_coords(0, 0, 100, 100))
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.position = (0, 0)
    f(event_data)
    assert func_ran


def test_origin_within_fails(event_data):
    func_ran = False

    @filter_by.require_origin_within(Rect.from_coords(0, 0, 100, 100))
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.position = (101, 101)
    f(event_data)
    assert not func_ran


def test_is_maximized_passes(event_data):
    func_ran = False

    @filter_by.is_maximized
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.maximized = True
    f(event_data)
    assert func_ran


def test_is_maximized_no_pass(event_data):
    func_ran = False

    @filter_by.is_maximized
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.maximized = False
    f(event_data)
    assert not func_ran


def test_exclude_window_events(event_data):
    func_ran = False

    @filter_by.exclude_window_events(
        [("Untitled - Notepad", event_data.event_info.event)]
    )
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert not func_ran


def test_require_window(event_data):
    func_ran = False

    @filter_by.require_window
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    f(event_data)
    assert func_ran


def test_require_window_no_pass(event_data):
    func_ran = False

    @filter_by.require_window
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window = None
    f(event_data)
    assert not func_ran


def test_touches_monitors(event_data):
    # TODO: This test isn't great.  What if only one monitor? What if window already
    #  on monitor? What if system has no monitors?
    func_ran = False

    system_monitors = [m.number for m in enumerate_monitors()]

    @filter_by.touches_monitors(system_monitors[0])
    def f(data: EventData):
        nonlocal func_ran
        func_ran = True

    event_data.window.send_to_monitor(system_monitors[0])
    f(event_data)
    assert func_ran
