"""
Hujjatlarning biznes logikasi: tasdiqlash, terish, jo'natish, bekor qilish.

View faqat "nima qilish kerak"ni chaqiradi, "qanday" — shu yerda.
Har bir amal bitta tranzaksiyada: biror qatorda qoldiq yetmasa,
oldingi qatorlarda qilingan o'zgarishlar ham bekor bo'ladi.
"""

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.inventory.models import Stock, StockMovement
from apps.inventory.services import StockError, change_stock

from .models import Document, StockCount, StockCountLine

Kind = Document.Kind
Status = Document.Status
Reason = StockMovement.Reason


def _check_lines(document):
    lines = list(document.lines.select_related("product", "location", "to_location"))
    if not lines:
        raise StockError(_("Hujjatda birorta ham qator yo'q."))

    for line in lines:
        if line.location.warehouse_id != document.warehouse_id:
            raise StockError(
                _("%(code)s joyi %(warehouse)s omboriga tegishli emas.")
                % {"code": line.location.code, "warehouse": document.warehouse.name}
            )
        if document.kind == Kind.TRANSFER:
            if line.to_location is None:
                raise StockError(
                    _("Ko'chirishda har bir qator uchun 'qaysi joyga' tanlanishi kerak.")
                )
            if line.to_location.warehouse_id != document.dest_warehouse_id:
                raise StockError(
                    _("%(code)s joyi qabul qiluvchi omborga tegishli emas.")
                    % {"code": line.to_location.code}
                )
            if line.to_location_id == line.location_id:
                raise StockError(_("Bir joydan o'sha joyning o'ziga ko'chirib bo'lmaydi."))
    return lines


def _mark_done(document, user):
    document.status = Status.DONE
    document.confirmed_by = user
    document.confirmed_at = timezone.now()
    document.save(update_fields=["status", "confirmed_by", "confirmed_at", "updated_at"])


@transaction.atomic
def confirm_receipt(document, user):
    if document.kind != Kind.RECEIPT or document.status != Status.DRAFT:
        raise StockError(_("Bu hujjatni tasdiqlab bo'lmaydi."))
    for line in _check_lines(document):
        change_stock(
            product=line.product,
            location=line.location,
            delta=line.quantity,
            reason=Reason.RECEIPT,
            user=user,
            document_number=document.number,
        )
    _mark_done(document, user)


@transaction.atomic
def start_picking(document, user):
    """
    Terish boshlanadi. Bu bosqichda qoldiq hali kamaymaydi, lekin yetarliligini
    oldindan tekshiramiz — omborchi bo'sh yacheykaga borib qolmasin.
    """
    if document.kind != Kind.SHIPMENT or document.status != Status.DRAFT:
        raise StockError(_("Bu hujjat uchun terishni boshlab bo'lmaydi."))
    for line in _check_lines(document):
        stock = Stock.objects.filter(product=line.product, location=line.location).first()
        available = stock.quantity if stock else 0
        if available < line.quantity:
            raise StockError(
                _("%(product)s: %(location)s da faqat %(have)s bor.")
                % {
                    "product": line.product.name,
                    "location": line.location.code,
                    "have": available,
                }
            )
    document.status = Status.PICKING
    document.save(update_fields=["status", "updated_at"])


@transaction.atomic
def ship(document, user):
    if document.kind != Kind.SHIPMENT or document.status != Status.PICKING:
        raise StockError(_("Avval terishni boshlang."))
    for line in _check_lines(document):
        change_stock(
            product=line.product,
            location=line.location,
            delta=-line.quantity,
            reason=Reason.SHIPMENT,
            user=user,
            document_number=document.number,
        )
    _mark_done(document, user)


@transaction.atomic
def confirm_transfer(document, user):
    if document.kind != Kind.TRANSFER or document.status != Status.DRAFT:
        raise StockError(_("Bu hujjatni tasdiqlab bo'lmaydi."))
    for line in _check_lines(document):
        change_stock(
            product=line.product,
            location=line.location,
            delta=-line.quantity,
            reason=Reason.TRANSFER_OUT,
            user=user,
            document_number=document.number,
        )
        change_stock(
            product=line.product,
            location=line.to_location,
            delta=line.quantity,
            reason=Reason.TRANSFER_IN,
            user=user,
            document_number=document.number,
        )
    _mark_done(document, user)


def confirm(document, user):
    """Hujjat turiga qarab kerakli funksiyani chaqiradi."""
    if document.kind == Kind.RECEIPT:
        return confirm_receipt(document, user)
    if document.kind == Kind.TRANSFER:
        return confirm_transfer(document, user)
    if document.status == Status.DRAFT:
        return start_picking(document, user)
    return ship(document, user)


@transaction.atomic
def cancel(document, user):
    # Bajarilgan hujjatni bekor qilib bo'lmaydi: qoldiq allaqachon o'zgargan.
    # Xatoni tuzatish uchun teskari hujjat yaratiladi — buxgalteriyadagi kabi.
    if document.status not in (Status.DRAFT, Status.PICKING):
        raise StockError(_("Bajarilgan hujjatni bekor qilib bo'lmaydi."))
    document.status = Status.CANCELLED
    document.cancelled_by = user
    document.save(update_fields=["status", "cancelled_by", "updated_at"])


# --- Inventarizatsiya ---


@transaction.atomic
def open_count(*, company, warehouse, zone, user):
    """Sanoq ochiladi va shu paytdagi tizim qoldig'i qatorlarga ko'chiriladi."""
    count = StockCount.objects.create(
        company=company, warehouse=warehouse, zone=zone.strip(), created_by=user
    )
    stock = Stock.objects.filter(location__warehouse=warehouse, quantity__gt=0)
    if count.zone:
        stock = stock.filter(location__zone__iexact=count.zone)

    StockCountLine.objects.bulk_create(
        StockCountLine(
            company=company,
            count=count,
            product_id=row.product_id,
            location_id=row.location_id,
            system_quantity=row.quantity,
        )
        for row in stock
    )
    return count


@transaction.atomic
def finish_count(count, user):
    """
    Farqlar qoldiqqa yoziladi. Farqni sanoq ochilgandagi emas, hozirgi qoldiqqa
    nisbatan hisoblaymiz: sanoq davomida kirim bo'lgan bo'lsa ham natija to'g'ri chiqadi.
    """
    if count.status != StockCount.Status.OPEN:
        raise StockError(_("Bu sanoq allaqachon yakunlangan."))

    lines = count.lines.select_related("product", "location").filter(counted_quantity__isnull=False)
    for line in lines:
        current = Stock.objects.filter(product=line.product, location=line.location).first()
        current_quantity = current.quantity if current else 0
        change_stock(
            product=line.product,
            location=line.location,
            delta=line.counted_quantity - current_quantity,
            reason=Reason.COUNT,
            user=user,
            document_number=count.number,
        )

    count.status = StockCount.Status.FINISHED
    count.finished_by = user
    count.finished_at = timezone.now()
    count.save(update_fields=["status", "finished_by", "finished_at", "updated_at"])
