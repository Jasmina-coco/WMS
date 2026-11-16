from django.db.models import Q
from django.views.generic import ListView

from apps.core.mixins import PermissionMixin

from .models import Stock, StockMovement


class StockListView(PermissionMixin, ListView):
    permission = "stock.view"
    template_name = "inventory/stock_list.html"
    context_object_name = "rows"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            Stock.objects.filter(location__warehouse__in=self.request.user.allowed_warehouses())
            .exclude(quantity=0)
            .select_related("product", "location__warehouse")
            .order_by("product__name", "location__code")
        )
        warehouse = self.request.GET.get("warehouse")
        if warehouse:
            qs = qs.filter(location__warehouse_id=warehouse)
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(product__name__icontains=search)
                | Q(product__sku__icontains=search)
                | Q(location__code__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["warehouses"] = self.request.user.allowed_warehouses()
        return context


class MovementListView(PermissionMixin, ListView):
    permission = "stock.view"
    template_name = "inventory/movement_list.html"
    context_object_name = "movements"
    paginate_by = 50

    def get_queryset(self):
        qs = StockMovement.objects.filter(
            location__warehouse__in=self.request.user.allowed_warehouses()
        ).select_related("product", "location__warehouse", "created_by")
        reason = self.request.GET.get("reason")
        if reason:
            qs = qs.filter(reason=reason)
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(product__name__icontains=search)
                | Q(product__sku__icontains=search)
                | Q(document_number__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reasons"] = StockMovement.Reason.choices
        return context
