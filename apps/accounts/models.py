from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CompanyModel, TimeStampedModel


class Company(TimeStampedModel):
    """Platformadan foydalanuvchi mijoz-kompaniya. Uni faqat platforma admini yaratadi."""

    name = models.CharField(_("Nomi"), max_length=200)
    phone = models.CharField(_("Telefon"), max_length=30, blank=True)
    contact_person = models.CharField(_("Mas'ul shaxs"), max_length=150, blank=True)
    note = models.TextField(_("Izoh"), blank=True)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Kompaniya")
        verbose_name_plural = _("Kompaniyalar")

    def __str__(self):
        return self.name


class Role(CompanyModel):
    """
    Menejer o'zi yaratadigan rol. Ruxsatlar PostgreSQL massivida saqlanadi:
    ["receipts.view", "receipts.create", ...]. Alohida jadval qilish shart emas —
    ro'yxat kichik va doim butunligicha o'qiladi.
    """

    name = models.CharField(_("Nomi"), max_length=100)
    permissions = ArrayField(models.CharField(max_length=50), default=list, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_role_name_per_company")
        ]

    def __str__(self):
        return self.name


class User(AbstractUser):
    company = models.ForeignKey(
        Company,
        verbose_name=_("Kompaniya"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )
    # Menejer — kompaniya ichidagi bosh foydalanuvchi, unda hamma ruxsat bor
    is_manager = models.BooleanField(_("Menejer"), default=False)
    role = models.ForeignKey(
        Role, verbose_name=_("Rol"), on_delete=models.SET_NULL, null=True, blank=True
    )
    warehouses = models.ManyToManyField(
        "warehouses.Warehouse", verbose_name=_("Omborlar"), blank=True, related_name="staff"
    )
    phone = models.CharField(_("Telefon"), max_length=30, blank=True)

    def has_wms_perm(self, code):
        if not self.is_active or self.company_id is None:
            return False
        if self.is_manager:
            return True
        return bool(self.role and code in self.role.permissions)

    def allowed_warehouses(self):
        """Xodim faqat o'ziga biriktirilgan omborlarni ko'radi, menejer — hammasini."""
        from apps.warehouses.models import Warehouse

        warehouses = Warehouse.objects.for_company(self.company)
        if self.is_manager:
            return warehouses
        return warehouses.filter(pk__in=self.warehouses.values("pk"))

    @property
    def display_name(self):
        return self.get_full_name() or self.username
