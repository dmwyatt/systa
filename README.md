systa: SYSTem Automation
========================
An attempt to make a GUI automation tool for Windows that takes
advantage of all the Python features it can for its API, and is as fast
as is possible.

 **Warning**: this is under heavy development. Check
the issues page for insight into what is getting worked on, thought
about, and experimented on.

Examples
--------
Following is some examples of where we're at on API development right
now.

### Closing a window
```pycon
>>> from systa import CurrentWindows, SYSTA_BACKEND_ENV

# we can get backend from the environment so I'm just doing that here
# so we don't have to type it every time we instantiate a
# backend-requiring class.
>>> import os
>>> os.environ.set(SYSTA_BACKEND_ENV, 'autoit')

# Ok, so here we go!
>>> current_windows = CurrentWindows()
>>> notepad = current_windows['Untitled - Notepad']

# Note how we got a list.  After all, we might
# have multiple matching windows.

# CurrentWindows always returns a list.
>>> notepad
[Window(handle=1643340, backend="autoit", title="Untitled - Notepad")]

>>> notepad[0].close()
>>> notepad[0].exists
False
```

### Oops, window doesn't exist!
```pycon
>>> notepad = current_windows['Oops, spelled incorrectly!']
...
 KeyError: 'No windows found with title: Oops, spelled incorrectly!'
```

### Get window by substring of title
```pycon
>>> from systa import TitleSubStrSearch as substr
>>> current_windows[substr('Notepad')]
[Window(handle=1643340, backend="autoit", title="Untitled - Notepad")]
```

### Get window by regex on title
```pycon
>>> from systa import RegexTitleSearch as re_title
>>> current_windows[re_title('.*[Nn]ote.*')]
[Window(handle=1643340, backend="autoit", title="Untitled - Notepad")]
```

### Exists check
```pycon
>>> 'Untitled - Notepad` in current_windows
True
>>> '🍔' in current_windows
False
```

### Hey do you really act like a dict?
```pycon
>>> current_windows.get('🍔')
None
```
