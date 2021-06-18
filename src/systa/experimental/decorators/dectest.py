import abc
from collections import defaultdict
from functools import wraps
from inspect import unwrap

ranges = defaultdict(list)
func_wrapped = {}


class dec_meta(type, abc.ABC):
    @property
    def decorate(cls):
        return cls()


class winevent:
    def __init__(self, ranges_) -> None:
        self.ranges = ranges_

    def __call__(self, func):
        ranges[func].append(self.ranges)

        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        wrapper._da_name = "winevent"

        return wrapper


class EventTesterBase(metaclass=dec_meta):
    @abc.abstractmethod
    def event_test(self, event_data):
        ...

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.event_test(kwargs["data"]):
                return func(*args, **kwargs)
            else:
                return None

        # Capture the callable, including all decorators
        func_wrapped[unwrap(func)] = wrapper

        return wrapper


class has_lol(EventTesterBase):
    def event_test(self, event_data):
        if "lol" in event_data:
            return True
        return False


class has_hmm(EventTesterBase):
    def event_test(self, event_data):
        if "hmm" in event_data:
            return True
        return False


def hmmph(func):
    return has_hmm()(func)


if __name__ == "__main__":
    print("hi")

    # event_69 = winevent(69)
    # hmm = has_hmm()
    # lol = has_lol()

    @winevent(69)
    @hmmph
    @has_lol.decorate
    def myfunc(data):
        print(data)

    # if __name__ == "__main__":
    # minimized(maximized(titled(myfunc("decorators"))))
    myfunc(data="lolhmm")
    # winevent(69)(has_hmm()(has_lol()(myfunc(data="lolhxmm"))))
