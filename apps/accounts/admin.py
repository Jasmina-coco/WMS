from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Company, Role, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "company", "is_manager", "role", "is_active"]
    list_filter = ["company", "is_manager", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("WMS", {"fields": ("company", "is_manager", "role", "warehouses", "phone")}),
    )


admin.site.register(Company)
admin.site.register(Role)
