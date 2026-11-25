from django.contrib import admin

from apps.core.admin import ReadOnlyAdmin

from .models import Stock, StockMovement


@admin.register(Stock)
class StockAdmin(ReadOnlyAdmin):
    list_display = ["product", "location", "quantity", "company", "updated_at"]
    list_filter = ["company", "location__warehouse"]
    search_fields = ["product__name", "product__sku", "location__code"]
    list_select_related = ["product", "location", "company"]


@admin.register(StockMovement)
class StockMovementAdmin(ReadOnlyAdmin):
    list_display = [
        "created_at",
        "product",
        "location",
        "quantity",
        "balance_after",
        "reason",
        "document_number",
        "created_by",
        "company",
    ]
    list_filter = ["company", "reason"]
    search_fields = ["product__name", "product__sku", "document_number"]
    date_hierarchy = "created_at"
    list_select_related = ["product", "location", "created_by", "company"]
