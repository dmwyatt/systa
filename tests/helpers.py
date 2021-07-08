from contextlib import contextmanager
from typing import Any, ContextManager, MutableSequence


@contextmanager
def temp_append(l: MutableSequence[Any], elem: Any) -> ContextManager:
    l.append(elem)
    yield
    l.pop(-1)
