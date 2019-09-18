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
        >>> def do_something_different(prev_fn, something):
        ...     result = getattr(something, '_different')()
        ...     return result or prev_fn()

    3. Specify the path in settings (e.g. in `envs/private.py`):
        >>> DO_SOMETHING_IMPL = 'do_something_different_plugin.do_something.do_something_different'

        You can also chain functions:
        >>> DO_SOMETHING_IMPL = [
        ...     'do_something_different_plugin.do_something.do_something_different',
        ...     'do_something_else_plugin.do_something.do_something_else',
        ... ]
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            prev_fn = functools.partial(f, *args, **kwargs)  # The base method in `edx-platform`.

            override_functions = getattr(settings, override, None)
            if not override_functions:  # Override not specified, call the original implementation.
                return prev_fn()

            if isinstance(override_functions, str):
                override_functions = [override_functions]

            for impl in override_functions:
                module, function = impl.rsplit('.', 1)
                mod = import_module(module)
                func = getattr(mod, function)

                prev_fn = functools.partial(func, prev_fn, *args, **kwargs)
            # Call the last specified function. It can call the previous one, which can call the previous one, etc.
            # (until it reaches the base implementation). It can also return without calling `prev_fn`.
            return prev_fn()
        return wrapper
    return decorator
