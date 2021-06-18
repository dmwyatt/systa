Doing Stuff to Windows
======================

Windows in Windows are represented a Window. 💩

Confused yet?

In ``systa`` the various windows on your system are represented and controlled by
instances of the :class:`~systa.windows.Window` class.

Getting a Window
----------------

There's various ways you can get a :class:`~systa.windows.Window` instance.  You can just
:ref:`create <finding_windows:Using the Window object>` one if you know there is going
to be only one matching window on your system.

>>> from systa.windows import Window
>>> Window("Untitled - Notepad")
Window(handle=...)

You also get lists of :class:`~systa.windows.Window` objects back from :data:`~systa
.windows.current_windows` objects as
described in :doc:`finding_windows`.

Manipulating Windows
--------------------

You can do stuff to :class:`~systa.windows.Window` objects.  Where it makes sense you just set
attributes instead of calling methods. For example, you can minimize a window like so:

>>> notepad = Window("Untitled - Notepad")
>>> notepad.minimized
False
>>> notepad.minimized = True
>>> notepad.minimized
True
