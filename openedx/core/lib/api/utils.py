import functools
from importlib import import_module

from django.conf import settings


def pluggable_override(override):
    """
    This decorator allows overriding any function or method by pointing to an alternative implementation
    with `override` param.
    :param override: path to the alternative function

    Usage:

    1. Add this decorator to your original method. `DO_SOMETHING_IMPL` is the variable name in settings that can be
       used for overriding this method.
        >>> @pluggable_override('DO_SOMETHING_IMPL')
        ...     def do_something(self):
        ...         return _something()

    2. Prepare an alternative implementation:
        >>> def do_something_different(something):
        ...     return getattr(something, '_different')()


    3. Specify the path in settings (e.g. in `envs/private.py`):
        >>> DO_SOMETHING_IMPL = 'do_something_different_plugin.do_something.do_something_different'
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            function_string = getattr(settings, override)
            if not function_string:
                return f(*args, **kwargs)

            module, function = function_string.rsplit('.', 1)
            mod = import_module(module)
            func = getattr(mod, function)
            return func(*args, **kwargs)
        return wrapper
    return decorator
