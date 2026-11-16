from django.conf import settings


def site(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
    }
