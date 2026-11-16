from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from apps.core.forms import CompanyModelForm
from apps.core.permissions import permission_choices

from .models import Role, User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label=_("Login"), widget=forms.TextInput(attrs={"autofocus": True}))
    password = forms.CharField(label=_("Parol"), widget=forms.PasswordInput)


class RoleForm(CompanyModelForm):
    permissions = forms.MultipleChoiceField(
        label=_("Ruxsatlar"),
        choices=permission_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name", "permissions"]
        labels = {"name": _("Rol nomi")}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        same = Role.objects.for_company(self.company).filter(name__iexact=name)
        if self.instance.pk:
            same = same.exclude(pk=self.instance.pk)
        if same.exists():
            raise forms.ValidationError(_("Bunday nomli rol allaqachon bor."))
        return name


class StaffForm(CompanyModelForm):
    """Menejer xodim qo'shadi yoki tahrirlaydi. Parol faqat yangi xodimda majburiy."""

    password = forms.CharField(
        label=_("Parol"),
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text=_("Tahrirlashda bo'sh qoldirsangiz, parol o'zgarmaydi."),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "phone", "role", "warehouses", "is_active"]
        labels = {
            "username": _("Login"),
            "first_name": _("Ism"),
            "last_name": _("Familiya"),
            "is_active": _("Faol"),
        }
        widgets = {"warehouses": forms.CheckboxSelectMultiple}

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not self.instance.pk and not password:
            raise forms.ValidationError(_("Yangi xodim uchun parol kiriting."))
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.company = self.company
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user
