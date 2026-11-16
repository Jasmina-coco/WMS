from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("django-admin/", admin.site.urls),
    path("panel/", include("apps.panel.urls")),
    path("", include("apps.accounts.urls")),
    path("app/", include("apps.reports.urls")),
    path("app/warehouses/", include("apps.warehouses.urls")),
    path("app/products/", include("apps.catalog.urls")),
    path("app/stock/", include("apps.inventory.urls")),
    path("app/docs/", include("apps.operations.urls")),
    path("", include("apps.landing.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
