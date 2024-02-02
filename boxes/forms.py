from boxes.models import CustomUser
from django import forms
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(UserCreationForm):
    class Meta:
        model=CustomUser
        fields = ["username", "email", "company", "prefix", "first_name", "middle_name", "last_name", "suffix", "password1", "password2"] 
