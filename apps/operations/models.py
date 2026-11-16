from decimal import Decimal

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CompanyModel
from apps.core.storage import CompanyUploadPath


class Document(CompanyModel):
    """
    Kirim, chiqim va ko'chirish — bitta jadvalda, `kind` bilan ajratiladi.
    Uchalasining tuzilishi bir xil (sarlavha + qatorlar), farq faqat
    tasdiqlanganda qoldiq qanday o'zgarishida — bu services.py da.
    """

    class Kind(models.TextChoices):
        RECEIPT = "receipt", _("Kirim")
        SHIPMENT = "shipment", _("Chiqim")
        TRANSFER = "transfer", _("Ko'chirish")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Qoralama")
        PICKING = "picking", _("Terilmoqda")
        DONE = "done", _("Bajarildi")
        CANCELLED = "cancelled", _("Bekor qilingan")

    NUMBER_PREFIX = {"receipt": "KR", "shipment": "CH", "transfer": "KO"}

    kind = models.CharField(max_length=10, choices=Kind)
    number = models.CharField(_("Raqam"), max_length=20, blank=True, db_index=True)
    status = models.CharField(_("Holat"), max_length=10, choices=Status, default=Status.DRAFT)
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", verbose_name=_("Ombor"), on_delete=models.PROTECT, related_name="+"
    )
    # Faqat ko'chirishda: qaysi omborga
    dest_warehouse = models.ForeignKey(
        "warehouses.Warehouse",
        verbose_name=_("Qaysi omborga"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    # Kirimda — yetkazib beruvchi, chiqimda — mijoz
    partner = models.CharField(_("Kontragent"), max_length=200, blank=True)
    note = models.TextField(_("Izoh"), blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["company", "kind", "status"])]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Raqam id dan olinadi — shunda ikki xodim bir vaqtda yaratsa ham takrorlanmaydi
        if not self.number:
            self.number = f"{self.NUMBER_PREFIX[self.kind]}-{self.pk:06d}"
            super().save(update_fields=["number"])

    @property
    def is_editable(self):
        return self.status == self.Status.DRAFT

    @property
    def permission_prefix(self):
        return {"receipt": "receipts", "shipment": "shipments", "transfer": "transfers"}[self.kind]


class DocumentLine(CompanyModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(
        "catalog.Product", verbose_name=_("Tovar"), on_delete=models.PROTECT
    )
    quantity = models.DecimalField(
        _("Miqdor"),
        max_digits=14,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    # Kirimda — qayerga qo'yiladi, chiqim va ko'chirishda — qayerdan olinadi
    location = models.ForeignKey(
        "warehouses.Location", verbose_name=_("Joy"), on_delete=models.PROTECT, related_name="+"
    )
    # Faqat ko'chirishda: qayerga
    to_location = models.ForeignKey(
        "warehouses.Location",
        verbose_name=_("Qaysi joyga"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        ordering = ["location__code", "id"]


class Attachment(CompanyModel):
    """Hujjatga biriktirilgan fayl (nakladnoy, skan). S3 da saqlanadi."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        _("Fayl"),
        upload_to=CompanyUploadPath("documents"),
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "xlsx", "xls", "docx", "csv"])
        ],
    )
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at"]


class StockCount(CompanyModel):
    """Inventarizatsiya: ombordagi haqiqiy miqdorni sanab, tizim bilan solishtirish."""

    class Status(models.TextChoices):
        OPEN = "open", _("Ochiq")
        FINISHED = "finished", _("Yakunlangan")

    warehouse = models.ForeignKey(
        "warehouses.Warehouse", verbose_name=_("Ombor"), on_delete=models.PROTECT
    )
    zone = models.CharField(
        _("Zona"), max_length=50, blank=True, help_text=_("Bo'sh qolsa — butun ombor")
    )
    status = models.CharField(max_length=10, choices=Status, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    finished_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def number(self):
        return f"INV-{self.pk:06d}"


class StockCountLine(CompanyModel):
    count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    location = models.ForeignKey("warehouses.Location", on_delete=models.PROTECT)
    # Sanoq ochilgan paytdagi tizim qoldig'i
    system_quantity = models.DecimalField(max_digits=14, decimal_places=3)
    # Xodim sanagan miqdor; hali sanalmagan bo'lsa — bo'sh
    counted_quantity = models.DecimalField(max_digits=14, decimal_places=3, null=True, blank=True)

    class Meta:
        ordering = ["location__code", "product__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["count", "product", "location"], name="unique_count_line"
            )
        ]

    @property
    def difference(self):
        if self.counted_quantity is None:
            return None
        return self.counted_quantity - self.system_quantity
