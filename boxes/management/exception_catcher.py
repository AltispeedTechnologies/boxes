"""View decorator converting exceptions to JSON error responses."""
import decimal
import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from functools import wraps


def exception_catcher():
    """Decorator factory: catch exceptions and return JSON ``{errors: [...]}``.

    Returns a decorator that wraps view callables. On success with a ``None``
    return value, responds with ``{"success": true}``. On known input errors,
    returns structured JSON error payloads suitable for ``ajax_request``.
    """

    def decorator(func):
        """Attach exception handling to ``func`` and preserve metadata via wraps."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Invoke the view; convert exceptions to JsonResponse errors."""
            try:
                # Call the decorated function
                result = func(*args, **kwargs)
                # If the function returns None, assume success
                if result is None:
                    return JsonResponse({"success": True})
                return result
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "errors": ["Invalid JSON"]})
            except (ValueError, TypeError, KeyError, decimal.InvalidOperation):
                return JsonResponse({"success": False, "errors": ["Invalid input"]})
            except ObjectDoesNotExist:
                return JsonResponse({"success": False, "errors": ["Requested object not found"]})
            except Exception as e:
                return JsonResponse({"success": False, "errors": [str(e)]})
        return wrapper
    return decorator
