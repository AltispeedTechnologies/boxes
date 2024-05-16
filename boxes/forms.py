from boxes.models import *
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, RegexValidator

class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"]


class CustomUserForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ["prefix", "first_name", "middle_name", "last_name", "suffix", "company", "phone_number", "email", "comments"]

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            model_field = self.Meta.model._meta.get_field(field_name)
            if model_field.null or model_field.blank:
                field.required = False


class PackageForm(forms.ModelForm):
    tracking_code = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    comments = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "cols": 2}),
                               validators=[MaxLengthValidator(256)],
                               required=False)
    account_id = forms.CharField()
    carrier_id = forms.CharField()
    package_type_id = forms.CharField()
    inside = forms.BooleanField(required=False)
    queue_id = forms.CharField(validators=[
                                   MaxLengthValidator(4),
                                   RegexValidator(r'^\d+$')
                               ])

    class Meta:
        model = Package
        fields = ["tracking_code", "price", "account_id", "carrier_id", "package_type_id", "inside", "comments"]
