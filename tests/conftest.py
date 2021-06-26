import subprocess
import threading
import time

import pytest
from pynput.mouse import Controller

from systa.events.store import callback_store
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
