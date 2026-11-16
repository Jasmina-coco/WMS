"""
Namoyish uchun demo ma'lumot: kompaniya, 2 ta ombor, joylar, tovarlar,
omborchi roli va bir nechta bajarilgan hujjat.

    python manage.py seed_demo

Qayta ishga tushirilsa, eski demo kompaniya o'chirilib, yangidan yaratiladi.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Company, Role, User
from apps.catalog.models import Category, Product
from apps.landing.models import Lead
from apps.operations import services
from apps.operations.models import Document, DocumentLine
from apps.warehouses.models import Location, Warehouse

DEMO_COMPANY = "Demo Savdo MChJ"
DEMO_PASSWORD = "demo12345"

PRODUCTS = [
    ("SUT-001", "Sut 1 l", "Sut mahsulotlari", "pcs", 50),
    ("SUT-002", "Qatiq 0.5 l", "Sut mahsulotlari", "pcs", 40),
    ("NON-001", "Non oq", "Non mahsulotlari", "pcs", 30),
    ("GUR-001", "Guruch lazer", "Bakaleya", "kg", 100),
    ("YOG-001", "Paxta yog'i 1 l", "Bakaleya", "pcs", 60),
    ("SHA-001", "Shakar", "Bakaleya", "kg", 80),
    ("CHO-001", "Choy ko'k 100 g", "Ichimliklar", "pcs", 20),
    ("SUV-001", "Mineral suv 1.5 l", "Ichimliklar", "box", 10),
]


class Command(BaseCommand):
    help = "Namoyish uchun demo kompaniya va ma'lumotlar yaratadi"

    @transaction.atomic
    def handle(self, *args, **options):
        old = Company.objects.filter(name=DEMO_COMPANY).first()
        if old:
            # PROTECT bog'lanishlari sababli avval jurnal va hujjatlarni tozalaymiz
            from apps.inventory.models import Stock, StockMovement
            from apps.operations.models import StockCount

            StockMovement.objects.filter(company=old).delete()
            Stock.objects.filter(company=old).delete()
            StockCount.objects.filter(company=old).delete()
            Document.objects.filter(company=old).delete()
            User.objects.filter(company=old).update(role=None)
            Product.objects.filter(company=old).delete()
            User.objects.filter(company=old).delete()
            old.delete()

        company = Company.objects.create(
            name=DEMO_COMPANY, contact_person="Alisher Karimov", phone="+998 90 000 00 00"
        )
        manager = User.objects.create_user(
            "demo_manager",
            password=DEMO_PASSWORD,
            first_name="Alisher",
            company=company,
            is_manager=True,
        )

        main = Warehouse.objects.create(
            company=company, name="Markaziy ombor", address="Toshkent, Sergeli"
        )
        second = Warehouse.objects.create(
            company=company, name="Chilonzor filiali", address="Toshkent, Chilonzor"
        )

        locations = {}
        for warehouse, zones in ((main, "AB"), (second, "A")):
            for zone in zones:
                for row in range(1, 3):
                    for cell in range(1, 4):
                        code = f"{zone}-{row:02d}-{cell:02d}"
                        locations[(warehouse.pk, code)] = Location.objects.create(
                            company=company, warehouse=warehouse, zone=zone, code=code
                        )

        categories = {}
        products = []
        for sku, name, category, unit, min_stock in PRODUCTS:
            if category not in categories:
                categories[category] = Category.objects.create(company=company, name=category)
            products.append(
                Product.objects.create(
                    company=company,
                    sku=sku,
                    name=name,
                    category=categories[category],
                    unit=unit,
                    min_stock=min_stock,
                )
            )

        role = Role.objects.create(
            company=company,
            name="Omborchi",
            permissions=[
                "warehouses.view",
                "products.view",
                "stock.view",
                "receipts.view",
                "receipts.create",
                "receipts.confirm",
                "shipments.view",
                "shipments.create",
                "shipments.confirm",
                "transfers.view",
                "transfers.create",
                "counts.view",
                "counts.do",
            ],
        )
        worker = User.objects.create_user(
            "demo_omborchi",
            password=DEMO_PASSWORD,
            first_name="Bobur",
            company=company,
            role=role,
        )
        worker.warehouses.set([main])

        # Kirim: hamma tovardan markaziy omborga
        receipt = Document.objects.create(
            company=company,
            kind="receipt",
            warehouse=main,
            partner="Agro Ta'minot MChJ",
            created_by=manager,
        )
        for index, product in enumerate(products):
            code = f"{'AB'[index % 2]}-01-{index % 3 + 1:02d}"
            DocumentLine.objects.create(
                company=company,
                document=receipt,
                product=product,
                location=locations[(main.pk, code)],
                quantity=Decimal(product.min_stock * 2 if index % 3 else product.min_stock // 2),
            )
        services.confirm(receipt, manager)

        # Chiqim: bir qismini jo'natamiz
        shipment = Document.objects.create(
            company=company,
            kind="shipment",
            warehouse=main,
            partner="Do'kon №12, Yunusobod",
            created_by=worker,
        )
        for line in receipt.lines.all()[:3]:
            DocumentLine.objects.create(
                company=company,
                document=shipment,
                product=line.product,
                location=line.location,
                quantity=line.quantity / 4,
            )
        services.confirm(shipment, worker)
        services.confirm(shipment, worker)

        # Ochiq chiqim — dashboardda ko'rinsin
        draft = Document.objects.create(
            company=company,
            kind="shipment",
            warehouse=main,
            partner="Do'kon №7, Mirobod",
            created_by=worker,
        )
        first = receipt.lines.first()
        DocumentLine.objects.create(
            company=company,
            document=draft,
            product=first.product,
            location=first.location,
            quantity=5,
        )

        Lead.objects.get_or_create(
            phone="+998 93 123 45 67",
            defaults={
                "name": "Dilshod",
                "company_name": "Farovon Distribyutsiya",
                "warehouses_count": 3,
                "message": "Uchta omborimiz bor, demo ko'rmoqchimiz.",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo tayyor. Loginlar: demo_manager / demo_omborchi, parol: {DEMO_PASSWORD}"
            )
        )
