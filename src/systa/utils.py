import time
from typing import Any, Callable, TypeVar

from boltons.iterutils import is_collection
from boltons.typeutils import make_sentinel

AnyCallable = Callable[..., Any]
PredicateCallable = Callable[[AnyCallable], bool]

DecoratedClass = TypeVar("DecoratedClass")


dontcheck = make_sentinel("dontcheck", "dontcheck")


def timeit(method):
    """Quick and dirty function timing decorator."""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        op_time = (te - ts) * 1000
        print("%r  %2.2f ms" % (method.__name__, op_time))
        return result

    return timed


def is_int(val):
    return isinstance(val, int)


def is_collection_of_ints(val):
    return is_collection(val) and all(is_int(v) for v in val)


def is_collection_of_collection_of_ints(val):
    return is_collection(val) and all(is_collection_of_ints(v) for v in val)


def wait_for_it(condition: Callable[..., bool], max_wait=5) -> bool:
    """Waits for up to ``max_wait`` seconds for ``condition`` to be truthy.

    :returns: ``True`` if condition, else ``False``
    """
    start = time.time()
    while not condition() and (time.time() - start) <= max_wait:
        time.sleep(0.1)
    return bool(condition())


def composed(*decs):
    """Combine multiple decorators into one.

    .. code-block::

        from systa.utils import composed
        from systa.events import listen_to

        our_listener = composed(listen_to.destroy, listen_to.restore, listen_to.location_change)

        @our_listener
        def our_func(data: EventData):
            ...
    """

    def deco(f):
        for dec in reversed(decs):
            f = dec(f)
        return f

    return deco
