from unittest import mock

from django.test import SimpleTestCase

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
