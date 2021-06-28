Systa: A :class:`~systa.windows.Window` for `windows <https://en.wikipedia.org/wiki/Window_(computing)>`_ on `Windows <https://en.wikipedia.org/wiki/Microsoft_Windows>`_.
==========================================================================================================================================================

**Systa** is a Microsoft Windows automation library, built for people who aren't Microsoft
Windows programming gurus.

**Basic Usage**

>>> from systa.windows import current_windows
>>> "Untitled - Notepad" in current_windows
True
>>> "🍔" in current_windows
False
>>> notepad = current_windows["Untitled - Notepad"][0]
>>> notepad.maximized
False
>>> notepad.maximized = True # it's now maximized
>>> notepad.maximized
True

For more guidance see :doc:`finding_windows` and :doc:`manipulating_windows`.

---------------------------------
Behold, the power of the WinEvent
---------------------------------

Often you'll want to do something to a window when something else happens.
One solution to this is to just run a tight loop querying all the open windows
every X seconds.  Instead of this, why don't we have Windows itself tell us when things
happen and then execute our code doing whatever is we want?

.. testsetup:: behold

  import time
  import threading
  from systa.windows import Window

  def smallify_notepad():
    time.sleep(.3)
    np = Window("Untitled - Notepad")
    orig_width = np.width
    orig_height = np.height
    orig_pos = np.position
    np.width = 190
    np.height = 190
    np.position = (0,0)
    np.minimized = True
    np.minimized = False
    np.position = orig_pos
    np.width = orig_width
    np.height = orig_height

  np = threading.Thread(target=smallify_notepad, daemon=True)
  np.start()


.. testcode:: behold

    from systa.events.decorators import listen_to, filter_by
    from systa.events.store import callback_store
    from systa.events.types import EventData

    @filter_by.require_size_is_less_than(200, 200)
    @filter_by.require_title("*Notepad")
    @listen_to.restore
    @listen_to.create
    def a_func_to_do_the_thing(event_data: EventData):
        print(f"Notepad restored or created! ({event_data.window.width}, {event_data.window.height})")

    callback_store.run(.6)

.. testoutput:: behold
  :hide:

  ...Notepad restored or created! (190, 190)...

In this example, any time a window is created *or* restored from the minimized state,
Windows runs our code.  Our code includes the ``@filter_by`` decorators that only permit
``a_func_to_do_the_thing`` to run if the window's title ends with "Notepad" and has a
size of less than 200x200.

If those criteria are met, then we resize the window to 120x400.

See more at :doc:`events`.

------
Guides
------
* :doc:`finding_windows`
* :doc:`manipulating_windows`
* :doc:`events`




Indices and tables
==================

* :ref:`genindex`

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   finding_windows
   manipulating_windows
   events
   api
