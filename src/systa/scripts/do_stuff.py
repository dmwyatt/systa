from systa.windows import current_windows


def one():
    from pynput.mouse import Button, Controller
    import time
    import threading
    from systa.windows import Window

    def move_notepad():
        # waits a bit to let the main testcode block start up the callback store
        time.sleep(0.1)

        mouse = Controller()

        np = Window("Untitled - Notepad")
        np.bring_mouse_to(50, 8)
        mouse.press(Button.left)
        time.sleep(0.85)

        mouse.position = (250, 250)

        mouse.release(Button.left)

    np = threading.Thread(target=move_notepad, daemon=True)
    np.start()

    from systa.events.decorators import filter_by, listen_to
    from systa.events.store import callback_store
    from systa.events.types import EventData

    @filter_by.any_filter(
        filter_by.require_title("*Notepad"),
        filter_by.require_size_is_less_than(200, 200),
    )
    @listen_to.move_or_sizing_ended
    def some_func(event_data: EventData):

        print("Notepad resized or small window moved.")

    callback_store.run(1.6)


def current_str():
    "Untitled - Notepad" in current_windows


if __name__ == "__main__":
    one()
