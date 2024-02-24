from boxes.models import CustomUser, Package, Carrier, Account
from django import forms
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"] 


class PackageForm(forms.ModelForm):
    price = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    carrier_id = forms.ChoiceField(label="Carrier", choices=Carrier.objects.values_list("id", "name").distinct(), widget=forms.Select(attrs={'class': 'form-control'}))
    account_id = forms.ChoiceField(label="Customer", choices=Account.objects.values_list("id", "description").distinct(), widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Package
        fields = ["tracking_code", "price", "carrier_id", "account_id"]

    def clean_current_state(self):
        return self.cleaned_data['current_state']
