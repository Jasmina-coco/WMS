from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("leads/", views.LeadListView.as_view(), name="leads"),
    path("leads/<int:pk>/", views.LeadDetailView.as_view(), name="lead_detail"),
    path("companies/", views.CompanyListView.as_view(), name="companies"),
    path("companies/new/", views.CompanyCreateView.as_view(), name="company_create"),
    path("companies/<int:pk>/", views.CompanyUpdateView.as_view(), name="company_edit"),
]
