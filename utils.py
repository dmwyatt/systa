import csv
import inspect
import io
import subprocess
import time
from importlib import import_module
from typing import (Any, Callable, Mapping, Optional, Sequence, TypeVar)

import wrapt
from argupdate.argupdate import Args, Kwargs, iter_args
from boltons.typeutils import make_sentinel

from exceptions import SystaError


class cached_property:
    """
    Decorator that converts a method with a single self argument into a
    property cached on the instance.

    Optional ``name`` argument allows you to make cached properties of other
    methods. (e.g.  url = cached_property(get_absolute_url, name='url') )
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__

    def __get__(self, instance, cls=None):
        """
        Call the function and put the return value in instance.__dict__ so that
        subsequent attribute access on the instance returns the cached value
        instead of calling cached_property.__get__().
        """
        if instance is None:
            return self
        res = instance.__dict__[self.name] = self.func(instance)
        return res


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    # Stolen straight from Django 2.2
    # https://github.com/django/django/blob/2.2/django/utils/module_loading.py#L7-L24

    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
                          ) from err


def class_to_dotted(cls: type) -> str:
    """Takes a class and returns the dotted path that would import it."""
    return f'{cls.__module__}.{cls.__qualname__}'


def get_process_name(pid: int) -> str:
    """Gets the process name for a PID.  Windows-only."""
    result = subprocess.run(['tasklist', '/fo', 'csv', '/fi', f'pid eq {pid}'],
                            capture_output=True,
                            universal_newlines=True)

    if result.stderr and not result.stdout:
        raise SystaError(f'Error capturing process name. ({result.stderr})')

    f = io.StringIO(result.stdout)
    data = list(csv.reader(f, delimiter=',', quoting=csv.QUOTE_ALL))

    if len(data) != 2:
        raise SystaError(f'Not valid output from tasklist:\n{result.stdout}')

    return data[1][0]


AnyCallable = Callable[..., Any]
PredicateCallable = Callable[[AnyCallable], bool]

DecoratedClass = TypeVar('DecoratedClass')


def method_decorator(decorator: Callable[..., AnyCallable],
                     predicates: Sequence[PredicateCallable]
                     ) -> Callable[[DecoratedClass], DecoratedClass]:
    """Takes a decorator and applies it to all methods of a class.

    :param decorator: The decorator we're applying.
    :param predicates: A sequence of functions that take the method we want to decorate and
        return a bool indicating whether we should decorate it or not.  If any return False,
        we skip the method.
    :return: Returns the decorator we want to use on a class.
    """

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if not (instance is None and inspect.isclass(wrapped)):
            raise TypeError('Use `method_decorator` on classes.')
        for name, fn in inspect.getmembers(wrapped, inspect.isfunction):
            if all(predicate(fn) for predicate in predicates):
                setattr(wrapped, name, decorator(fn))
        return wrapped(*args, **kwargs)

    return wrapper


dontcheck = make_sentinel('dontcheck', 'dontcheck')


def has_parameter(parameter_name: str,
                  annotation: Optional[type] = dontcheck
                  ) -> PredicateCallable:
    """Creates a predicate that checks for an arg name in a function signature.

    :param parameter_name: The name of the parameter we want to check for.
    :param annotation: If provided, checks that the annotation matches this.
    """

    def predicate(func: AnyCallable) -> bool:
        sig = inspect.signature(func)
        parameter = sig.parameters.get(parameter_name)
        if not parameter:
            return False

        if annotation is dontcheck:
            return True

        return parameter.annotation == annotation

    return predicate


def exclude_method_name(method_name: str) -> PredicateCallable:
    """Creates a predicate that excludes methods with the provided name."""

    def predicate(func: AnyCallable) -> bool:
        return func.__name__ != method_name

    return predicate


def exclude_method_attribute(attribute: str, value: Any = False) -> PredicateCallable:
    """Creates a predicate that excludes methods with an attribute set to a value"""

    def predicate(func: AnyCallable) -> bool:
        # Return true if has attribute `attribute` with value `value`.
        if not hasattr(func, attribute):
            # does not have the attribute, so we're not skipping it
            return True
        if getattr(func, attribute) == value:
            # it does have the attribute and it equals the value, so skip it
            print('skipping', func.__name__)
            return False
        # it has the attribute, but its not `value`, so don't skip it
        return True

    return predicate


def get_value_by_arg_name(func: AnyCallable,
                          arg_name: str,
                          args: Sequence[Any],
                          kwargs: Mapping[str, Any]
                          ) -> Any:
    """Get the value for a function's argument from the args and kwargs.

    Given the args and kwargs destined for a function, returns the value matching the requested
    name.

    >>> def the_callable(arg1, arg2, arg3=False): ...
    >>> args = ('one', 'two')
    >>> kwargs = {'arg3': 'whoa'}
    >>> get_value_by_arg_name(the_callable, 'arg3', args, kwargs)
    'whoa'
    >>> get_value_by_arg_name(the_callable, 'arg1', args, kwargs)
    'one'
    >>> get_value_by_arg_name(the_callable, 'notanargname', args, kwargs)
    Traceback (most recent call last):
        ...
    ValueError: "notanargname" not found in signature for `the_callable()`.

    :param func: The callable object that the `args` and `kwargs` are destined for.
    :param arg_name: The name of the argument we're interested in getting the value for.
    :param args: The sequence of positional arguments.
    :param kwargs: The mapping of keyword arguments.

    """
    for name, value in iter_args(func, args, kwargs):
        if name == arg_name:
            return value
    raise ValueError(f'"{arg_name}" not found in signature for `{func.__name__}()`.')


ExcCallable = Callable[[
                           AnyCallable,  # The decorated function
                           Any,  # The decorated function's return value
                           Args,  # The arguments for the decorated function
                           Kwargs  # The kwargs for the decorated function
                       ],
                       Exception]
T = TypeVar('T')


def raise_on_return_value(exc: ExcCallable, return_value: T
                          ) -> Callable[[AnyCallable, Any, Args, Kwargs], T]:
    """Decorator that will raise an exception on a function if it returns a specific value.

    :param exc: A callable that returns an exception for us to raise.
    :param return_value: The return value that we will raise on.
    """

    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        result = wrapped(*args, **kwargs)
        if result == return_value:
            # For a decorated instance method, args does not contain `self`.  That's normally ok,
            # because wrapt has already bound the method to the class instance.
            # However, we're not passing the args and kwargs to the instance method.  We're passing
            # it to a function that uses the `inspect` module to investigate the function signature
            # and it requires the self parameter.  So, here we add the instance to the beginning of
            # the args list.
            if instance and not inspect.isclass(instance):
                # only if instance is not None and instance is not a class can we be sure this is an
                # instance method.
                args = [instance] + list(args)

            raise exc(wrapped, result, args, kwargs)
        return result

    return wrapper


def timeit(method):
    """Quick and dirty function timing decorator."""

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed
