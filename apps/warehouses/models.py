from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CompanyModel


class Warehouse(CompanyModel):
    name = models.CharField(_("Nomi"), max_length=150)
    address = models.CharField(_("Manzil"), max_length=255, blank=True)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_warehouse_name")
        ]

    def __str__(self):
        return self.name


class Location(CompanyModel):
    """
    Ombordagi aniq joy: zona + yacheyka. Kod ombor ichida noyob,
    masalan "A-01-03" (A zona, 1-qator, 3-yacheyka).
    """

    warehouse = models.ForeignKey(
        Warehouse, verbose_name=_("Ombor"), on_delete=models.CASCADE, related_name="locations"
    )
    zone = models.CharField(_("Zona"), max_length=50, blank=True)
    code = models.CharField(_("Kod"), max_length=50)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["warehouse__name", "code"]
        constraints = [
            models.UniqueConstraint(fields=["warehouse", "code"], name="unique_location_code")
        ]

    def __str__(self):
        return f"{self.warehouse.name} / {self.code}"
