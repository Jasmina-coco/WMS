from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Lead(TimeStampedModel):
    """Landingdan kelgan ariza. Admin qo'ng'iroq qilib, natijani shu yerda belgilaydi."""

    class Status(models.TextChoices):
        NEW = "new", _("Yangi")
        CONTACTED = "contacted", _("Bog'lanildi")
        AGREED = "agreed", _("Rozi bo'ldi")
        REJECTED = "rejected", _("Rad etildi")

    name = models.CharField(_("Ism"), max_length=120)
    company_name = models.CharField(_("Kompaniya"), max_length=200)
    phone = models.CharField(_("Telefon"), max_length=30)
    email = models.EmailField(_("Email"), blank=True)
    warehouses_count = models.PositiveIntegerField(_("Omborlar soni"), null=True, blank=True)
    message = models.TextField(_("Izoh"), blank=True)

    status = models.CharField(_("Holat"), max_length=12, choices=Status, default=Status.NEW)
    admin_note = models.TextField(_("Admin izohi"), blank=True)
    # Spamni cheklash uchun: bitta IP dan soatiga nechta ariza kelganini sanaymiz
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} ({self.phone})"
