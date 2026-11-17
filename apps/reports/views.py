import csv
from datetime import date, timedelta

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView

from apps.core.mixins import CompanyRequiredMixin, PermissionMixin

from . import dashboard, queries


class DashboardView(CompanyRequiredMixin, TemplateView):
    """Bosh sahifa. Har bir xodim faqat ruxsati bor omborlar bo'yicha ma'lumotni ko'radi."""

    template_name = "reports/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.request.company
        warehouses = self.request.user.allowed_warehouses()
        flow, flow_totals = dashboard.monthly_flow(company, warehouses)
        pending = dashboard.pending(company, warehouses)

        context.update(
            today=timezone.localdate(),
            kpis=dashboard.daily_kpis(company, warehouses),
            cards=dashboard.summary_cards(company, warehouses),
            flow=flow,
            flow_totals=flow_totals,
            activity=dashboard.recent_activity(warehouses),
            top_products=dashboard.top_products(company, warehouses),
            pending=pending,
            pending_total=sum(pending.values()),
            has_warehouses=warehouses.exists(),
        )
        return context


def _period(request):
    """GET dan davrni o'qiydi, berilmagan bo'lsa — oxirgi 30 kun."""
    today = timezone.localdate()
    date_to = parse_date(request.GET.get("to", "") or "") or today
    date_from = parse_date(request.GET.get("from", "") or "") or (date_to - timedelta(days=30))
    if date_from > date_to:
        date_from, date_to = date_to, date_from
    return date_from, date_to


def csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    # BOM — Excel o'zbek/rus harflarini to'g'ri ochishi uchun
    response.write("﻿")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(header)
    writer.writerows(rows)
    return response


class ReportView(PermissionMixin, TemplateView):
    """
    Bitta view barcha hisobotlar uchun: `report` nomiga qarab kerakli
    so'rov bajariladi. ?export=csv bo'lsa — jadval fayl bo'lib yuklanadi.
    """

    permission = "reports.view"
    template_name = "reports/report.html"

    REPORTS = {
        "stock": gettext_lazy("Qoldiqlar"),
        "turnover": gettext_lazy("Tovar aylanmasi"),
        "low": gettext_lazy("Kam qolgan tovarlar"),
        "staff": gettext_lazy("Xodimlar faolligi"),
    }

    def get(self, request, *args, **kwargs):
        report = kwargs.get("report", "stock")
        if report not in self.REPORTS:
            report = "stock"
        header, rows = self.build(report)

        if request.GET.get("export") == "csv":
            if not request.user.has_wms_perm("reports.export"):
                raise PermissionDenied
            filename = f"{report}_{date.today():%Y%m%d}.csv"
            return csv_response(filename, header, rows)

        date_from, date_to = _period(request)
        return self.render_to_response(
            self.get_context_data(
                report=report,
                reports=self.REPORTS,
                title=self.REPORTS[report],
                header=header,
                rows=rows,
                date_from=date_from,
                date_to=date_to,
                uses_period=report in ("turnover", "staff"),
                uses_warehouse=report == "stock",
                warehouses=request.user.allowed_warehouses(),
            )
        )

    def build(self, report):
        request = self.request
        company = request.company
        warehouses = request.user.allowed_warehouses()
        date_from, date_to = _period(request)

        if report == "stock":
            data = queries.stock_by_location(warehouses, request.GET.get("warehouse"))
            header = [_("Ombor"), _("Joy"), _("SKU"), _("Tovar"), _("Miqdor"), _("Birlik")]
            rows = [
                [
                    s.location.warehouse.name,
                    s.location.code,
                    s.product.sku,
                    s.product.name,
                    s.quantity.normalize(),
                    s.product.get_unit_display(),
                ]
                for s in data
            ]
        elif report == "turnover":
            data = queries.turnover(company, warehouses, date_from, date_to)
            header = [_("SKU"), _("Tovar"), _("Kirdi"), _("Chiqdi"), _("Amallar soni")]
            rows = [
                [
                    r["product__sku"],
                    r["product__name"],
                    r["qty_in"].normalize(),
                    (-r["qty_out"]).normalize(),
                    r["operations"],
                ]
                for r in data
            ]
        elif report == "low":
            data = queries.low_stock(company, warehouses)
            header = [_("SKU"), _("Tovar"), _("Qoldiq"), _("Minimal"), _("Yetishmaydi")]
            rows = [
                [
                    p.sku,
                    p.name,
                    p.total.normalize(),
                    p.min_stock.normalize(),
                    (p.min_stock - p.total).normalize(),
                ]
                for p in data
            ]
        else:
            data = queries.staff_activity(company, date_from, date_to)
            header = [_("Xodim"), _("Kirim"), _("Chiqim"), _("Ko'chirish"), _("Jami")]
            rows = [
                [
                    " ".join(
                        filter(None, [r["confirmed_by__first_name"], r["confirmed_by__last_name"]])
                    )
                    or r["confirmed_by__username"],
                    r["receipts"],
                    r["shipments"],
                    r["transfers"],
                    r["total"],
                ]
                for r in data
            ]
        return header, rows
