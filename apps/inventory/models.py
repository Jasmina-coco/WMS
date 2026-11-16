from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CompanyModel


class Stock(CompanyModel):
    """
    Joriy qoldiq: qaysi tovardan qaysi joyda qancha bor.

    Bu jadvalni hech kim qo'lda o'zgartirmaydi — faqat services.change_stock()
    orqali, va har bir o'zgarish StockMovement jurnaliga yoziladi.
    """

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock")
    location = models.ForeignKey(
        "warehouses.Location", on_delete=models.PROTECT, related_name="stock"
    )
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "location"], name="unique_stock_row"),
            # Ikkinchi himoya qatlami: kodda xato bo'lsa ham baza manfiy qoldiqni qabul qilmaydi
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name="stock_not_negative"),
        ]


class StockMovement(CompanyModel):
    """
    Harakatlar jurnali. Faqat qo'shiladi, hech qachon o'zgartirilmaydi va
    o'chirilmaydi — shuning uchun istalgan sanadagi qoldiqni va kim nima
    qilganini keyin tiklab olish mumkin.
    """

    class Reason(models.TextChoices):
        RECEIPT = "receipt", _("Kirim")
        SHIPMENT = "shipment", _("Chiqim")
        TRANSFER_OUT = "transfer_out", _("Ko'chirish (chiqdi)")
        TRANSFER_IN = "transfer_in", _("Ko'chirish (keldi)")
        COUNT = "count", _("Inventarizatsiya tuzatishi")

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT)
    location = models.ForeignKey("warehouses.Location", on_delete=models.PROTECT)
    # Musbat — kirdi, manfiy — chiqdi
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    balance_after = models.DecimalField(max_digits=14, decimal_places=3)
    reason = models.CharField(max_length=20, choices=Reason)
    # Qaysi hujjat sabab bo'lgani — matn ko'rinishida ("KR-000012"), havola uchun
    document_number = models.CharField(max_length=30, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["company", "created_at"])]
