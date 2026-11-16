"""Testlar uchun umumiy tayyorgarlik: kompaniya, ombor, joy, tovar va foydalanuvchilar."""

from apps.accounts.models import Company, Role, User
from apps.catalog.models import Product
from apps.warehouses.models import Location, Warehouse


def make_company(name="Test MChJ"):
    company = Company.objects.create(name=name)
    manager = User.objects.create_user(
        f"manager_{company.pk}", password="pass12345!", company=company, is_manager=True
    )
    warehouse = Warehouse.objects.create(company=company, name="Asosiy")
    loc_a = Location.objects.create(company=company, warehouse=warehouse, code="A-01")
    loc_b = Location.objects.create(company=company, warehouse=warehouse, code="A-02")
    product = Product.objects.create(company=company, sku="P-1", name="Tovar 1")
    return {
        "company": company,
        "manager": manager,
        "warehouse": warehouse,
        "loc_a": loc_a,
        "loc_b": loc_b,
        "product": product,
    }


def make_worker(data, permissions, username="worker", warehouses=None):
    role = Role.objects.create(
        company=data["company"], name=f"Rol {username}", permissions=permissions
    )
    user = User.objects.create_user(
        username, password="pass12345!", company=data["company"], role=role
    )
    user.warehouses.set(warehouses if warehouses is not None else [data["warehouse"]])
    return user
