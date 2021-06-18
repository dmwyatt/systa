from functools import wraps
from inspect import unwrap

from systa.experimental.decorators import func_ranges


class winevent:
    def __init__(self, ranges_) -> None:
        self.ranges = ranges_

    def __call__(self, func):
        func_ranges[unwrap(func)].append(self.ranges)

        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)

        return wrapper


def restore(func):
    return winevent((69, 69))(func)


def maximize(func):
    return winevent((42, 42))(func)


if __name__ == "__main__":

    @maximize
    @restore
    def my_func():
        print("in my func")

    my_func()
    print(func_ranges)
