"""
View'lar uchun umumiy mixinlar: kirish, ruxsat va kompaniya bo'yicha filtr.

Har bir WMS sahifasi shu uchtasini ishlatadi, shuning uchun tekshiruv
bir joyda yozilgan va hech bir view uni "unutib" qo'ya olmaydi.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class CompanyRequiredMixin(LoginRequiredMixin):
    """Faqat biror kompaniyaga biriktirilgan foydalanuvchilar uchun."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.company is None:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PermissionMixin(CompanyRequiredMixin):
    """
    `permission = "receipts.view"` deb yoziladi.
    Menejerda hamma ruxsat bor, xodimda — faqat roliga berilganlari.
    """

    permission = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.permission and not request.user.has_wms_perm(self.permission):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CompanyScopedMixin(PermissionMixin):
    """
    get_queryset() ni kompaniya bo'yicha filtrlaydi, yangi obyektga
    kompaniyani o'zi qo'yadi. Boshqa kompaniyaning ID si URL ga yozilsa ham
    obyekt topilmaydi va 404 qaytadi.
    """

    model = None

    def get_queryset(self):
        return self.model.objects.for_company(self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["company"] = self.request.company
        return kwargs

    def form_valid(self, form):
        if not form.instance.pk:
            form.instance.company = self.request.company
        return super().form_valid(form)


class PlatformAdminMixin(LoginRequiredMixin):
    """Platforma paneli faqat superuser (loyiha egasi) uchun."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
