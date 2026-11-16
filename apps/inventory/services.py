"""
Qoldiqni o'zgartirishning yagona yo'li.

Nega alohida funksiya: kirim, chiqim, ko'chirish va inventarizatsiya —
hammasi oxir-oqibat "shu joyda shu tovar shuncha o'zgardi" degan amal.
Uni bir joyda to'g'ri yozsak, qolgan hamma joy to'g'ri ishlaydi.
"""

from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext as _

from .models import Stock, StockMovement


class StockError(Exception):
    """Qoldiq yetmasa yoki amal noto'g'ri bo'lsa. Xabari foydalanuvchiga ko'rsatiladi."""


def change_stock(*, product, location, delta, reason, user, document_number=""):
    """
    `delta` musbat bo'lsa qoldiq oshadi, manfiy bo'lsa kamayadi.

    select_for_update() qatorni tranzaksiya oxirigacha qulflaydi: ikki omborchi
    bir vaqtda oxirgi 5 donani chiqarmoqchi bo'lsa, ikkinchisi birinchisini kutadi
    va keyin "qoldiq yetarli emas" xatosini oladi. Qulfsiz ikkalasi ham o'tib
    ketib, qoldiq -5 bo'lib qolardi.
    """
    delta = Decimal(delta)
    if delta == 0:
        return None
    if product.company_id != location.company_id:
        raise StockError(_("Tovar va joy turli kompaniyalarga tegishli."))

    with transaction.atomic():
        stock, _created = Stock.objects.select_for_update().get_or_create(
            company_id=product.company_id, product=product, location=location
        )
        new_quantity = stock.quantity + delta
        if new_quantity < 0:
            raise StockError(
                _(
                    "%(product)s: %(location)s da yetarli qoldiq yo'q "
                    "(bor: %(have)s, kerak: %(need)s)"
                )
                % {
                    "product": product.name,
                    "location": location.code,
                    "have": stock.quantity.normalize(),
                    "need": (-delta).normalize(),
                }
            )
        stock.quantity = new_quantity
        stock.save(update_fields=["quantity", "updated_at"])

        return StockMovement.objects.create(
            company_id=product.company_id,
            product=product,
            location=location,
            quantity=delta,
            balance_after=new_quantity,
            reason=reason,
            document_number=document_number,
            created_by=user,
        )


def quantity_at(product, location):
    stock = Stock.objects.filter(product=product, location=location).first()
    return stock.quantity if stock else Decimal("0")
