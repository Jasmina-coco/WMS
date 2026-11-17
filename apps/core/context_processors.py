from django.conf import settings


def site(request):
    context = {
        "SITE_NAME": settings.SITE_NAME,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
    }
    # Platforma admini menyusida yangi arizalar sonini ko'rsatamiz
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and user.is_superuser:
        from apps.landing.models import Lead

        context["new_leads_count"] = Lead.objects.filter(status=Lead.Status.NEW).count()
    return context
