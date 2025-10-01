from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home") 