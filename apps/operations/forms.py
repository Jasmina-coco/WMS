from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Product
from apps.core.forms import CompanyModelForm
from apps.warehouses.models import Location

from .models import Attachment, Document, DocumentLine, StockCount

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024


class DocumentForm(CompanyModelForm):
    def __init__(self, *args, kind, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = kind
        allowed = user.allowed_warehouses().filter(is_active=True)
        self.fields["warehouse"].queryset = allowed

        if kind == Document.Kind.TRANSFER:
            self.fields["dest_warehouse"].queryset = allowed
            self.fields["dest_warehouse"].required = True
            del self.fields["partner"]
        else:
            del self.fields["dest_warehouse"]
            self.fields["partner"].label = (
                _("Yetkazib beruvchi") if kind == Document.Kind.RECEIPT else _("Mijoz / manzil")
            )

    class Meta:
        model = Document
        fields = ["warehouse", "dest_warehouse", "partner", "note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2})}


class LineForm(forms.ModelForm):
    class Meta:
        model = DocumentLine
        fields = ["product", "location", "to_location", "quantity"]


class BaseLineFormSet(BaseInlineFormSet):
    """
    Qatorlar jadvali. Tanlovlardagi tovar va joylar faqat shu kompaniyaniki
    va faqat xodimga ruxsat berilgan omborlarniki bo'ladi.
    """

    def __init__(self, *args, company, user, kind, **kwargs):
        self.company = company
        self.user = user
        self.kind = kind
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        self._limit_choices(form)
        return form

    @property
    def empty_form(self):
        form = super().empty_form
        self._limit_choices(form)
        return form

    def _limit_choices(self, form):
        locations = Location.objects.filter(
            warehouse__in=self.user.allowed_warehouses(), is_active=True
        ).select_related("warehouse")
        form.fields["product"].queryset = Product.objects.for_company(self.company).filter(
            is_active=True
        )
        form.fields["location"].queryset = locations
        if self.kind == Document.Kind.TRANSFER:
            form.fields["to_location"].queryset = locations
            form.fields["to_location"].required = True
        else:
            del form.fields["to_location"]

    def save_new(self, form, commit=True):
        form.instance.company = self.company
        return super().save_new(form, commit=commit)

    def clean(self):
        super().clean()
        filled = [
            f for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE", False)
        ]
        if not filled:
            raise forms.ValidationError(_("Kamida bitta qator kiriting."))


LineFormSet = inlineformset_factory(
    Document,
    DocumentLine,
    form=LineForm,
    formset=BaseLineFormSet,
    extra=1,
    can_delete=True,
)


class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ["file"]

    def clean_file(self):
        file = self.cleaned_data["file"]
        if file.size > MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError(_("Fayl hajmi 10 MB dan oshmasin."))
        return file


class StockCountForm(forms.ModelForm):
    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["warehouse"].queryset = user.allowed_warehouses().filter(is_active=True)

    class Meta:
        model = StockCount
        fields = ["warehouse", "zone"]


class CountExtraLineForm(forms.Form):
    """Sanoqda tizimda yo'q, lekin joyida topilgan tovarni qo'shish uchun."""

    product = forms.ModelChoiceField(label=_("Tovar"), queryset=Product.objects.none())
    location = forms.ModelChoiceField(label=_("Joy"), queryset=Location.objects.none())
    counted_quantity = forms.DecimalField(label=_("Sanalgan miqdor"), min_value=0)

    def __init__(self, *args, count, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.for_company(count.company)
        locations = Location.objects.filter(warehouse=count.warehouse)
        if count.zone:
            locations = locations.filter(zone__iexact=count.zone)
        self.fields["location"].queryset = locations
