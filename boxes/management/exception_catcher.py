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
                return JsonResponse({"success": False, "errors": "Invalid JSON"}, status=400)
            except (ValueError, TypeError, KeyError, decimal.InvalidOperation):
                return JsonResponse({"success": False, "errors": "Invalid input"}, status=400)
            except ObjectDoesNotExist:
                return JsonResponse({"success": False, "errors": "Requested object not found"}, status=404)
            except Exception as e:
                return JsonResponse({"success": False, "errors": str(e)}, status=500)
        return wrapper
    return decorator
