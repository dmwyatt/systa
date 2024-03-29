import inspect

from pytest_mock import MockerFixture

from systa.events.constants import win_events
from systa.events.decorators import filter_by, listen_to
from systa.events.store import Store, make_func_hookable
from systa.events.types import EventData


def test_can_add_function(cb_store: Store):
    def func(data: EventData):
        pass

    results = cb_store.add_user_func(func, win_events.EVENT_OBJECT_DESTROY)
    assert results == {
        (win_events.EVENT_OBJECT_DESTROY, win_events.EVENT_OBJECT_DESTROY): True
    }


def test_can_add_func_with_singular_event(cb_store: Store):
    def func(data: EventData):
        pass

    results = cb_store.add_user_func(func, win_events.EVENT_OBJECT_DESTROY)
    assert results == {
        (win_events.EVENT_OBJECT_DESTROY, win_events.EVENT_OBJECT_DESTROY): True
    }


def test_can_add_func_with_range(cb_store: Store):
    def func(data: EventData):
        pass

    results = cb_store.add_user_func(
        func, (win_events.EVENT_OBJECT_CREATE, win_events.EVENT_OBJECT_DESTROY)
    )

    assert results == {
        (win_events.EVENT_OBJECT_CREATE, win_events.EVENT_OBJECT_DESTROY): True
    }


def test_can_add_func_with_ranges(cb_store: Store):
    def func(data: EventData):
        pass

    results = cb_store.add_user_func(
        func,
        [
            (win_events.EVENT_OBJECT_CREATE, win_events.EVENT_OBJECT_DESTROY),
            (win_events.EVENT_OBJECT_DRAGENTER, win_events.EVENT_OBJECT_DRAGDROPPED),
        ],
    )

    assert results == {
        (win_events.EVENT_OBJECT_CREATE, win_events.EVENT_OBJECT_DESTROY): True,
        (win_events.EVENT_OBJECT_DRAGENTER, win_events.EVENT_OBJECT_DRAGDROPPED): True,
    }


def test_update_callable(cb_store: Store, move_np_thread):
    # Make our user's callable
    @listen_to.location_change
    def func(data: EventData):
        pass

    # ...and register it
    results = cb_store.add_user_func(func, win_events.EVENT_OBJECT_LOCATIONCHANGE)

    func2_called = False

    # ...ok, going to replace it with this
    def func2(data: EventData):
        nonlocal func2_called
        func2_called = True
        return True

    # ... do the replacement
    cb_store.update_callable(func, func2)

    notepad, notepad_mover = move_np_thread

    notepad_mover.start()
    cb_store.run(0.2)
    assert func2_called


def test_clear_store(cb_store, mocker: MockerFixture):
    def func(data: EventData):
        pass

    hook_unregisterer = mocker.spy(cb_store, "unregister_all_hooks")
    results = cb_store.add_user_func(func, win_events.EVENT_OBJECT_DESTROY)

    # func is registered?
    assert cb_store.is_registered_for(
        func, (win_events.EVENT_OBJECT_DESTROY, win_events.EVENT_OBJECT_DESTROY)
    )

    cb_store.clear_store()

    # clear store unregistered hooks
    assert hook_unregisterer.call_count == 1

    # func is no longer registered
    assert not cb_store.is_registered_for(
        func, (win_events.EVENT_OBJECT_DESTROY, win_events.EVENT_OBJECT_DESTROY)
    )


def test_make_func_hookable_has_correct_signature_for_windows_hook():
    def func(data: EventData):
        ...

    hookable_func = make_func_hookable(func)
    assert inspect.unwrap(hookable_func) == func

    sig = inspect.signature(hookable_func, follow_wrapped=False)

    assert len(sig.parameters) == 7


def test_can_add_and_run_checkable_event(cb_store):
    func_called = False

    IDLE_FOR = 1

    @listen_to.idleness(seconds=IDLE_FOR)
    def func(data: EventData):
        nonlocal func_called
        func_called = True

    # We can run the store for less than IDLE_FOR because of the amount of time it
    # takes to set up tests and run all the other tests. In fact, even if you're
    # running just this single test, the setup and run takes longer than a second on
    # my machine. Might need adjusted for other machines?  Keep as low as possible so
    # that the tests don't take so long to run.
    cb_store.run(0.8)
    assert func_called


def test_can_add_and_run_checkable_event_no_pass(cb_store):
    func_called = False

    IDLE_FOR = 1

    @listen_to.idleness(seconds=IDLE_FOR)
    def func(data: EventData):
        nonlocal func_called
        func_called = True

    cb_store.run(0.2)

    # System not idle long enough so func not called.
    assert not func_called


def test_can_stack_checkable_event_with_passing_filters(cb_store):
    func_called = False

    IDLE_FOR = 1

    @filter_by.sanity(True)
    @filter_by.sanity(True)
    @listen_to.idleness(seconds=IDLE_FOR)
    def func(data: EventData):
        nonlocal func_called
        func_called = True

    # We can run the store for less than IDLE_FOR because of the amount of time it
    # takes to set up tests and run all the other tests. In fact, even if you're
    # running just this single test, the setup and run takes longer than a second on
    # my machine. Might need adjusted for other machines?  Keep as low as possible so
    # that the tests don't take so long to run.
    cb_store.run(0.8)
    assert func_called


def test_can_stack_checkable_event_with_not_passing_filters(cb_store):
    func_called = False

    IDLE_FOR = 0.01

    @filter_by.sanity(False)
    @filter_by.sanity(True)
    @listen_to.idleness(seconds=IDLE_FOR)
    def func(data: EventData):
        nonlocal func_called
        func_called = True

    cb_store.run(0.2)
    assert not func_called
