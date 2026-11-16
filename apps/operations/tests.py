from decimal import Decimal

from django.test import TestCase

from apps.core.testing import make_company
from apps.inventory.models import Stock, StockMovement
from apps.inventory.services import StockError, change_stock, quantity_at
from apps.warehouses.models import Location, Warehouse

from . import services
from .models import Document, DocumentLine


class StockServiceTests(TestCase):
    def setUp(self):
        self.d = make_company()

    def test_receipt_increases_stock_and_writes_journal(self):
        change_stock(
            product=self.d["product"],
            location=self.d["loc_a"],
            delta=10,
            reason="receipt",
            user=self.d["manager"],
        )
        self.assertEqual(quantity_at(self.d["product"], self.d["loc_a"]), Decimal("10"))
        movement = StockMovement.objects.get()
        self.assertEqual(movement.balance_after, Decimal("10"))

    def test_cannot_go_negative(self):
        change_stock(
            product=self.d["product"],
            location=self.d["loc_a"],
            delta=3,
            reason="receipt",
            user=self.d["manager"],
        )
        with self.assertRaises(StockError):
            change_stock(
                product=self.d["product"],
                location=self.d["loc_a"],
                delta=-5,
                reason="shipment",
                user=self.d["manager"],
            )
        self.assertEqual(quantity_at(self.d["product"], self.d["loc_a"]), Decimal("3"))


class DocumentFlowTests(TestCase):
    def setUp(self):
        self.d = make_company()
        self.user = self.d["manager"]

    def make_doc(self, kind, quantity, location=None, to_location=None, **extra):
        doc = Document.objects.create(
            company=self.d["company"],
            kind=kind,
            warehouse=self.d["warehouse"],
            created_by=self.user,
            **extra,
        )
        DocumentLine.objects.create(
            company=self.d["company"],
            document=doc,
            product=self.d["product"],
            location=location or self.d["loc_a"],
            to_location=to_location,
            quantity=quantity,
        )
        return doc

    def stock(self, location):
        return quantity_at(self.d["product"], location)

    def test_receipt_then_shipment(self):
        receipt = self.make_doc("receipt", 20)
        services.confirm(receipt, self.user)
        receipt.refresh_from_db()
        self.assertEqual(receipt.status, "done")
        self.assertTrue(receipt.number.startswith("KR-"))

        shipment = self.make_doc("shipment", 8)
        services.confirm(shipment, self.user)  # terish boshlandi
        self.assertEqual(self.stock(self.d["loc_a"]), Decimal("20"))
        services.confirm(shipment, self.user)  # jo'natildi
        self.assertEqual(self.stock(self.d["loc_a"]), Decimal("12"))

    def test_shipment_without_stock_fails_and_changes_nothing(self):
        shipment = self.make_doc("shipment", 5)
        with self.assertRaises(StockError):
            services.confirm(shipment, self.user)
        shipment.refresh_from_db()
        self.assertEqual(shipment.status, "draft")

    def test_transfer_moves_between_locations(self):
        services.confirm(self.make_doc("receipt", 10), self.user)
        transfer = self.make_doc(
            "transfer", 4, to_location=self.d["loc_b"], dest_warehouse=self.d["warehouse"]
        )
        services.confirm(transfer, self.user)
        self.assertEqual(self.stock(self.d["loc_a"]), Decimal("6"))
        self.assertEqual(self.stock(self.d["loc_b"]), Decimal("4"))

    def test_line_location_must_belong_to_document_warehouse(self):
        other = Warehouse.objects.create(company=self.d["company"], name="Boshqa")
        foreign = Location.objects.create(company=self.d["company"], warehouse=other, code="X-1")
        receipt = self.make_doc("receipt", 1, location=foreign)
        with self.assertRaises(StockError):
            services.confirm(receipt, self.user)

    def test_done_document_cannot_be_cancelled(self):
        receipt = self.make_doc("receipt", 1)
        services.confirm(receipt, self.user)
        with self.assertRaises(StockError):
            services.cancel(receipt, self.user)

    def test_stock_count_fixes_difference(self):
        services.confirm(self.make_doc("receipt", 10), self.user)
        count = services.open_count(
            company=self.d["company"], warehouse=self.d["warehouse"], zone="", user=self.user
        )
        line = count.lines.get()
        self.assertEqual(line.system_quantity, Decimal("10"))

        line.counted_quantity = Decimal("7")
        line.save()
        services.finish_count(count, self.user)

        self.assertEqual(self.stock(self.d["loc_a"]), Decimal("7"))
        self.assertEqual(Stock.objects.get().quantity, Decimal("7"))
        self.assertEqual(StockMovement.objects.filter(reason="count").get().quantity, Decimal("-3"))
