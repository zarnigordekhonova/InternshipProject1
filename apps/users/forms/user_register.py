from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "password1", "password2")