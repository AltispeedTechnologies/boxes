from boxes.models import Account
from django.core.paginator import Paginator
from django.db.models import Case, When, Value, CharField, F
from django.db.models.functions import Concat
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def account_mgmt(request):
    accounts = Account.objects.select_related(
        "useraccount__user"
    ).annotate(
        phone_number=F("useraccount__user__phone_number"),
        mobile_number=F("useraccount__user__mobile_number"),
        hr_balance=Case(
            When(balance__gte=0, then=Concat(Value("$"), F("balance"))),
            default=Concat(Value("$("), F("balance") * -1, Value(")")),
            output_field=CharField(),
        )
    ).values(
        "id", "name", "hr_balance", "phone_number", "mobile_number"
    ).order_by("name")

    page_number = request.GET.get("page", 1)
    per_page = request.GET.get("per_page", 10)

    paginator = Paginator(accounts, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, "mgmt/accounts.html", {"page_obj": page_obj})
