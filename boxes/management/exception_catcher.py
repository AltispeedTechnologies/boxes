import decimal
import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from functools import wraps


def exception_catcher():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Call the decorated function
                result = func(*args, **kwargs)
                # If the function returns None, assume success
                if result is None:
                    return JsonResponse({"success": True})
                return result
            except json.JSONDecodeError as jde:
                return JsonResponse({"success": False, "errors": ["Invalid JSON"]})
            except (ValueError, TypeError, KeyError, decimal.InvalidOperation):
                return JsonResponse({"success": False, "errors": ["Invalid input"]})
            except ObjectDoesNotExist:
                return JsonResponse({"success": False, "errors": ["Requested object not found"]})
            except Exception as e:
                return JsonResponse({"success": False, "errors": [str(e)]})
        return wrapper
    return decorator
