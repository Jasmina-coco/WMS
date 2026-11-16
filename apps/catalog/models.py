from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CompanyModel
from apps.core.storage import CompanyUploadPath


class Category(CompanyModel):
    name = models.CharField(_("Nomi"), max_length=150)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="unique_category_name")
        ]

    def __str__(self):
        return self.name


class Product(CompanyModel):
    class Unit(models.TextChoices):
        PIECE = "pcs", _("dona")
        KG = "kg", _("kg")
        LITER = "l", _("litr")
        METER = "m", _("metr")
        BOX = "box", _("quti")

    sku = models.CharField(_("SKU (artikul)"), max_length=64)
    name = models.CharField(_("Nomi"), max_length=255)
    category = models.ForeignKey(
        Category, verbose_name=_("Kategoriya"), on_delete=models.SET_NULL, null=True, blank=True
    )
    unit = models.CharField(_("O'lchov birligi"), max_length=10, choices=Unit, default=Unit.PIECE)
    # Hozircha qo'lda kiritiladi, skaner keyingi bosqichda ulanadi
    barcode = models.CharField(_("Shtrix-kod"), max_length=64, blank=True, db_index=True)
    min_stock = models.DecimalField(_("Minimal qoldiq"), max_digits=12, decimal_places=3, default=0)
    # Rasm S3 da saqlanadi (lokalda — media/ papkada).
    # ImageField o'rniga FileField: ImageField uchun Pillow kutubxonasi kerak bo'lardi,
    # bizga esa faqat fayl turini tekshirish yetarli.
    image = models.FileField(
        _("Rasm"),
        upload_to=CompanyUploadPath("products"),
        blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["company", "sku"], name="unique_sku")]

    def __str__(self):
        return f"{self.sku} — {self.name}"
