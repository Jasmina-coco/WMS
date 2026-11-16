"""
Tizimdagi barcha ruxsatlar ro'yxati.

Menejer rol yaratayotganda shu ro'yxatdan belgilaydi. Ruxsat kodi
"modul.amal" ko'rinishida — view'larda aynan shu kod tekshiriladi.
Yangi ruxsat qo'shish uchun faqat shu yerga yozish kifoya.
"""

from django.utils.translation import gettext_lazy as _

PERMISSION_GROUPS = [
    (
        _("Omborlar va lokatsiyalar"),
        [
            ("warehouses.view", _("Ko'rish")),
            ("warehouses.edit", _("Qo'shish va tahrirlash")),
        ],
    ),
    (
        _("Tovarlar"),
        [
            ("products.view", _("Ko'rish")),
            ("products.edit", _("Qo'shish va tahrirlash")),
        ],
    ),
    (
        _("Qoldiqlar"),
        [
            ("stock.view", _("Ko'rish")),
        ],
    ),
    (
        _("Kirim"),
        [
            ("receipts.view", _("Ko'rish")),
            ("receipts.create", _("Yaratish")),
            ("receipts.confirm", _("Tasdiqlash")),
            ("receipts.cancel", _("Bekor qilish")),
        ],
    ),
    (
        _("Chiqim"),
        [
            ("shipments.view", _("Ko'rish")),
            ("shipments.create", _("Yaratish")),
            ("shipments.confirm", _("Terish va jo'natish")),
            ("shipments.cancel", _("Bekor qilish")),
        ],
    ),
    (
        _("Ko'chirish"),
        [
            ("transfers.view", _("Ko'rish")),
            ("transfers.create", _("Yaratish")),
            ("transfers.confirm", _("Tasdiqlash")),
        ],
    ),
    (
        _("Inventarizatsiya"),
        [
            ("counts.view", _("Ko'rish")),
            ("counts.do", _("Sanoq o'tkazish")),
            ("counts.finish", _("Yakunlash")),
        ],
    ),
    (
        _("Hisobotlar"),
        [
            ("reports.view", _("Ko'rish")),
            ("reports.export", _("Eksport")),
        ],
    ),
    (
        _("Xodimlar va rollar"),
        [
            ("staff.manage", _("Boshqarish")),
        ],
    ),
]

ALL_PERMISSIONS = {code for _group, items in PERMISSION_GROUPS for code, _label in items}


def permission_choices():
    """Formadagi checkboxlar uchun (kod, nom) juftliklari."""
    return [(code, label) for _group, items in PERMISSION_GROUPS for code, label in items]
