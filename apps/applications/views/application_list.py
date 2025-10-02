from django.urls import reverse_lazy
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.applications.models import Application
from apps.applications.choices import ApplicationStatus


class ApplicationListView(LoginRequiredMixin, ListView):
    """List all applications for the current user"""
    model = Application
    template_name = 'applications/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Application.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            'applicationbranch_set__branch',
            'applicationbranch_set__specialties',
            'applicationbranch_set__selected_specialists',
            'applicationbranch_set__selected_equipment'
        ).order_by('-created_at')
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['total_applications'] = self.get_queryset().count()
        
    #     queryset = self.get_queryset()
    #     context['draft_count'] = queryset.filter(status=ApplicationStatus.DRAFT).count()
    #     context['submitted_count'] = queryset.filter(status=ApplicationStatus.SUBMITTED).count()
    #     context['pending_count'] = queryset.filter(status=ApplicationStatus.PENDING).count()
    #     context['approved_count'] = queryset.filter(status=ApplicationStatus.APPROVED).count()
    #     context['rejected_count'] = queryset.filter(status=ApplicationStatus.REJECTED).count()
        
    #     return context
