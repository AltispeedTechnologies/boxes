import json
from boxes.forms import CustomUserForm
from boxes.models import Account, CustomUser, UserAccount
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def update_user(request):
    try:
        data = json.loads(request.body)
        
        responses = {}
        for user_id, user_data in data.items():
            accounts = UserAccount.objects.filter(user=user_id).values_list("account_id", flat=True)
            if len(accounts) == 1:
                new_account_name = ""

                for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"]:
                    new_account_name += user_data[field] + " " if len(user_data[field]) > 0 else ""

                account = Account.objects.filter(pk=accounts[0]).first()
                account.name = new_account_name.strip()
                account.save()
                account.ensure_primary_alias()

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
