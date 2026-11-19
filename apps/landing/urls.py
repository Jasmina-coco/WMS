from django.urls import path

from . import views

app_name = "landing"

urlpatterns = [
    path("", views.home, name="home"),
    path("ariza/", views.submit_lead, name="submit"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_xml, name="sitemap"),
    path(views.GOOGLE_VERIFICATION_FILE, views.google_verification, name="google_verification"),
]
