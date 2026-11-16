from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.forms import CompanyModelForm

from .models import Location, Warehouse


class WarehouseForm(CompanyModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "address", "is_active"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        same = Warehouse.objects.for_company(self.company).filter(name__iexact=name)
        if self.instance.pk:
            same = same.exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError(_("Bunday nomli ombor bor."))
        return name


class LocationForm(CompanyModelForm):
    class Meta:
        model = Location
        fields = ["warehouse", "zone", "code", "is_active"]

    def clean(self):
        data = super().clean()
        warehouse, code = data.get("warehouse"), data.get("code")
        if warehouse and code:
            data["code"] = code = code.strip().upper()
            same = Location.objects.filter(warehouse=warehouse, code=code)
            if self.instance.pk:
                same = same.exclude(pk=self.instance.pk)
            if same.exists():
                self.add_error("code", _("Bu omborda shunday kodli joy bor."))
        return data
