import os
from typing import Optional, Union, TypeVar

from systa.backends.win_access import WinAccessBase
from systa.exceptions import SystaError
from systa.utils import import_string


def import_backend(backend_name: str):
    return import_string(f"backends.{backend_name}.WinAccess")


def class_path_to_backend_name(class_path: str) -> str:
    return class_path.replace("backends.", "").split(".")[0]


Backend = TypeVar("Backend")


def get_backend(backend: Optional[Union[str, Backend]] = None) -> Backend:
    """ Helper function for getting a backend by name.

    :param backend: The name of the backend to get and return an instance of.
    """

    # We don't need to import anything, this is already an instance of the class...
    if isinstance(backend, WinAccessBase):
        return backend

    # Attempt to import the provided string.
    elif isinstance(backend, str):
        return import_backend(backend)()

    # Attempt to get the backend to use from the environment
    elif backend is None:
        env = os.environ.get(SYSTA_BACKEND_ENV)
        if env is None:
            raise SystaError(
                f"If no backend is provided, the environment variable "
                f"{SYSTA_BACKEND_ENV} must be set to the name of the backend to use."
            )
        else:
            try:
                return import_string(env)()
            except ImportError:
                return import_string(f"backends.{env}.WinAccess")()


SYSTA_BACKEND_ENV = "SYSTA_BACKEND"
