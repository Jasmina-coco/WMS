from django import forms


class CompanyModelForm(forms.ModelForm):
    """
    Formadagi tanlov maydonlari (ombor, kategoriya, tovar...) faqat joriy
    kompaniyaning yozuvlarini ko'rsatishi kerak. Bu forma ularni avtomatik
    filtrlaydi — aks holda select ichida boshqa kompaniyaning ombori chiqib qolardi.
    """

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = company
        for field in self.fields.values():
            queryset = getattr(field, "queryset", None)
            if queryset is not None and hasattr(queryset.model, "company"):
                field.queryset = queryset.filter(company=company)
