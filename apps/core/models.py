from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CompanyQuerySet(models.QuerySet):
    def for_company(self, company):
        return self.filter(company=company)


class CompanyModel(TimeStampedModel):
    """
    Kompaniyaga tegishli har bir jadval shundan meros oladi.

    Kompaniyalar bitta bazada turadi, ularni faqat company_id ajratib turadi.
    Shuning uchun view'larda doim `Model.objects.for_company(request.company)`
    ishlatiladi — CompanyScopedMixin buni avtomatik qiladi.
    """

    company = models.ForeignKey(
        "accounts.Company", on_delete=models.CASCADE, related_name="+", db_index=True
    )

    objects = CompanyQuerySet.as_manager()

    class Meta:
        abstract = True
