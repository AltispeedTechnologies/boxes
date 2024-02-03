from boxes.models import CustomUser, Package
from django import forms
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"] 


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = ["tracking_code", "current_state"]

    def __init__(self, user, *args, **kwargs):
        super(PackageForm, self).__init__(*args, **kwargs)
        self.fields["user"] = user.id
        self.fields["current_state"].initial = 0

    def clean_current_state(self):
        # Add any additional validation logic for current_state if needed
        return self.cleaned_data['current_state']

