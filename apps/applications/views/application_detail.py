from django.views.generic import DetailView
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.applications.models import Application, ApplicationBranch


class ApplicationDetailView(LoginRequiredMixin, DetailView):
    template_name = 'applications/application_detail.html'
    
    def get(self, request, pk):
        application = get_object_or_404(
            Application,
            pk=pk,
            user=request.user
        )
        
        try:
            application_branch = ApplicationBranch.objects.get(application=application)
        except ApplicationBranch.DoesNotExist:
            application_branch = None
        
        context = {
            'application': application,
            'application_branch': application_branch,
        }
        
        return render(request, self.template_name, context)