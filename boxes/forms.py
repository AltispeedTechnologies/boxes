from boxes.models import CustomUser, Package, Carrier, Account, PackageType
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator

class PriceInput(forms.widgets.TextInput):
    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.update({
            "type": "number",
            "step": "0.01",
            "value": "6.00",
            "placeholder": "6.00",
            "class": "form-control"
        })
        super().__init__(attrs)


class PriceField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", PriceInput())
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if value is not None:
            if value < 0:
                raise ValidationError("Price cannot be negative.")
            max_digits, decimal_places = 8, 2
            value_str = "{:.{}f}".format(value, decimal_places)
            int_part, dec_part = value_str.split(".")
            if len(dec_part) > decimal_places:
                raise ValidationError("No more than {} decimal places are allowed.".format(decimal_places))
            if len(int_part) > max_digits - decimal_places:
                raise ValidationError("The total number of digits cannot exceed {}.".format(max_digits))
        return value


class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"]


class PackageForm(forms.ModelForm):
    carrier_id = forms.ChoiceField(label="Carrier", widget=forms.Select(attrs={"class": "form-control select-select2"}))
    account_id = forms.ChoiceField(label="Customer", widget=forms.Select(attrs={"class": "form-control select-select2"}))
    package_type_id = forms.ChoiceField(label="Type", widget=forms.Select(attrs={"class": "form-control select-select2"}))

    def __init__(self, *args, **kwargs):
        super(PackageForm, self).__init__(*args, **kwargs)
        self.fields["carrier_id"].choices = Carrier.objects.values_list("id", "name").distinct()
        self.fields["account_id"].choices = Account.objects.values_list("id", "description").distinct()
        self.fields["package_type_id"].choices = PackageType.objects.values_list("id", "description").distinct()

    class Meta:
        model = Package
        fields = ["tracking_code", "price", "carrier_id", "account_id", "package_type_id", "comments"]
