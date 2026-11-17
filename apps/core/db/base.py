"""
PostgreSQL backend: parolni AWS Secrets Manager'dan oladi.

RDS bazasining paroli Secrets Manager'da turadi va har 7 kunda avtomatik
almashtiriladi. Parolni .env ga yozib qo'ysak, bir hafta o'tib sayt bazaga
ulana olmay qoladi. Shuning uchun har yangi ulanishda parolni secret'dan
olamiz (10 daqiqalik kesh bilan). Parol almashib, ulanish rad etilsa —
keshni tozalab, yangi parol bilan yana bir marta urinib ko'ramiz.

Kodda ham, serverdagi fayllarda ham parol yo'q: EC2 IAM role orqali o'qiladi.
"""

import json
import threading
import time

import boto3
from django.conf import settings
from django.db.backends.postgresql import base

CACHE_SECONDS = 600

_lock = threading.Lock()
_cache = {}


def fetch_credentials(secret_arn, force=False):
    with _lock:
        cached = _cache.get(secret_arn)
        if cached and not force and time.time() - cached[0] < CACHE_SECONDS:
            return cached[1]

        client = boto3.client("secretsmanager", region_name=settings.AWS_REGION)
        secret = json.loads(client.get_secret_value(SecretId=secret_arn)["SecretString"])
        credentials = {"user": secret["username"], "password": secret["password"]}
        _cache[secret_arn] = (time.time(), credentials)
        return credentials


class DatabaseWrapper(base.DatabaseWrapper):
    def _secret_arn(self):
        return self.settings_dict.get("SECRET_ARN")

    def get_connection_params(self):
        params = super().get_connection_params()
        if self._secret_arn():
            params.update(fetch_credentials(self._secret_arn()))
        return params

    def get_new_connection(self, conn_params):
        try:
            return super().get_new_connection(conn_params)
        except base.Database.OperationalError:
            if not self._secret_arn():
                raise
            # Parol endigina almashgan bo'lishi mumkin — yangisini olib, qayta urinamiz
            conn_params.update(fetch_credentials(self._secret_arn(), force=True))
            return super().get_new_connection(conn_params)
