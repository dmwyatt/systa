from systa.events.constants import win_events
from systa.events.decorators import filter_by, listen_to
from systa.events.store import callback_store
from systa.events.types import EventData


def printany():
    @filter_by.exclude_window_events(
        [
            ("Chrome Legacy Window", win_events.EVENT_OBJECT_SHOW),
            ("Chrome Legacy Window", win_events.EVENT_SYSTEM_SCROLLINGEND),
            ("Chrome Legacy Window", win_events.EVENT_SYSTEM_SCROLLINGSTART),
        ]
    )
    @filter_by.exclude_untitled
    @filter_by.exclude_system_windows
    @listen_to.any_event
    def print_em(data: EventData):
        if data.raw_cb_args.event == win_events.EVENT_OBJECT_NAMECHANGE:
            return
        if data.window.title == "Chrome Legacy Window":
            if data.raw_cb_args.event in [
                win_events.EVENT_OBJECT_REORDER,
                win_events.EVENT_OBJECT_LOCATIONCHANGE,
                win_events.EVENT_OBJECT_HIDE,
            ]:
                return
        print("print_em---------------")
        print_data(data)
        return


def notepad_time():
    @filter_by.include_only_titled("*Notepad")
    @listen_to.specified_events((win_events.EVENT_MIN, win_events.EVENT_MAX))
    def notepad_size(data: EventData):
        print(f"NOTEPAD TIME!!!!! {data.window.title}")


def something():
    @filter_by.any_filter(
        filter_by.include_titled("*Overflow*"),
        filter_by.include_titled("*Notepad*"),
    )
    @listen_to.minimize
    def any_check(data: EventData):
        print(data.window.title)


def whats_chrome_up_to():
    @filter_by.include_titled("*Chrome*")
    @listen_to.any_event
    def whats_up_chrome(data: EventData):
        print("whats_up_chrome--------")
        print_data(data)


def print_data(data: EventData):
    print(
        f"{data.window.title}: {data.raw_cb_args.event_name} ("
        f"{data.raw_cb_args.event})"
    )


if __name__ == "__main__":
    printany()
    whats_chrome_up_to()
    callback_store.run()
