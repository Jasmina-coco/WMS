"""
Hisobot so'rovlari. Hammasi bazada hisoblanadi (SUM, COUNT, GROUP BY) —
Python'da sikl bilan sanamaymiz, aks holda katta omborda sahifa sekin ochiladi.
"""

from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from apps.catalog.models import Product
from apps.inventory.models import Stock, StockMovement
from apps.operations.models import Document

ZERO = Value(0, output_field=DecimalField(max_digits=14, decimal_places=3))


def stock_by_location(warehouses, warehouse_id=None):
    qs = (
        Stock.objects.filter(location__warehouse__in=warehouses)
        .exclude(quantity=0)
        .select_related("product", "location__warehouse")
        .order_by("location__warehouse__name", "location__code", "product__name")
    )
    if warehouse_id:
        qs = qs.filter(location__warehouse_id=warehouse_id)
    return qs


def turnover(company, warehouses, date_from, date_to):
    """Davr bo'yicha har bir tovar: qancha kirdi, qancha chiqdi."""
    movements = StockMovement.objects.filter(
        company=company,
        location__warehouse__in=warehouses,
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
    )
    incoming = Q(quantity__gt=0) & ~Q(reason__startswith="transfer")
    outgoing = Q(quantity__lt=0) & ~Q(reason__startswith="transfer")
    return (
        movements.values("product__sku", "product__name", "product__unit")
        .annotate(
            qty_in=Coalesce(Sum("quantity", filter=incoming), ZERO),
            qty_out=Coalesce(Sum("quantity", filter=outgoing), ZERO),
            operations=Count("id"),
        )
        .order_by("product__name")
    )


def low_stock(company, warehouses):
    """Umumiy qoldig'i minimal chegaradan past tovarlar."""
    return (
        Product.objects.for_company(company)
        .filter(is_active=True, min_stock__gt=0)
        .annotate(
            total=Coalesce(
                Sum("stock__quantity", filter=Q(stock__location__warehouse__in=warehouses)),
                ZERO,
            )
        )
        .filter(total__lt=F("min_stock"))
        .order_by("name")
    )


def staff_activity(company, date_from, date_to):
    """Kim nechta hujjatni bajargan — omborchilar ish hajmini ko'rish uchun."""
    return (
        Document.objects.for_company(company)
        .filter(
            status=Document.Status.DONE,
            confirmed_at__date__gte=date_from,
            confirmed_at__date__lte=date_to,
        )
        .values("confirmed_by__username", "confirmed_by__first_name", "confirmed_by__last_name")
        .annotate(
            receipts=Count("id", filter=Q(kind="receipt")),
            shipments=Count("id", filter=Q(kind="shipment")),
            transfers=Count("id", filter=Q(kind="transfer")),
            total=Count("id"),
        )
        .order_by("-total")
    )
