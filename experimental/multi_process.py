import json
import time
from multiprocessing import Process
from pprint import pprint

import win32com.client
import zmq

from systa import CurrentWindows
from utils import timeit


def setup():
    ai = win32com.client.Dispatch("AutoItX3.Control")
    ai.Opt("WinTitleMatchMode", 2)
    ai.Opt("WinWaitDelay", 20)

    title = "Untitled - Notepad"

    return ai, title


@timeit
def get_all_windows(number):
    cw = CurrentWindows('autoit')
    for i in range(number):
        windows = [w for w in cw]


def window_event_server():
    cw = CurrentWindows('autoit')
    old = cw.current_handles

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind('tcp://127.0.0.1:59123')
    while True:
        time.sleep(1)
        new = cw.current_handles
        if old.keys() != new.keys():
            changes = {
                'created': [(handle, new[handle].title) for handle in new if handle not in old],
                'destroyed': [(handle, old[handle].title) for handle in old if handle not in new]
            }
            for key, value in changes.items():
                socket.send_multipart(
                        (bytes(key.encode('utf8')),
                         bytes(json.dumps(value).encode('utf8'))
                         )
                )

            old = new


def window_event_client():
    context = zmq.Context()
    created_socket = context.socket(zmq.SUB)
    created_socket.subscribe('created')
    created_socket.connect('tcp://127.0.0.1:59123')

    destroyed_socket = context.socket(zmq.SUB)
    destroyed_socket.subscribe('destroyed')
    destroyed_socket.connect('tcp://127.0.0.1:59123')

    while True:
        print('receiving...')

        # our server always sends created and destroyed topics
        # together even if one of them is empty
        created = created_socket.recv_multipart()[1]
        destroyed = destroyed_socket.recv_multipart()[1]
        created = json.loads(created.decode('utf8'))
        destroyed = json.loads(destroyed.decode('utf8'))

        print('created')
        pprint(created)
        print('destroyed')
        pprint(destroyed)

        print('*' * 50)


if __name__ == '__main__':
    get_all_windows(100)
    processes = [
        Process(target=window_event_server),
        Process(target=window_event_client)
    ]

    for process in processes:
        process.daemon = True
        process.start()

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
