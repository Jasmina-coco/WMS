from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import LeadForm
from .models import Lead


def home(request):
    return render(request, "landing/home.html", {"form": LeadForm()})


def robots_txt(request):
    # Qidiruv tizimlariga faqat ochiq sahifalarni ko'rsatamiz; tizim ichi va panel yopiq
    lines = [
        "User-agent: *",
        "Allow: /$",
        "Disallow: /app/",
        "Disallow: /panel/",
        "Disallow: /django-admin/",
        "Disallow: /login/",
        "Disallow: /ariza/",
        "Disallow: /health/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


# Google Search Console sayt egasini shu fayl orqali tasdiqlaydi — o'chirmang
GOOGLE_VERIFICATION_FILE = "google07cedd02fcf117f8.html"


def google_verification(request):
    return HttpResponse(
        f"google-site-verification: {GOOGLE_VERIFICATION_FILE}",
        content_type="text/html; charset=utf-8",
    )


def sitemap_xml(request):
    # Saytda indekslanadigan sahifa bitta — landing
    url = request.build_absolute_uri("/")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>\n"
        "</urlset>\n"
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


def client_ip(request):
    # Nginx orqasida turganimiz uchun haqiqiy IP ni Nginx X-Real-IP ga yozib beradi.
    # X-Forwarded-For ga ishonmaymiz: uni foydalanuvchi o'zi soxtalashtirishi mumkin.
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


@require_POST
def submit_lead(request):
    """
    Ariza formasi JS orqali (fetch) yuboriladi, javob JSON. Sahifa qayta
    yuklanmaydi. JS o'chirilgan bo'lsa ham forma oddiy POST sifatida ishlaydi.
    """
    form = LeadForm(request.POST)
    wants_json = request.headers.get("X-Requested-With") == "fetch"

    if not form.is_valid():
        if wants_json:
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return render(request, "landing/home.html", {"form": form}, status=400)

    ip = client_ip(request)
    hour_ago = timezone.now() - timedelta(hours=1)
    too_many = (
        Lead.objects.filter(ip_address=ip, created_at__gte=hour_ago).count()
        >= settings.LEAD_LIMIT_PER_HOUR
    )

    # Botga ham, limitdan oshganga ham "qabul qilindi" deymiz — bot farqini bilmasin.
    # Faqat bazaga yozmaymiz.
    if not form.is_spam() and not too_many:
        lead = form.save(commit=False)
        lead.ip_address = ip
        lead.save()

    message = _("Rahmat! Arizangiz qabul qilindi, tez orada siz bilan bog'lanamiz.")
    if wants_json:
        return JsonResponse({"ok": True, "message": message})
    return render(request, "landing/thanks.html", {"message": message})
