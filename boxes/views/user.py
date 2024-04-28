import json
from boxes.forms import CustomUserForm
from boxes.models import CustomUser
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def update_user(request):
    try:
        data = json.loads(request.body)
        
        responses = {}
        for user_id, user_data in data.items():
            user = CustomUser.objects.get(id=user_id)
            form = CustomUserForm(user_data, instance=user)
            if form.is_valid():
                form.save()
            else:
                return JsonResponse({"success": False, "form_errors": form.errors})
        
        return JsonResponse({"success": True})
    except Exception as e:
        # Handle exceptions (e.g., parsing errors, database errors)
        return JsonResponse({"success": False, "errors": [str(e)]})
