from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("start/", views.after_login, name="after_login"),
    path("app/password/", views.PasswordChangeView.as_view(), name="password_change"),
    path("app/roles/", views.RoleListView.as_view(), name="roles"),
    path("app/roles/new/", views.RoleCreateView.as_view(), name="role_create"),
    path("app/roles/<int:pk>/", views.RoleUpdateView.as_view(), name="role_edit"),
    path("app/staff/", views.StaffListView.as_view(), name="staff"),
    path("app/staff/new/", views.StaffCreateView.as_view(), name="staff_create"),
    path("app/staff/<int:pk>/", views.StaffUpdateView.as_view(), name="staff_edit"),
]
