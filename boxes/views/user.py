import json
import random
import string
from boxes.forms import CustomUserForm
from boxes.models import Account, CustomUser, UserAccount
from django.db import transaction
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
        return JsonResponse({"success": False, "errors": [str(e)]})

# Generate a unique username
def generate_username():
    while True:
        username = "".join(random.choices(string.ascii_letters + string.digits + "@._+-", k=8))
        if not CustomUser.objects.filter(username=username).exists():
            return username

@require_http_methods(["POST"])
def create_user(request):
    try:
        data = json.loads(request.body)
        data["username"] = generate_username()
        
        with transaction.atomic():
            form = CustomUserForm(data)

            if form.is_valid():
                user = form.save()
                new_account_name = " ".join(
                    data.get(field, "") for field in ["prefix", "first_name", "middle_name", "last_name", "suffix"] if data.get(field)
                ).strip()

                account = Account(user=user, name=new_account_name, balance=0.00, billable=True)
                account.save()
                account.ensure_primary_alias()

                UserAccount.objects.create(user=user, account=account)

                return JsonResponse({"success": True, "account_id": account.id, "account_name": new_account_name})
            else:
                return JsonResponse({"success": False, "form_errors": form.errors})
    except Exception as e:
        return JsonResponse({"success": False, "errors": [str(e)]})
