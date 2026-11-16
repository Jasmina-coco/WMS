from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Company, User
from apps.landing.models import Lead


class LeadUpdateForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["status", "admin_note"]
        widgets = {"admin_note": forms.Textarea(attrs={"rows": 4})}


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "contact_person", "phone", "note", "is_active"]
        widgets = {"note": forms.Textarea(attrs={"rows": 3})}


class CompanyCreateForm(CompanyForm):
    """Kompaniya va uning birinchi menejeri bir vaqtda yaratiladi."""

    manager_username = forms.CharField(label=_("Menejer logini"), max_length=150)
    manager_password = forms.CharField(label=_("Menejer paroli"), widget=forms.PasswordInput)

    def clean_manager_username(self):
        username = self.cleaned_data["manager_username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(_("Bu login band."))
        return username

    def clean_manager_password(self):
        password = self.cleaned_data["manager_password"]
        validate_password(password)
        return password

    @transaction.atomic
    def save(self, commit=True):
        company = super().save()
        User.objects.create_user(
            username=self.cleaned_data["manager_username"],
            password=self.cleaned_data["manager_password"],
            first_name=company.contact_person,
            phone=company.phone,
            company=company,
            is_manager=True,
        )
        return company
