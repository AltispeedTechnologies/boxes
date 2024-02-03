from boxes.forms import PackageForm
from django.shortcuts import redirect, render
from boxes.models import Address, Package

def all_packages(request):
    packages = Package.objects.all()
    return render(request, "packages/index.html", {"packages": packages})

def create_package(request):
    if request.method == "POST":
        form = PackageForm(request.user, request.POST)
        if form.is_valid():
            # Process the form data and save the new package
            package = form.save(commit=False)
            package.user_id = request.user.id
            package.account_id_id = 1
            package.address_id_id = 1
            package.save()

            return redirect("packages")
    else:
        form = PackageForm(request.user)

    return render(request, "packages/create.html", {"form": form})
