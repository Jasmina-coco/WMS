"""
Fayllarni Amazon S3 da saqlash.

Django'ning Storage interfeysini boto3 orqali o'zimiz yozdik. Shunda
`ImageField` va `FileField` odatdagidek ishlaydi, fayl esa S3 ga tushadi.

Muhim tomonlari:
- Bucket yopiq (public emas). Faylni ko'rish uchun 1 soatlik imzolangan
  havola (presigned URL) beriladi. Havolani faqat tegishli kompaniya xodimi
  ochgan sahifada generatsiya qilamiz.
- Access key kodda ham, .env da ham yo'q. boto3 EC2 ga biriktirilgan
  IAM role'dan vaqtinchalik kalitlarni o'zi oladi.
"""

import mimetypes
import uuid
from pathlib import PurePosixPath

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

URL_EXPIRES_SECONDS = 3600


@deconstructible
class S3Storage(Storage):
    def __init__(self, bucket=None, region=None):
        self.bucket = bucket or settings.AWS_S3_BUCKET
        self.region = region or settings.AWS_REGION
        self._client = None

    @property
    def client(self):
        # Klientni birinchi kerak bo'lganda yaratamiz, har so'rovda emas
        if self._client is None:
            self._client = boto3.client("s3", region_name=self.region)
        return self._client

    def _open(self, name, mode="rb"):
        response = self.client.get_object(Bucket=self.bucket, Key=name)
        return ContentFile(response["Body"].read(), name=name)

    def _save(self, name, content):
        content_type = (
            getattr(content, "content_type", None)
            or mimetypes.guess_type(name)[0]
            or "application/octet-stream"
        )
        content.seek(0)
        self.client.upload_fileobj(
            content,
            self.bucket,
            name,
            ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"},
        )
        return name

    def get_available_name(self, name, max_length=None):
        # Nomlar to'qnashmasligi uchun oldiga qisqa tasodifiy prefiks qo'shamiz,
        # shunda har safar S3 dan "bunday fayl bormi" deb so'rash shart emas
        path = PurePosixPath(name)
        unique = f"{uuid.uuid4().hex[:8]}_{path.name}"
        return str(path.with_name(unique))

    def exists(self, name):
        try:
            self.client.head_object(Bucket=self.bucket, Key=name)
            return True
        except ClientError:
            return False

    def delete(self, name):
        self.client.delete_object(Bucket=self.bucket, Key=name)

    def size(self, name):
        return self.client.head_object(Bucket=self.bucket, Key=name)["ContentLength"]

    def url(self, name):
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": name},
            ExpiresIn=URL_EXPIRES_SECONDS,
        )


@deconstructible
class CompanyUploadPath:
    """
    Fayllar kompaniya bo'yicha papkalarga ajratiladi:
    companies/<id>/products/... , companies/<id>/documents/...

    Funksiya emas, klass — chunki Django migratsiyaga yozishi uchun
    upload_to qiymatini saqlab qo'ya olishi kerak.
    """

    def __init__(self, folder):
        self.folder = folder

    def __call__(self, instance, filename):
        return f"companies/{instance.company_id}/{self.folder}/{filename}"
