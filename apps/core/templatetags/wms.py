from django import template

register = template.Library()


@register.filter
def can(user, permission):
    """Shablonda: {% if user|can:"receipts.create" %} ... {% endif %}"""
    return user.is_authenticated and user.has_wms_perm(permission)


@register.filter
def qty(value):
    """Miqdorni ortiqcha nollarsiz ko'rsatadi: 12.500 -> 12.5, 3.000 -> 3"""
    if value is None:
        return "0"
    text = f"{value:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


@register.simple_tag(takes_context=True)
def query_with(context, **kwargs):
    """Filtrlarni saqlagan holda sahifa raqamini almashtirish uchun."""
    params = context["request"].GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()
