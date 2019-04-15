import csv
import inspect
import io
import subprocess
from importlib import import_module
from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    TypeVar,
)

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

    # TODO: update this to work with decorator generators...aka, decorators that take arguments
    def decorate(cls):
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if all(predicate(fn) for predicate in predicates):
                setattr(cls, name, decorator(fn))
        return cls

    return decorate


dontcheck = make_sentinel('dontcheck', 'dontcheck')


def has_parameter(parameter_name: str,
                  annotation: Optional[type] = dontcheck
                  ) -> Callable[[AnyCallable], bool]:
    """Creates a predicate that checks that a for an arg name in a function signature.

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
