from utils import import_string


def import_backend(backend_name: str):
    return import_string(f'backends.{backend_name}.WinAccess')


def class_path_to_backend_name(class_path: str) -> str:
    return class_path.replace('backends.', '').split('.')[0]
