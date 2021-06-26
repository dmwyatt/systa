Systa: Windows Automation for Sentient Entities™
================================================

**Systa** is a Microsoft Windows automation library, built for people who aren't Microsoft
Windows programming gurus.

Basic Usage
-----------

>>> from systa.windows import current_windows
>>> "Untitled - Notepad" in current_windows True
>>> "🍔" in current_windows False
>>> notepad = current_windows["Untitled - Notepad"][0]
>>> notepad.maximized False
>>> notepad.maximized = True # it's now maximized
>>> notepad.maximized True

Events
------
The real power of systa springs from its integration with Windows system hooks.  You can
run code when things happen to windows on the system.

.. code-block:: python

  from systa.events.decorators import listen_to, filter_by
  from systa.events.store import callback_store
  from systa.events.types import EventData

  @filter_by.require_size_is_less_than(200, 200)
  @filter_by.require_title("*Notepad")
  @listen_to.restore
  @listen_to.create
  def a_func_to_do_the_thing(event_data: EventData):
      print(f"Notepad restored or created! ({event_data.window.width}, {event_data.window.height})")

  callback_store.run()

The above code prints a message when:

1. A window is opened ``OR`` a window is restored from a minimized state.
2. ``AND`` the window's title ends with the string ``Notepad``.
3. ``AND`` the window's size is less than 200x200.
