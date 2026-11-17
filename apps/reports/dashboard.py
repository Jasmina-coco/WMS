"""
Bosh sahifa (dashboard) uchun ma'lumotlar.

Har bir blok alohida funksiya — view'da faqat ularni yig'ib shablonga beramiz.
Hamma hisoblar bazada (COUNT, SUM) bajariladi, Python'da sikl bilan sanalmaydi.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.utils import timezone

from apps.catalog.models import Product
from apps.inventory.models import Stock, StockMovement
from apps.operations.models import Document, StockCount
from apps.warehouses.models import Location

from . import queries


def percent_change(today, yesterday):
    """Kechagiga nisbatan o'zgarish foizi. Kecha 0 bo'lsa — solishtirib bo'lmaydi."""
    if not yesterday:
        return None
    return round((today - yesterday) / yesterday * 100)


def share(part, total):
    return round(part / total * 100) if total else 0


def daily_kpis(company, warehouses):
    """Yuqoridagi ko'k blokdagi 4 ta ko'rsatkich: bugun va kecha bilan solishtirish."""
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    done = Document.objects.for_company(company).filter(
        warehouse__in=warehouses, status=Document.Status.DONE
    )
    movements = StockMovement.objects.filter(location__warehouse__in=warehouses)

    def docs(kind, day):
        return done.filter(kind=kind, confirmed_at__date=day).count()

    def moves(day):
        return movements.filter(created_at__date=day).count()

    open_docs = (
        Document.objects.for_company(company)
        .filter(warehouse__in=warehouses, status__in=["draft", "picking"])
        .count()
    )
    rows = [
        ("receipt", docs("receipt", today), docs("receipt", yesterday)),
        ("shipment", docs("shipment", today), docs("shipment", yesterday)),
        ("movements", moves(today), moves(yesterday)),
    ]
    result = {
        key: {"value": t, "yesterday": y, "change": percent_change(t, y)} for key, t, y in rows
    }
    result["open"] = {"value": open_docs, "change": None}
    return result


def summary_cards(company, warehouses):
    """To'rtta katta karta: qiymat + progress chizig'i."""
    all_warehouses = warehouses.count()
    active_warehouses = warehouses.filter(is_active=True).count()

    products = Product.objects.for_company(company).filter(is_active=True)
    products_total = products.count()
    stock = Stock.objects.filter(location__warehouse__in=warehouses, quantity__gt=0)
    products_in_stock = stock.values("product").distinct().count()

    locations = Location.objects.filter(warehouse__in=warehouses, is_active=True)
    locations_total = locations.count()
    locations_used = stock.values("location").distinct().count()

    low = queries.low_stock(company, warehouses).count()
    healthy = products_total - low

    return [
        {
            "key": "warehouses",
            "value": all_warehouses,
            "sub": active_warehouses,
            "progress": share(active_warehouses, all_warehouses),
        },
        {
            "key": "products",
            "value": products_total,
            "sub": products_in_stock,
            "progress": share(products_in_stock, products_total),
        },
        {
            "key": "locations",
            "value": locations_total,
            "sub": locations_used,
            "progress": share(locations_used, locations_total),
        },
        {
            "key": "health",
            "value": low,
            "sub": healthy,
            "progress": share(healthy, products_total),
        },
    ]


def monthly_flow(company, warehouses, months=3):
    """
    Oxirgi N oy bo'yicha kirim va chiqim miqdori — gorizontal chiziqli grafik uchun.
    Chiziq uzunligi eng katta oyga nisbatan foizda beriladi.
    """
    today = timezone.localdate()
    first = today.replace(day=1)
    periods = []
    for _ in range(months):
        periods.append(first)
        first = (first - timedelta(days=1)).replace(day=1)
    periods.reverse()

    movements = StockMovement.objects.filter(
        company=company, location__warehouse__in=warehouses, created_at__date__gte=periods[0]
    )
    rows = []
    for start in periods:
        end = (start + timedelta(days=32)).replace(day=1)
        month = movements.filter(created_at__date__gte=start, created_at__date__lt=end)
        totals = month.aggregate(
            incoming=Sum("quantity", filter=Q(reason="receipt")),
            outgoing=Sum("quantity", filter=Q(reason="shipment")),
            operations=Count("id"),
        )
        rows.append(
            {
                "month": start,
                "incoming": totals["incoming"] or Decimal("0"),
                "outgoing": -(totals["outgoing"] or Decimal("0")),
                "operations": totals["operations"],
            }
        )

    peak = max([r["incoming"] for r in rows] + [r["outgoing"] for r in rows] + [Decimal("1")])
    for index, row in enumerate(rows):
        row["in_width"] = share(row["incoming"], peak)
        row["out_width"] = share(row["outgoing"], peak)
        previous = rows[index - 1]["operations"] if index else None
        row["change"] = percent_change(row["operations"], previous)

    totals = {
        "incoming": sum(r["incoming"] for r in rows),
        "outgoing": sum(r["outgoing"] for r in rows),
        "operations": sum(r["operations"] for r in rows),
    }
    totals["per_month"] = round(totals["operations"] / months)
    return rows, totals


def recent_activity(warehouses, limit=6):
    return StockMovement.objects.filter(location__warehouse__in=warehouses).select_related(
        "product", "location", "created_by"
    )[:limit]


def top_products(company, warehouses, limit=3):
    """Shu oy eng ko'p jo'natilgan tovarlar."""
    start = timezone.localdate().replace(day=1)
    return (
        StockMovement.objects.filter(
            company=company,
            location__warehouse__in=warehouses,
            reason="shipment",
            created_at__date__gte=start,
        )
        .values("product__id", "product__name", "product__sku", "product__unit")
        .annotate(shipped=-Sum("quantity"), operations=Count("id"))
        .order_by(F("shipped").desc())[:limit]
    )


def pending(company, warehouses):
    """Pastdagi "kutayotgan ishlar" bloki."""
    documents = Document.objects.for_company(company).filter(warehouse__in=warehouses)
    return {
        "receipts": documents.filter(kind="receipt", status="draft").count(),
        "shipments": documents.filter(kind="shipment", status__in=["draft", "picking"]).count(),
        "counts": StockCount.objects.for_company(company)
        .filter(warehouse__in=warehouses, status="open")
        .count(),
    }
