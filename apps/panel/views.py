from django.contrib import messages
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.accounts.models import Company
from apps.core.mixins import PlatformAdminMixin
from apps.landing.models import Lead

from .forms import CompanyCreateForm, CompanyForm, LeadUpdateForm


class DashboardView(PlatformAdminMixin, TemplateView):
    template_name = "panel/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lead_stats"] = Lead.objects.aggregate(
            total=Count("id"),
            new=Count("id", filter=Q(status=Lead.Status.NEW)),
            contacted=Count("id", filter=Q(status=Lead.Status.CONTACTED)),
            agreed=Count("id", filter=Q(status=Lead.Status.AGREED)),
        )
        context["company_stats"] = Company.objects.aggregate(
            total=Count("id"), active=Count("id", filter=Q(is_active=True))
        )
        context["latest_leads"] = Lead.objects.all()[:5]
        return context


class LeadListView(PlatformAdminMixin, ListView):
    model = Lead
    template_name = "panel/lead_list.html"
    context_object_name = "leads"
    paginate_by = 30

    def get_queryset(self):
        qs = Lead.objects.all()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(company_name__icontains=search)
                | Q(name__icontains=search)
                | Q(phone__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Lead.Status.choices
        return context


class LeadDetailView(PlatformAdminMixin, UpdateView):
    model = Lead
    form_class = LeadUpdateForm
    template_name = "panel/lead_detail.html"
    context_object_name = "lead"
    success_url = reverse_lazy("panel:leads")

    def form_valid(self, form):
        messages.success(self.request, _("Ariza yangilandi."))
        return super().form_valid(form)


class CompanyListView(PlatformAdminMixin, ListView):
    model = Company
    template_name = "panel/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        return Company.objects.annotate(users_count=Count("users"))


class CompanyCreateView(PlatformAdminMixin, CreateView):
    model = Company
    form_class = CompanyCreateForm
    template_name = "panel/company_form.html"
    success_url = reverse_lazy("panel:companies")

    def get_initial(self):
        # Arizadan kelgan bo'lsak, ma'lumotlarni oldindan to'ldirib qo'yamiz
        lead_id = self.request.GET.get("lead")
        lead = Lead.objects.filter(pk=lead_id).first() if lead_id else None
        if lead:
            return {
                "name": lead.company_name,
                "contact_person": lead.name,
                "phone": lead.phone,
            }
        return {}

    def form_valid(self, form):
        messages.success(self.request, _("Kompaniya va menejer akkaunti yaratildi."))
        return super().form_valid(form)


class CompanyUpdateView(PlatformAdminMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "panel/company_form.html"
    success_url = reverse_lazy("panel:companies")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["managers"] = self.object.users.filter(is_manager=True)
        return context
