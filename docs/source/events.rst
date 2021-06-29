Events
======

With the event-driven API, the user's code can respond to events on the
system. For example, when a window appears, code to resize it can run
automatically.

Listening
---------

Each user function *requires* registration with a function from the
:mod:`~systa.events.decorators.listen_to` module to listen to a range of events called
`WinEvents <https://docs.microsoft.com/en-us/windows/win32/winauto/winevents-infrastructure>`_
. We call the user's function with a single argument providing an :class:`~systa.events
.types.EventData` dataclass containing information about the event and the window. The
function can then do *stuff* with the data we provide it.

.. testsetup:: basic-listen-to

  import time
  import threading
  import random
  from systa.windows import Window

  def move_notepad():
      # waits a bit to let the main testcode block start up the callback store
      time.sleep(.3)
      # this will make the window fire some events
      np = Window("Untitled - Notepad")
      pos = np.position
      np.position = (0, 0)
      np.position = (250, 250)

  np = threading.Thread(target=move_notepad, daemon=True)
  np.start()

.. _basic-listen-to:

.. testcode:: basic-listen-to

  from systa.events.store import callback_store
  from systa.events.decorators import listen_to
  from systa.events.types import EventData


  @listen_to.any_event # not a good idea, see next example
  def user_function(data: EventData) -> None:
      if data.window and "Notepad" in data.window.title:
          print(f"It's a Notepad event! ({data.event_info.event_name})")

  callback_store.run(.5)


.. testoutput:: basic-listen-to
  :hide:

  It's a Notepad event! (...

Ideally, you won't listen to every event.  There are a LOT of events fired on a modern
Windows system, and it consumes OS resources to call your functions.  Luckily, we can
listen to only the events we care about.

.. testsetup:: basic-choose-events

  import time
  import threading
  import random
  from systa.windows import Window


  def move_notepad():
      # waits a bit to let the main testcode block start up the callback store
      time.sleep(.3)
      # this'll make the window fire some events
      np = Window("Untitled - Notepad")
      pos = np.position
      np.position = (pos.x+10, pos.y+10)

  np = threading.Thread(target=move_notepad, daemon=True)
  np.start()

.. testcode:: basic-choose-events

  from systa.events.store import callback_store
  from systa.events.decorators import listen_to
  from systa.events.types import EventData
  from systa.events.constants import win_events

  # Only listens to location-changed events
  @listen_to.location_change
  def user_function(data: EventData) -> None:
      name = data.event_info.event
      if data.window and "Notepad" in data.window.title:
          print(f"Notepad moved!")

  callback_store.run(.5)


.. testoutput:: basic-choose-events
  :hide:

  Notepad moved!...

.. note:: There are many more ``listen_to`` event decorators you can use in the
  :mod:`~systa.events.decorators.listen_to` module.

Other events
------------

If you know what you're doing you can use the the
:func:`~systa.events.decorators.listen_to.specified_events` decorator to specify the exact
events you want to listen to.

.. code-block:: python

  import requests
  from systa.events.constants import win_events
  from systa.events.decorators import listen_to
  from systa.events.store import callback_store


  @listen_to.specified_events(
      (win_events.EVENT_OBJECT_CONTENTSCROLLED, win_events.EVENT_OBJECT_FOCUS)
  )
  def the_user_func(event_data):
      """POST the window title  every time content is scrolled or an object receives focus."""
      requests.post("http://myservice/events", data={"window": event_data.window.title})


  callback_store.run()

.. warning:: ``listen_to`` decorators should always be specified *before* ``filter_by``
  decorators.

Filtering
---------

Listening to specific events will probably still give us too many events.  For example,
you might just be interested in running your code when Notepad is moved to a new
location.  However, Windows will call your code whenever *any* window is moved.

You can handle this with `if` branching in your function as in the above examples
wherein we check if the window title has the word "Notepad".

Or, you can get fancy and use some decorators from
:mod:`~systa.events.decorators.filter_by`:

Ignore events that aren't for a specific window
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. testsetup:: filter-by-basic

  import time
  import threading
  import random
  from systa.windows import Window

  def move_notepad():
      # waits a bit to let the main testcode block start up the callback store
      time.sleep(.3)
      # this'll make the window fire some events
      np = Window("Untitled - Notepad")
      pos = np.position
      np.position = (0, 0)
      np.position = (250, 250)

  np = threading.Thread(target=move_notepad, daemon=True)
  np.start()

.. testcode:: filter-by-basic

  from systa.events.store import callback_store
  from systa.events.decorators import filter_by, listen_to
  from systa.events.types import EventData

  @filter_by.require_title("Untitled - Notepad")
  @listen_to.location_change
  def notepad_moved(data: EventData) -> None:
    print("Notepad moved!")

  callback_store.run(.6)

.. testoutput:: filter-by-basic
  :hide:

  Notepad moved!...

.. note:: The above is equivalent to the :any:`code above <basic-listen-to>`
  where we check if Notepad moved.


Combine as many filters as you want
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. testsetup:: stacked-filters

  import time
  import threading
  import random
  from systa.windows import Window

  def move_notepad():
      # waits a bit to let the main testcode block start up the callback store
      time.sleep(.3)
      # this'll make the window fire some events
      np = Window("Untitled - Notepad")
      pos = np.position
      np.position = (0, 0)
      np.position = (250, 250)

  np = threading.Thread(target=move_notepad, daemon=True)
  np.start()

.. testcode:: stacked-filters

  from systa.events.store import callback_store
  from systa.events.decorators import filter_by, listen_to
  from systa.events.types import EventData
  from systa.types import Point, Rect

  origin = Point(100, 100)
  end = Point(500, 500)

  @filter_by.require_origin_within(Rect(origin, end))
  @filter_by.require_title("Untitled - Notepad")
  @listen_to.location_change
  def notepad_moved(data: EventData) -> None:
    print(f"Notepad moved to {data.window.position}!")

  callback_store.run(.6)

.. testoutput:: stacked-filters
  :hide:

  ...Notepad moved to Point(x=250, y=250)!


.. warning:: If your filters aren't behaving as you expect, remember that
  decorators are evaluated from the bottom up and the first one that doesn't pass
  prevents the rest of them from running. In other words, *all* filters must pass for
  your code to be called. You can use the
  :ref:`any_filter decorator<events:Combine filters with any_filter>` to change this
  behavior.

Combine filters with any_filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Combine filters with the :func:`~systa.events.decorators.filter_by.any_filter` decorator
to make it so that any single filter passing will run your function.

.. testsetup:: any-filter

  from pynput.mouse import Button, Controller
  import time
  import threading
  from systa.windows import Window

  def move_notepad():
    # waits a bit to let the main testcode block start up the callback store
    time.sleep(.1)

    mouse = Controller()

    np = Window("Untitled - Notepad")
    np.bring_mouse_to(50, 8)
    mouse.press(Button.left)
    time.sleep(0.85)

    mouse.position = (250, 250)

    mouse.release(Button.left)

  np = threading.Thread(target=move_notepad, daemon=True)
  np.start()


.. testcode:: any-filter

  from systa.events.decorators import filter_by, listen_to
  from systa.events.store import callback_store
  from systa.events.types import EventData

  @filter_by.any_filter(
      filter_by.require_title("*Notepad"),
      filter_by.require_size_is_less_than(200, 200),
  )
  @listen_to.move_or_sizing_ended
  def some_func(event_data: EventData):
      print('Notepad resized or small window moved.')

  callback_store.run(1.6)

.. testoutput:: any-filter
  :hide:

  Notepad resized or small window moved.

lol, decorators
---------------

If you have a lot of filtering or events to capture, your code can get pretty ugly and
hard to reason about as the decorators stack up.  Decorators only aid readability to a
point, then they can begin to hurt readability.

Some potential solutions follow.

When you have just a few events to listen to
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you have a lot of filtering, but just one or a few events you can move the
filtering into your own code.

.. testcode:: a-few-listeners

  from systa.events.decorators import listen_to
  from systa.events.types import EventData

  @listen_to.capture_mouse
  @listen_to.location_change
  def my_func(data: EventData):
    if not data.window:
      return

    if "Chrome" in data.window.title:
      # do stuff in here
      pass
    elif data.window.active and data.window.classname == "MozillaWindowClass":
      # do something else here
      pass
    # do whatever you want here
