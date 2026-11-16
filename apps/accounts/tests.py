"""Ruxsatlar va kompaniyalar ajratilishini tekshiradigan testlar."""

from django.test import TestCase
from django.urls import reverse

from apps.core.testing import make_company, make_worker
from apps.operations.models import Document
from apps.warehouses.models import Warehouse


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.a = make_company("A kompaniya")
        self.b = make_company("B kompaniya")
        self.doc_b = Document.objects.create(
            company=self.b["company"],
            kind="receipt",
            warehouse=self.b["warehouse"],
            created_by=self.b["manager"],
        )

    def test_cannot_open_other_company_document(self):
        self.client.force_login(self.a["manager"])
        url = reverse("operations:detail", args=["receipt", self.doc_b.pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_cannot_edit_other_company_product(self):
        self.client.force_login(self.a["manager"])
        url = reverse("catalog:product_edit", args=[self.b["product"].pk])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_lists_show_only_own_data(self):
        self.client.force_login(self.a["manager"])
        response = self.client.get(reverse("catalog:products"))
        self.assertEqual(list(response.context["object_list"]), [self.a["product"]])

    def test_form_choices_are_limited_to_own_company(self):
        self.client.force_login(self.a["manager"])
        response = self.client.get(reverse("operations:create", args=["receipt"]))
        choices = list(response.context["form"].fields["warehouse"].queryset)
        self.assertEqual(choices, [self.a["warehouse"]])

    def test_blocked_company_is_logged_out(self):
        self.a["company"].is_active = False
        self.a["company"].save()
        self.client.force_login(self.a["manager"])
        response = self.client.get(reverse("reports:dashboard"))
        self.assertRedirects(response, reverse("accounts:login"))


class PermissionTests(TestCase):
    def setUp(self):
        self.d = make_company()

    def test_worker_without_permission_gets_403(self):
        worker = make_worker(self.d, ["receipts.view"])
        self.client.force_login(worker)
        self.assertEqual(
            self.client.get(reverse("operations:list", args=["receipt"])).status_code, 200
        )
        self.assertEqual(
            self.client.get(reverse("operations:list", args=["shipment"])).status_code, 403
        )
        self.assertEqual(self.client.get(reverse("accounts:staff")).status_code, 403)

    def test_worker_sees_only_assigned_warehouses(self):
        other = Warehouse.objects.create(company=self.d["company"], name="Ikkinchi")
        worker = make_worker(self.d, ["warehouses.view"], warehouses=[other])
        self.client.force_login(worker)
        response = self.client.get(reverse("warehouses:list"))
        self.assertEqual(list(response.context["object_list"]), [other])

    def test_panel_only_for_superuser(self):
        self.client.force_login(self.d["manager"])
        self.assertEqual(self.client.get(reverse("panel:dashboard")).status_code, 403)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)


class PageSmokeTests(TestCase):
    """Menejer uchun barcha asosiy sahifalar xatosiz ochilishini tekshiradi."""

    def test_pages_open(self):
        d = make_company()
        self.client.force_login(d["manager"])
        urls = [
            reverse("reports:dashboard"),
            reverse("warehouses:list"),
            reverse("warehouses:create"),
            reverse("warehouses:locations"),
            reverse("warehouses:location_create"),
            reverse("catalog:products"),
            reverse("catalog:product_create"),
            reverse("catalog:product_detail", args=[d["product"].pk]),
            reverse("catalog:categories"),
            reverse("inventory:stock"),
            reverse("inventory:movements"),
            reverse("operations:counts"),
            reverse("operations:count_create"),
            reverse("accounts:staff"),
            reverse("accounts:staff_create"),
            reverse("accounts:roles"),
            reverse("accounts:role_create"),
        ]
        for kind in ("receipt", "shipment", "transfer"):
            urls += [
                reverse("operations:list", args=[kind]),
                reverse("operations:create", args=[kind]),
            ]
        for report in ("stock", "turnover", "low", "staff"):
            urls.append(reverse("reports:report", args=[report]))

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
