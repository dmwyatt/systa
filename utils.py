import csv
import io
import subprocess
from importlib import import_module

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
    return f'{cls.__module__}.{cls.__qualname__}'


def get_process_name(pid: int) -> str:
    result = subprocess.run(['tasklist', '/fo', 'csv', '/fi', f'pid eq {pid}'],
                            capture_output=True,
                            universal_newlines=True)

    if result.stderr and not result.stdout:
        raise SystaError(f'Error capturing process name. ({result.stderr})')

    f = io.StringIO(result.stdout)
    data = list(csv.reader(f, delimiter=',', quoting=csv.QUOTE_ALL))

    if len(data) != 2:
        raise SystaError('Not valid output from tasklist.')

    return data[1][0]
