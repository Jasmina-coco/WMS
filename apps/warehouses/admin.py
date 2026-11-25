from django.contrib import admin

from apps.core.admin import ReadOnlyAdmin

from .models import Location, Warehouse


@admin.register(Warehouse)
class WarehouseAdmin(ReadOnlyAdmin):
    list_display = ["name", "company", "address", "is_active"]
    list_filter = ["company", "is_active"]
    search_fields = ["name", "address"]


@admin.register(Location)
class LocationAdmin(ReadOnlyAdmin):
    list_display = ["code", "zone", "warehouse", "company", "is_active"]
    list_filter = ["company", "warehouse"]
    search_fields = ["code"]
