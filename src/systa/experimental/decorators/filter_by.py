import abc
from functools import wraps
from inspect import unwrap

from systa.experimental.decorators import func_stack


class EventTesterBase:
    """By subclassing this your event tests get registered"""

    @abc.abstractmethod
    def event_test(self, event_data):
        ...

    def __call__(self, func):
        @wraps(func)
        def wrapper(data):
            if data is None or not self.event_test(data):
                return None
            return func(data)

        # Capture the callable, including all decorators
        func_stack[unwrap(func)] = wrapper

        return wrapper


def has_lol(func):
    class _has_lol(EventTesterBase):
        def event_test(self, event_data):
            return "lol" in event_data

    return _has_lol()(func)


def has_hmm(func):
    class _has_hmm(EventTesterBase):
        def event_test(self, event_data):
            return "hmm" in event_data

    return _has_hmm()(func)


def is_text(text):
    def decorator(func):
        class _is_text(EventTesterBase):
            def event_test(self, event_data):
                return event_data == text

        return _is_text()(func)

    return decorator


def is_text2(text):
    def decorator(func):
        def wrapper(data):
            return data == text

        return wrapper

    return decorator
