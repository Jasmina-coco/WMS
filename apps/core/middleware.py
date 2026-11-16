from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _


class CompanyMiddleware:
    """
    Har bir so'rovga `request.company` ni qo'shadi.

    Foydalanuvchining kompaniyasi bloklangan bo'lsa, uni tizimdan chiqarib
    yuboramiz — admin kompaniyani o'chirsa, xodimlar darhol kira olmay qoladi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None
        user = request.user

        if user.is_authenticated and user.company_id:
            company = user.company
            if not company.is_active:
                logout(request)
                messages.error(
                    request, _("Kompaniya akkaunti faol emas. Administratorga murojaat qiling.")
                )
                return redirect("accounts:login")
            request.company = company

        return self.get_response(request)
