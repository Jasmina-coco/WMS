from django.urls import path

from . import views

app_name = "warehouses"

urlpatterns = [
    path("", views.WarehouseListView.as_view(), name="list"),
    path("new/", views.WarehouseCreateView.as_view(), name="create"),
    path("<int:pk>/", views.WarehouseUpdateView.as_view(), name="edit"),
    path("locations/", views.LocationListView.as_view(), name="locations"),
    path("locations/new/", views.LocationCreateView.as_view(), name="location_create"),
    path("locations/<int:pk>/", views.LocationUpdateView.as_view(), name="location_edit"),
]
