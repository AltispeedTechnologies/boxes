"""View decorator converting exceptions to JSON error responses."""
import decimal
import json
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
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
                result = func(*args, **kwargs)
                if result is None:
                    return JsonResponse({"success": True})
                return result
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "errors": ["Invalid JSON"]})
            except ValidationError as e:
                if hasattr(e, "message_dict"):
                    return JsonResponse({"success": False, "form_errors": e.message_dict})
                return JsonResponse({"success": False, "errors": list(e.messages)})
            except (ValueError, TypeError, KeyError, decimal.InvalidOperation):
                return JsonResponse({"success": False, "errors": ["Invalid input"]}, status=400)
            except ObjectDoesNotExist:
                return JsonResponse({"success": False, "errors": ["Requested object not found"]}, status=404)
            except PermissionDenied as e:
                msg = str(e) if str(e) else "Forbidden"
                return JsonResponse({"success": False, "errors": [msg]}, status=403)
            except Exception as e:
                return JsonResponse({"success": False, "errors": [str(e)]}, status=400)
        return wrapper
    return decorator
