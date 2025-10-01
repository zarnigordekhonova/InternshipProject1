from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView

from apps.users.forms import UserLoginForm


class UserLoginView(LoginView):
    form_class = UserLoginForm
    template_name = "users/login.html"
    success_url = reverse_lazy("home")

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or reverse_lazy("home")