from django.contrib import admin

from apps.core.admin import ReadOnlyAdmin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(ReadOnlyAdmin):
    list_display = ["name", "company"]
    list_filter = ["company"]


@admin.register(Product)
class ProductAdmin(ReadOnlyAdmin):
    list_display = ["sku", "name", "category", "unit", "min_stock", "company", "is_active"]
    list_filter = ["company", "category", "is_active"]
    search_fields = ["sku", "name", "barcode"]
