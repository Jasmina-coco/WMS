from unittest import mock

from django.test import SimpleTestCase, TestCase

from apps.core.db import base


class SecretCredentialsTests(SimpleTestCase):
    def setUp(self):
        base._cache.clear()

    def fake_client(self, password):
        client = mock.Mock()
        client.get_secret_value.return_value = {
            "SecretString": '{"username": "postgres", "password": "%s"}' % password
        }
        return client

    def test_credentials_are_cached(self):
        client = self.fake_client("p1")
        with mock.patch.object(base.boto3, "client", return_value=client):
            first = base.fetch_credentials("arn:test")
            second = base.fetch_credentials("arn:test")
        self.assertEqual(first, {"user": "postgres", "password": "p1"})
        self.assertEqual(first, second)
        self.assertEqual(client.get_secret_value.call_count, 1)

    def test_force_refreshes_rotated_password(self):
        with mock.patch.object(base.boto3, "client", return_value=self.fake_client("old")):
            base.fetch_credentials("arn:test")
        with mock.patch.object(base.boto3, "client", return_value=self.fake_client("new")):
            self.assertEqual(base.fetch_credentials("arn:test")["password"], "old")
            self.assertEqual(base.fetch_credentials("arn:test", force=True)["password"], "new")


class ReadOnlyAdminTests(TestCase):
    """Admin'da baza ma'lumoti faqat ko'riladi: qo'shish va o'chirish taqiqlangan."""

    def setUp(self):
        from apps.accounts.models import User

        self.client.force_login(User.objects.create_superuser("root", password=None))

    def test_tables_are_listed(self):
        for url in ["catalog/product", "inventory/stockmovement", "operations/document"]:
            self.assertEqual(self.client.get(f"/django-admin/{url}/").status_code, 200)

    def test_add_is_forbidden(self):
        self.assertEqual(self.client.get("/django-admin/catalog/product/add/").status_code, 403)
