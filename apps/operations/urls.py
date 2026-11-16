from django.urls import path

from . import views

app_name = "operations"

urlpatterns = [
    path("counts/", views.CountListView.as_view(), name="counts"),
    path("counts/new/", views.CountCreateView.as_view(), name="count_create"),
    path("counts/<int:pk>/", views.CountDetailView.as_view(), name="count_detail"),
    path("<str:kind>/", views.DocumentListView.as_view(), name="list"),
    path("<str:kind>/new/", views.DocumentFormView.as_view(), name="create"),
    path("<str:kind>/<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    path("<str:kind>/<int:pk>/edit/", views.DocumentFormView.as_view(), name="edit"),
    path("<str:kind>/<int:pk>/print/", views.DocumentPrintView.as_view(), name="print"),
    path("<str:kind>/<int:pk>/files/", views.AttachmentUploadView.as_view(), name="upload"),
    path(
        "<str:kind>/<int:pk>/files/<int:attachment_id>/",
        views.AttachmentOpenView.as_view(),
        name="attachment",
    ),
    # Bu yo'l eng oxirida turishi kerak, aks holda "files" ham amal deb tushuniladi
    path(
        "<str:kind>/<int:pk>/<str:action>/",
        views.DocumentActionView.as_view(),
        name="action",
    ),
]
