"""
An experimental zmq-based model where a server process polls for window
creation/destruction and publishes those events over a zmq socket.

I'm not exactly sure what use this is!  I think it might be useful for callbacks that
take too long when using an event-driven system?  We could publish all system events
and listen to them in another process...
"""
import json
import time
from multiprocessing import Process
from pprint import pprint

import zmq

from systa.windows import CurrentWindows

PORT = 31493


# @timeit
def get_all_windows(number):
    """
    Gets all of the windows.

    :param number: how many times to get the windows
    :return: We don't return anything
    """
    cw = CurrentWindows()
    for i in range(number):
        windows = [w for w in cw]


def window_event_server():
    cw = CurrentWindows()
    old = cw.current_handles

    context = zmq.Context()
    socket: zmq.Socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{PORT}")
    while True:
        new = cw.current_handles
        if old.keys() != new.keys():
            changes = {
                "created": [
                    (handle, new[handle].title) for handle in new if handle not in old
                ],
                "destroyed": [
                    (handle, old[handle].title) for handle in old if handle not in new
                ],
            }
            for key, value in changes.items():
                socket.send_multipart(
                    (bytes(key.encode("utf8")), bytes(json.dumps(value).encode("utf8")))
                )

            old = new
        time.sleep(0.01)


def window_event_client():
    context = zmq.Context()
    created_socket: zmq.Socket = context.socket(zmq.SUB)
    created_socket.subscribe("created")
    created_socket.connect(f"tcp://127.0.0.1:{PORT}")

    destroyed_socket: zmq.Socket = context.socket(zmq.SUB)
    destroyed_socket.subscribe("destroyed")
    destroyed_socket.connect(f"tcp://127.0.0.1:{PORT}")

    while True:
        print("receiving...")

        # our server always sends created and destroyed topics
        # together even if one of them is empty
        created = created_socket.recv_multipart()[1]
        destroyed = destroyed_socket.recv_multipart()[1]
        created = json.loads(created.decode("utf8"))
        destroyed = json.loads(destroyed.decode("utf8"))

        print("created")
        pprint(created)
        print("destroyed")
        pprint(destroyed)

        print("*" * 50)


if __name__ == "__main__":
    # Start a client process and a server process.  The server process watches for
    # newly created and destroyed windows and then publishes that info over a zmq
    # PUB socket.  The client process SUBs to that socket and prints the info.

    processes = [
        Process(target=window_event_server),
        Process(target=window_event_client),
    ]

    for process in processes:
        process.daemon = True
        process.start()

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        # TODO: you can't Ctrl-C zmq on Windows
        for process in processes:
            process.terminate()
