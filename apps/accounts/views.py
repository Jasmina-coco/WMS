from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.mixins import CompanyScopedMixin
from apps.core.permissions import PERMISSION_GROUPS

from .forms import LoginForm, RoleForm, StaffForm
from .models import Role, User


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@login_required
def after_login(request):
    """Kirgandan keyin: platforma admini panelga, kompaniya xodimi WMS ga."""
    if request.user.is_superuser:
        return redirect("panel:dashboard")
    return redirect("reports:dashboard")


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("reports:dashboard")

    def form_valid(self, form):
        messages.success(self.request, _("Parol o'zgartirildi."))
        return super().form_valid(form)


# --- Rollar ---


class RoleListView(CompanyScopedMixin, ListView):
    model = Role
    permission = "staff.manage"
    template_name = "accounts/role_list.html"


class RoleFormMixin(CompanyScopedMixin):
    model = Role
    form_class = RoleForm
    permission = "staff.manage"
    template_name = "accounts/role_form.html"
    success_url = reverse_lazy("accounts:roles")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        # Checkboxlarni modul bo'yicha guruhlab chiqarish uchun
        context["groups"] = PERMISSION_GROUPS
        if form.is_bound:
            context["selected"] = form.data.getlist("permissions")
        else:
            context["selected"] = self.object.permissions if self.object else []
        return context


class RoleCreateView(RoleFormMixin, CreateView):
    pass


class RoleUpdateView(RoleFormMixin, UpdateView):
    pass


# --- Xodimlar ---


class StaffQuerysetMixin(CompanyScopedMixin):
    model = User
    permission = "staff.manage"

    def get_queryset(self):
        # Menejerning o'zini ro'yxatdan tahrirlab bo'lmaydi — u admin tomonidan boshqariladi
        return (
            User.objects.filter(company=self.request.company, is_manager=False)
            .select_related("role")
            .prefetch_related("warehouses")
        )


class StaffListView(StaffQuerysetMixin, ListView):
    template_name = "accounts/staff_list.html"
    context_object_name = "staff"


class StaffFormMixin(StaffQuerysetMixin):
    form_class = StaffForm
    template_name = "accounts/staff_form.html"
    success_url = reverse_lazy("accounts:staff")

    def form_valid(self, form):
        messages.success(self.request, _("Saqlandi."))
        return super().form_valid(form)


class StaffCreateView(StaffFormMixin, CreateView):
    pass


class StaffUpdateView(StaffFormMixin, UpdateView):
    pass
