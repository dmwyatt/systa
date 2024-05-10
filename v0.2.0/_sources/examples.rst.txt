Examples
--------

Tiled Monitor
^^^^^^^^^^^^^

Here we change monitor #3 to always tile any window moved onto it.

.. raw:: html

  <video
    draggable="false"
    playsinline=""
    autoplay=""
    loop=""
    class="align-left"
    style="width: 550px; height: 309px;"
  >
    <source type="video/mp4" src="https://i.imgur.com/MHtMxZq.mp4">
  </video>

Things to note in this example:

* The instance of :class:`~systa.backend.monitors.SystaMonitor` that you can get
  from a window.
* The :class:`~systa.types.Rect` instance we get from the monitor and window objects
  are used to calculate overlap area.

.. literalinclude:: ../../src/examples/tiled_monitor.py
