Finding Windows
===============

The :const:`systa.windows.current_windows` object represents all the current
windows on the system.  You can index into this object as if it was a dictionary. This
is the recommended way to get a :class:`~systa.windows.Window` instance if you're not
using the :doc:`events API <events>`.

``current_windows`` *always* returns a list since there can be multiple windows
matching your query.

Basic Usage
-----------
>>> from systa.windows import current_windows
>>> current_windows["Untitled - Notepad"]
[Window(handle=..., title="Untitled - Notepad")]

Wildcards
---------
You can use UNIX-style wildcard matching on window titles.

+------------+-----------------------------------+
| Pattern    | Meaning                           |
+============+===================================+
| ``*``      | matches everything                |
+------------+-----------------------------------+
| ``?``      | matches any single character      |
+------------+-----------------------------------+
| ``[seq]``  | matches any character in seq      |
+------------+-----------------------------------+
| ``[!seq]`` | matches any character not in seq  |
+------------+-----------------------------------+

>>> from systa.windows import current_windows
>>> current_windows["Untitled - *"]
[Window(handle=..., title="Untitled - Notepad")]
>>> current_windows["?nti?led - Note[mnop]ad"]
[Window(handle=..., title="Untitled - Notepad")]

Regex Pattern
-------------
>>> from systa.windows import current_windows, regex_search
>>> current_windows[regex_search(r"\*?Untitled - Notepad")]
[Window(handle=..., title="Untitled - Notepad")]

Compiled Regex
--------------
You can also use a compiled regex...

>>> from systa.windows import current_windows
>>> import re
>>> pattern = re.compile(r"\*?Untitled - Notepad")
>>> current_windows[pattern]
[Window(handle=..., title="Untitled - Notepad")]

-----------------------
Using the Window object
-----------------------
If you **know** there is only one window that matches your query, you can directly
construct a :class:`~systa.windows.Window` object with your query to bypass the steps
where you index into :const:`~systa.windows.current_windows` and then index into the
returned list.

You'll get a ``ValueError`` if there is not exactly one window matching your query.

>>> from systa.windows import Window
>>> Window(re.compile(r"\*?Untitled - Notepad"))
Window(handle=...)
