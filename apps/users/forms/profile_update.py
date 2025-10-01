from django import forms
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name")