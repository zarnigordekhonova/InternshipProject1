from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import get_user_model

from apps.users.forms import UserRegisterForm

CustomUser = get_user_model()


class UserRegisterView(CreateView):
    model = CustomUser
    form_class = UserRegisterForm
    template_name = "users/register.html"
    success_url = reverse_lazy("users:login")