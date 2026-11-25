from django.contrib import admin

from apps.core.admin import ReadOnlyAdmin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(ReadOnlyAdmin):
    list_display = ["created_at", "name", "company_name", "phone", "warehouses_count", "status"]
    list_filter = ["status"]
    search_fields = ["name", "company_name", "phone"]
