from django.urls import path

from . import views

app_name = "landing"

urlpatterns = [
    path("", views.home, name="home"),
    path("ariza/", views.submit_lead, name="submit"),
]
