import re
from boxes.forms import PackageForm
from boxes.models import Package, PackageLedger, Carrier, Account, AccountLedger, PACKAGE_STATES
from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_slug
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

PACKAGES_PER_PAGE = 10

def all_packages(request):
    # Only get checked in packages
    packages = _get_packages(current_state = 1)

    # Paginate
    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "packages/index.html", {"search_url": reverse("search_packages"),
                                                   "page_obj": page_obj})

def check_out_packages(request):
    return render(request, "packages/check_out.html", {"search_url": reverse("search_check_out_packages")})

def check_in_packages(request):
    if request.method == "POST":
        try:
            ids = request.POST.getlist("ids[]", [])
            Package.objects.filter(id__in=ids).update(current_state=1)

            account_ledger, package_ledger = [], []
            for pkg in Package.objects.filter(id__in=ids).values("id", "account_id", "price"):
                acct_entry = AccountLedger(
                    account_id = pkg["account_id"],
                    debit = pkg["price"],
                    credit = 0,
                    description = ""
                )

                pkg_entry = PackageLedger(
                    user_id = request.user.id,
                    package_id_id = pkg["id"],
                    state = 1
                )

                account_ledger.append(acct_entry)
                package_ledger.append(pkg_entry)

            AccountLedger.objects.bulk_create(account_ledger)
            PackageLedger.objects.bulk_create(package_ledger)

            return JsonResponse({"success": True})
        except ValidationError as e:
            errors = [str(message) for message in e.messages]
            print(errors)
            return JsonResponse({"success": False, "errors": errors})
        except Exception as e:
            print(e)
            return JsonResponse({"success": False, "errors": [str(e)]})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.carrier_id = form.cleaned_data["carrier_id"]
            package.account_id = form.cleaned_data["account_id"]
            package.package_type_id = form.cleaned_data["package_type_id"]
            package.save()
            return JsonResponse({"success": True, "id": package.id})
        else:
            errors = dict(form.errors.items()) if form.errors else {}
            return JsonResponse({"success": False, "errors": errors})  # Return error response with form errors
    else:
        form = PackageForm()
        return render(request, "packages/create.html", {"form": form})

def search_check_out_packages(request):
    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("packages")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "packages/search_checkout.html", {"page_obj": page_obj,
                                                             "query": request.GET.get("q", ""),
                                                             "filter": request.GET.get("filter", "")})

def search_packages(request):
    try:
        packages = _search_packages_helper(request)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect("packages")

    page_number = request.GET.get("page")
    page_obj = packages.get_page(page_number)

    return render(request, "packages/search.html", {"page_obj": page_obj,
                                                    "query": request.GET.get("q", ""),
                                                    "filter": request.GET.get("filter", "")})

def _get_packages(**kwargs):
    # Organized by size of expected data, manually
    # Revisit this section after we have data to test with scale
    packages = Package.objects.select_related("account", "carrier", "packagetype").values(
        "id",
        "package_type__shortcode",
        "price",
        "carrier__name",
        "account__description",
        "package_type__description",
        "tracking_code",
        "comments",
    ).filter(**kwargs)

    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return paginator

def _search_packages_helper(request):
    query = request.GET.get("q", "").strip()
    filters = request.GET.get("filter", "").strip()

    # Your existing logic for processing the search query and filters
    allowed_filters = ["tracking_code", "customer"]
    if filters not in allowed_filters:
        raise ValueError("Invalid filter value")

    query = re.sub(r"[^\w\s-]", "", query)

    if filters == "tracking_code":
        packages = _get_packages(tracking_code__icontains=query, current_state=1)
    elif filters == "customer":
        # Use regex to search for packages where the account description contains the partial query as a whole word (case-sensitive).
        # - \b represents a word boundary, ensuring that the search term is matched as a whole word.
        # - {} inserts the escaped query term, allowing for partial matches.
        # - \w*? matches any word characters (0 or more) after the partial query.
        # - \b ensures that the match occurs as a whole word.
        packages = _get_packages(account__description__regex=r'\b{}\w*?\b'.format(re.escape(query)), current_state=1)
    
    paginator = Paginator(packages, PACKAGES_PER_PAGE)

    return packages
