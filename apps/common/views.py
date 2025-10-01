from django.shortcuts import render
from django.views.generic import TemplateView
from apps.applications.models import Application


class GetToHomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            applications = Application.objects.filter(user=user)
            if applications.exists():
                context['applications'] = applications
            else:
                context['no_applications'] = "Sizda hali arizalar mavjud emas."
        else:
            context['no_access'] = "Bu sahifaga kirish uchun login qilishingiz kerak."

        return context
