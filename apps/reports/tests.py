from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.core.testing import make_company
from apps.operations import services
from apps.operations.models import Document, DocumentLine


class DashboardTests(TestCase):
    def setUp(self):
        self.d = make_company()
        self.user = self.d["manager"]

    def make_doc(self, kind, quantity):
        doc = Document.objects.create(
            company=self.d["company"],
            kind=kind,
            warehouse=self.d["warehouse"],
            created_by=self.user,
        )
        DocumentLine.objects.create(
            company=self.d["company"],
            document=doc,
            product=self.d["product"],
            location=self.d["loc_a"],
            quantity=quantity,
        )
        return doc

    def test_dashboard_with_activity(self):
        services.confirm(self.make_doc("receipt", 10), self.user)
        shipment = self.make_doc("shipment", 4)
        services.confirm(shipment, self.user)
        services.confirm(shipment, self.user)
        self.make_doc("receipt", 1)  # qoralama — "kutayotgan ishlar"da chiqishi kerak

        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.status_code, 200)

        context = response.context
        self.assertEqual(context["kpis"]["receipt"]["value"], 1)
        self.assertEqual(context["kpis"]["shipment"]["value"], 1)
        self.assertEqual(context["pending"]["receipts"], 1)
        top = list(context["top_products"])
        self.assertEqual(top[0]["shipped"], Decimal("4"))
        self.assertEqual(context["flow"][-1]["incoming"], Decimal("10"))
        self.assertEqual(context["flow"][-1]["outgoing"], Decimal("4"))

    def test_other_company_data_not_counted(self):
        other = make_company("Boshqa")
        doc = Document.objects.create(
            company=other["company"],
            kind="receipt",
            warehouse=other["warehouse"],
            created_by=other["manager"],
        )
        DocumentLine.objects.create(
            company=other["company"],
            document=doc,
            product=other["product"],
            location=other["loc_a"],
            quantity=5,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.context["pending"]["receipts"], 0)
