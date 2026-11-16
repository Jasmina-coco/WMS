from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.StockListView.as_view(), name="stock"),
    path("movements/", views.MovementListView.as_view(), name="movements"),
]
