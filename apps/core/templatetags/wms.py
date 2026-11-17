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


@register.inclusion_tag("_nav.html", takes_context=True)
def nav(context, url, label, icon, match="", namespace="", kind="", badge=None):
    """
    Chap menyudagi bitta band. Joriy sahifaga mos kelsa, "active" bo'ladi:
        {% nav u l "box" namespace="catalog" %}
        {% nav u l "grid" match="dashboard" %}
    """
    resolved = context["request"].resolver_match
    active = bool(
        (match and resolved.url_name in match.split(","))
        or (namespace and resolved.namespace == namespace)
        or (kind and context.get("kind") == kind)
    )
    return {"url": url, "label": label, "icon": icon, "active": active, "badge": badge}
