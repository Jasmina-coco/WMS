from django import forms
from django.utils.translation import gettext_lazy as _

from apps.core.forms import CompanyModelForm

from .models import Category, Product

MAX_IMAGE_SIZE = 3 * 1024 * 1024


class CategoryForm(CompanyModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        same = Category.objects.for_company(self.company).filter(name__iexact=name)
        if self.instance.pk:
            same = same.exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError(_("Bunday kategoriya bor."))
        return name


class ProductForm(CompanyModelForm):
    class Meta:
        model = Product
        fields = ["sku", "name", "category", "unit", "barcode", "min_stock", "image", "is_active"]

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip().upper()
        same = Product.objects.for_company(self.company).filter(sku=sku)
        if self.instance.pk:
            same = same.exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError(_("Bu SKU boshqa tovarda ishlatilgan."))
        return sku

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and getattr(image, "size", 0) > MAX_IMAGE_SIZE:
            raise forms.ValidationError(_("Rasm hajmi 3 MB dan oshmasin."))
        return image

    def clean_min_stock(self):
        value = self.cleaned_data["min_stock"]
        if value < 0:
            raise forms.ValidationError(_("Manfiy bo'lishi mumkin emas."))
        return value
