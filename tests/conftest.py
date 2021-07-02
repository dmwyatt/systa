import subprocess
import threading
import time

import pytest
from pynput.mouse import Controller

from systa.events.constants import win_events
from systa.events.store import callback_store
from systa.events.types import CallbackReturn, EventData
from systa.windows import Window


@pytest.fixture
def notepad():
    notepad_process = subprocess.Popen(["notepad.exe"])

    notepad = Window.wait_for_window("Untitled - Notepad")
    yield notepad
    notepad_process.kill()


@pytest.fixture
def mouse():
    mouse = Controller()
    curr_position = mouse.position
    yield Controller()
    mouse.position = curr_position


@pytest.fixture
def notepad_mover(notepad):
    def start():
        def move_notepad():
            # waits a bit to let the main testcode block start up the callback store
            time.sleep(0.3)
            # this will make the window fire some events
            np = Window("Untitled - Notepad")
            pos = np.position
            np.position = (0, 0)
            np.position = (250, 250)

        np = threading.Thread(target=move_notepad, daemon=True)
        np.start()

    return start


@pytest.fixture
def cb_store():
    yield callback_store
    callback_store.clear_store()


@pytest.fixture
def move_np_thread(notepad):
    def move_notepad():
        pos = notepad.position
        notepad.position = (pos.x + 10, pos.y + 10)
        notepad.height = notepad.height + 10
        notepad.width = notepad.width + 10

    return notepad, threading.Thread(target=move_notepad, daemon=True)


@pytest.fixture
def callback_return(notepad):
    return CallbackReturn(
        hook_handle=1234,
        event=win_events.EVENT_SYSTEM_MOVESIZEEND,
        event_name="EVENT_SYSTEM_MOVESIZEEND",
        window_handle=notepad.handle,
        object_id=65551,
        child_id=1234,
        thread=1234,
        time_ms=1234,
    )


@pytest.fixture
def event_data(notepad, callback_return):
    return EventData(window=notepad, event_info=callback_return)
