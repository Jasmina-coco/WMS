from django.contrib import admin


class ReadOnlyAdmin(admin.ModelAdmin):
    """
    Bazadagi ma'lumotni brauzerda ko'rish uchun — o'zgartirib bo'lmaydi.
    Qoldiq va hujjatlar faqat tizim orqali (tekshiruv va jurnal bilan) o'zgarishi kerak,
    admin orqali to'g'ridan-to'g'ri tahrirlash qoldiqni buzib qo'yishi mumkin.
    """

    list_per_page = 50

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ReadOnlyInline(admin.TabularInline):
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        # Inline formasi tahrirlanmaydigan maydonlarni ham ko'rsata olishi uchun
        return self.fields or []
