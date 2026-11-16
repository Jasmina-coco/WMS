import re

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Lead


class LeadForm(forms.ModelForm):
    # Honeypot: odam bu maydonni ko'rmaydi (CSS bilan yashirilgan), bot esa
    # hamma maydonni to'ldiradi. To'ldirilgan bo'lsa — bu bot.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1"}))

    class Meta:
        model = Lead
        fields = ["name", "company_name", "phone", "email", "warehouses_count", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3}),
            "phone": forms.TextInput(
                attrs={"placeholder": "+998 90 123 45 67", "inputmode": "tel"}
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 9 or len(digits) > 15:
            raise forms.ValidationError(_("Telefon raqamini to'g'ri kiriting."))
        return phone.strip()

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))
