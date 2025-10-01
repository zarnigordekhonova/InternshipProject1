from django.urls import path
from apps.applications.views import (ApplicationCreateView,
                                    ApplicationUpdateView,
                                    ApplicationListView,
                                    ApplicationDetailView,
                                    get_requirements_for_specialty,
                                    )

app_name = "applications"

urlpatterns = [
    path("application-create/", ApplicationCreateView.as_view(), name="application_create"),
    path("application/<int:pk>/update/", ApplicationUpdateView.as_view(), name="application_update"),
    path("application-list/", ApplicationListView.as_view(), name="application_list"),
    path("application/<int:pk>/detail/", ApplicationDetailView.as_view(), name="application_detail"),
    path('get-requirements/', get_requirements_for_specialty, name='get_requirements'), 
]
