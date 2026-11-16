from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.mixins import CompanyScopedMixin

from .forms import LocationForm, WarehouseForm
from .models import Location, Warehouse


class WarehouseListView(CompanyScopedMixin, ListView):
    model = Warehouse
    permission = "warehouses.view"
    template_name = "warehouses/warehouse_list.html"

    def get_queryset(self):
        # Xodim faqat o'ziga biriktirilgan omborlarni ko'radi
        return self.request.user.allowed_warehouses()


class WarehouseFormMixin(CompanyScopedMixin):
    title = _("Ombor")
    model = Warehouse
    form_class = WarehouseForm
    permission = "warehouses.edit"
    template_name = "form_page.html"
    success_url = reverse_lazy("warehouses:list")


class WarehouseCreateView(WarehouseFormMixin, CreateView):
    pass


class WarehouseUpdateView(WarehouseFormMixin, UpdateView):
    pass


class LocationListView(CompanyScopedMixin, ListView):
    model = Location
    permission = "warehouses.view"
    template_name = "warehouses/location_list.html"
    paginate_by = 50

    def get_queryset(self):
        qs = Location.objects.filter(
            warehouse__in=self.request.user.allowed_warehouses()
        ).select_related("warehouse")
        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(code__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warehouses"] = self.request.user.allowed_warehouses()
        return context


class LocationFormMixin(CompanyScopedMixin):
    title = _("Joy (yacheyka)")
    model = Location
    form_class = LocationForm
    permission = "warehouses.edit"
    template_name = "form_page.html"
    success_url = reverse_lazy("warehouses:locations")


class LocationCreateView(LocationFormMixin, CreateView):
    pass


class LocationUpdateView(LocationFormMixin, UpdateView):
    pass
