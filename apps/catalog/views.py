from django.db.models import Q, Sum
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.mixins import CompanyScopedMixin
from apps.inventory.models import Stock, StockMovement

from .forms import CategoryForm, ProductForm
from .models import Category, Product


class ProductListView(CompanyScopedMixin, ListView):
    model = Product
    permission = "products.view"
    template_name = "catalog/product_list.html"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("category")
            .annotate(total_qty=Sum("stock__quantity"))
        )
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search) | Q(barcode=search))
        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.for_company(self.request.company)
        return context


class ProductDetailView(CompanyScopedMixin, DetailView):
    model = Product
    permission = "products.view"
    template_name = "catalog/product_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warehouses = self.request.user.allowed_warehouses()
        context["stock"] = (
            Stock.objects.filter(product=self.object, location__warehouse__in=warehouses)
            .exclude(quantity=0)
            .select_related("location__warehouse")
        )
        context["movements"] = StockMovement.objects.filter(
            product=self.object, location__warehouse__in=warehouses
        ).select_related("location", "created_by")[:20]
        return context


class ProductFormMixin(CompanyScopedMixin):
    title = _("Tovar")
    model = Product
    form_class = ProductForm
    permission = "products.edit"
    template_name = "form_page.html"
    success_url = reverse_lazy("catalog:products")


class ProductCreateView(ProductFormMixin, CreateView):
    pass


class ProductUpdateView(ProductFormMixin, UpdateView):
    pass


class CategoryListView(CompanyScopedMixin, ListView):
    model = Category
    permission = "products.view"
    template_name = "catalog/category_list.html"


class CategoryFormMixin(CompanyScopedMixin):
    title = _("Kategoriya")
    model = Category
    form_class = CategoryForm
    permission = "products.edit"
    template_name = "form_page.html"
    success_url = reverse_lazy("catalog:categories")


class CategoryCreateView(CategoryFormMixin, CreateView):
    pass


class CategoryUpdateView(CategoryFormMixin, UpdateView):
    pass
