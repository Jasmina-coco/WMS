from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Lead

VALID = {
    "name": "Ali",
    "company_name": "Ali Savdo",
    "phone": "+998 90 123 45 67",
    "warehouses_count": "2",
}


class LeadTests(TestCase):
    def test_landing_opens(self):
        self.assertEqual(self.client.get(reverse("landing:home")).status_code, 200)

    def test_lead_saved(self):
        response = self.client.post(reverse("landing:submit"), VALID, HTTP_X_REQUESTED_WITH="fetch")
        self.assertTrue(response.json()["ok"])
        self.assertEqual(Lead.objects.get().status, Lead.Status.NEW)

    def test_bad_phone_rejected(self):
        response = self.client.post(
            reverse("landing:submit"), {**VALID, "phone": "123"}, HTTP_X_REQUESTED_WITH="fetch"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.json()["errors"])

    def test_honeypot_is_ignored_silently(self):
        response = self.client.post(
            reverse("landing:submit"),
            {**VALID, "website": "spam.com"},
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertTrue(response.json()["ok"])
        self.assertFalse(Lead.objects.exists())

    @override_settings(LEAD_LIMIT_PER_HOUR=2)
    def test_rate_limit(self):
        for _ in range(4):
            self.client.post(reverse("landing:submit"), VALID, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(Lead.objects.count(), 2)

    def test_health(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.json()["database"], True)
