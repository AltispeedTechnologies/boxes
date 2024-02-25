from boxes.models import CustomUser, Package, Carrier, Account, PackageType
from django import forms
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"] 


class PackageForm(forms.ModelForm):
    tracking_code = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    price = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    carrier_id = forms.ChoiceField(label="Carrier", choices=Carrier.objects.values_list("id", "name").distinct(), widget=forms.Select(attrs={"class": "form-control select-select2"}))
    account_id = forms.ChoiceField(label="Customer", choices=Account.objects.values_list("id", "description").distinct(), widget=forms.Select(attrs={"class": "form-control select-select2"}))
    package_type_id = forms.ChoiceField(label="Type", choices=PackageType.objects.values_list("id", "description").distinct(), widget=forms.Select(attrs={"class": "form-control select-select2"}))

    class Meta:
        model = Package
        fields = ["tracking_code", "price", "carrier_id", "account_id", "package_type_id"]
