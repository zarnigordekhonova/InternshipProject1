from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")  
    password = forms.CharField(widget=forms.PasswordInput)

   