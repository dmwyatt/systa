(use-cases)=
# Use Cases
Here we speculate on potential APIs.

## The event-driven system

With the event-driven API, the user's code can respond to events on the
system. For example, when a window appears, code to resize it can run
automatically.

Each user function *requires* registration to listen to a range of
`WinEvent`'s. We call the user's function with a single argument
providing an `EventData` dataclass containing information about the
event and the window. The function can then do ***stuff*** with the data
we provide it.

For users functions to work with this library, the function has to be
registered. We provide a set of `listen_to` decorators for the user to
specify which events the function is interested in.

We also provide a set of `filter_by` decorators so that the user can
tell us which windows and under which circumstances the user's function
should be called.

So, if you're using our decorators, you have to, at minimum use one fo
the `listen_to` decorators. You may also find it convenient to use one
of our `filter_by` decorators to limit when your function is called.


## Event decorators

We provide shortcut decorators that automatically listen to the
`WinEvent`'s relevant to the task you want to complete.

:::{tip}  
Remember that python decorators are processed *bottom to top*.  
:::

<!--(header_target)=-->
### Straightforward stack

Basic example of using the decorators.

```python
from systa.events.decorators import listen_to, filter_by
from systa.events.store import callback_store


# *all* `filter_by` decorators must return True for the function to be run
@filter_by.require_size_is_less_than(200, 200)
@filter_by.require_title("*Notepad")
# if *any* of the `listen_to` events fire, the function is called 
# (if there are `filter_by` decorators they too must pass first)
@listen_to.restore
@listen_to.create
def a_func_to_do_the_thing(event_data):
    event_data.window.position = (120, 400)


# Runs the message loop that calls user functions when the events
# they are registered are fired.
callback_store.run()
```

### Specify events

If you want to cut down the stack of decorators, or we don't provide the
decorators for some esoteric event you want to listen to, you can just
specify the events with the `listen_to.events` decorator.

:::{note}  
The other `listen_to` decorators like `restore` or `create` are just
sugar for `listen_to.events` decorators.  
:::

```python
import requests
from systa.events.constants import win_events
from systa.events.decorators import listen_to
from systa.events.store import callback_store


@listen_to.events(
    [win_events.EVENT_OBJECT_CONTENTSCROLLED, win_events.EVENT_OBJECT_FOCUS]
)
def the_user_func(event_data):
    """POST's the window title for every time content is scrolled or an object receives focus."""
    requests.post("http://myservice/events", data={"window": event_data.window.title})


callback_store.run()
```

### Any filter

Putting a stack of `filter_by` decorators on top of your function
requires all of them to pass before your function runs.

If you'd like your function to run if *any* of them pass, use the `any`
helper.

```python
import logging
from systa.events.decorators import filter_by
from systa.events.store import callback_store

logger = logging.getLogger(__name__)


@filter_by.any(filter_by.title_contains, filter_by.require_size_is_less_than(200, 200))
@listen_to.resized
def some_func(event_data):
    logger.info(event_data.window.title)


callback_store.run()
```

### All filter

The following is equivalent to stacking your `filter_by` decorators as
in [](#straightforward-stack).

```python
from systa.events.decorators import filter_by, listen_to
from systa.events.store import callback_store


@filter_by.all(
        [filter_by.require_size_is_less_than(200, 200),
         filter_by.title_contains("Notepad")]
)
@listen_to.restore
@listen_to.create
def a_func_to_do_the_thing(event_data):
    event_data.window.position = (120, 400)


callback_store.run()
```

### Combining `any` and `all`
You can represent more complex filtering logic by using `filter_by.all`
and `filter_by.any` together.

```python
from systa.events.decorators import filter_by, listen_to
from systa.events.store import callback_store


# And then it has to pass all of these filters. 
# (These could also just be stacked instead of using `filter_by.all`)
@filter_by.all([filter_by.is_active, filter_by.on_display(1)])
# First, the window has to pass any of these filters
@filter_by.any(
        [filter_by.require_size_is_less_than(200, 200),
         filter_by.title_contains("Notepad")]
)
@listen_to.restore
@listen_to.create
def a_func_to_do_the_thing(event_data):
    event_data.window.position = (120, 400)


callback_store.run()
```



## lol at decorators
If you've got a lot of filtering to do, it might just be cleaner or
easier to do your filtering in your function...check attributes of
window and then do or not do what you want.

```python
from systa.events.decorators import filter_by, listen_to
from systa.events.store import callback_store
from systa.events.constants import win_events


def my_old_school_function(event_data):
    # Filtering in our function instead of with a decorator
    if "notepad" in event_data.window.title.casefold():
        print(f"The window is: {event_data.window.title}")


# get registration function for move events
register_for_moves = register(
    event_ranges=[
        (
            win_events.EVENT_SYSTEM_MOVESIZESTART,
            win_events.EVENT_SYSTEM_MOVESIZEEND,
        )
    ]
)
# registering like this instead of with `listen_to` decorators
# (yeah this is really a decorator without using the @ python syntax)
register_for_moves(my_old_school_function)

callback_store.run()
```



