from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.ProductListView.as_view(), name="products"),
    path("new/", views.ProductCreateView.as_view(), name="product_create"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_edit"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/", views.CategoryUpdateView.as_view(), name="category_edit"),
]
