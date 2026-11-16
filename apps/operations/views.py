from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.core.mixins import CompanyRequiredMixin
from apps.inventory.services import StockError

from . import services
from .forms import (
    AttachmentForm,
    CountExtraLineForm,
    DocumentForm,
    LineFormSet,
    StockCountForm,
)
from .models import Attachment, Document, StockCount, StockCountLine

PERM_PREFIX = {"receipt": "receipts", "shipment": "shipments", "transfer": "transfers"}


class DocumentKindMixin(CompanyRequiredMixin):
    """
    URL dagi hujjat turini (receipt/shipment/transfer) o'qiydi va
    kerakli ruxsatni tekshiradi: `receipts.view`, `shipments.create` va h.k.
    """

    action = "view"

    def dispatch(self, request, *args, **kwargs):
        self.kind = kwargs["kind"]
        if self.kind not in PERM_PREFIX:
            raise Http404
        if request.user.is_authenticated and not self.can(self.action):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def can(self, action):
        return self.request.user.has_wms_perm(f"{PERM_PREFIX[self.kind]}.{action}")

    def documents(self):
        return Document.objects.for_company(self.request.company).filter(
            kind=self.kind, warehouse__in=self.request.user.allowed_warehouses()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kind"] = self.kind
        context["kind_label"] = Document.Kind(self.kind).label
        return context


class DocumentListView(DocumentKindMixin, ListView):
    template_name = "operations/document_list.html"
    context_object_name = "documents"
    paginate_by = 30

    def get_queryset(self):
        qs = self.documents().select_related("warehouse", "dest_warehouse", "created_by")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(Q(number__icontains=search) | Q(partner__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Document.Status.choices
        context["can_create"] = self.can("create")
        return context


class DocumentFormView(DocumentKindMixin, TemplateView):
    """Yaratish va tahrirlash bitta view'da: sarlavha formasi + qatorlar formset."""

    template_name = "operations/document_form.html"
    action = "create"

    def get_document(self):
        pk = self.kwargs.get("pk")
        if pk is None:
            return Document(kind=self.kind, company=self.request.company)
        document = get_object_or_404(self.documents(), pk=pk)
        if not document.is_editable:
            raise PermissionDenied
        return document

    def build_forms(self, data=None):
        document = self.get_document()
        form = DocumentForm(
            data,
            instance=document,
            company=self.request.company,
            kind=self.kind,
            user=self.request.user,
        )
        formset = LineFormSet(
            data,
            instance=document,
            prefix="lines",
            company=self.request.company,
            user=self.request.user,
            kind=self.kind,
        )
        return form, formset

    def get(self, request, *args, **kwargs):
        form, formset = self.build_forms()
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    def post(self, request, *args, **kwargs):
        form, formset = self.build_forms(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                document = form.save(commit=False)
                if not document.pk:
                    document.created_by = request.user
                document.save()
                formset.instance = document
                formset.save()
            messages.success(request, _("Hujjat saqlandi."))
            return redirect("operations:detail", kind=self.kind, pk=document.pk)
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class DocumentDetailView(DocumentKindMixin, DetailView):
    template_name = "operations/document_detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return self.documents().select_related(
            "warehouse", "dest_warehouse", "created_by", "confirmed_by", "cancelled_by"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lines"] = self.object.lines.select_related("product", "location", "to_location")
        context["attachments"] = self.object.attachments.select_related("uploaded_by")
        context["attachment_form"] = AttachmentForm()
        context["can_upload"] = self.can("create") and self.object.status != "cancelled"
        context["can_edit"] = self.object.is_editable and self.can("create")
        context["can_confirm"] = self.object.status in ("draft", "picking") and self.can("confirm")
        context["can_cancel"] = (
            self.object.status in ("draft", "picking")
            and self.kind != "transfer"
            and self.can("cancel")
        )
        return context


class DocumentPrintView(DocumentDetailView):
    """Chiqim uchun terish varag'i, qolganlari uchun oddiy chop etish ko'rinishi."""

    template_name = "operations/document_print.html"


class DocumentActionView(DocumentKindMixin, View):
    """Tasdiqlash / terish / jo'natish / bekor qilish — faqat POST."""

    def dispatch(self, request, *args, **kwargs):
        self.action = "cancel" if kwargs["action"] == "cancel" else "confirm"
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, kind, pk, action):
        document = get_object_or_404(self.documents(), pk=pk)
        try:
            if action == "cancel":
                services.cancel(document, request.user)
                messages.success(request, _("Hujjat bekor qilindi."))
            else:
                services.confirm(document, request.user)
                messages.success(request, _("Bajarildi."))
        except StockError as error:
            messages.error(request, str(error))
        return redirect("operations:detail", kind=kind, pk=pk)


class AttachmentUploadView(DocumentKindMixin, View):
    action = "create"

    def post(self, request, kind, pk):
        document = get_object_or_404(self.documents(), pk=pk)
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.company = request.company
            attachment.document = document
            attachment.uploaded_by = request.user
            attachment.original_name = request.FILES["file"].name[:255]
            attachment.save()
            messages.success(request, _("Fayl yuklandi."))
        else:
            for error in form.errors.get("file", []):
                messages.error(request, error)
        return redirect("operations:detail", kind=kind, pk=pk)


class AttachmentOpenView(DocumentKindMixin, View):
    """
    Faylni to'g'ridan-to'g'ri havola bilan bermaymiz: avval foydalanuvchi shu
    hujjatni ko'rishga haqli ekanini tekshiramiz, keyin S3 ning vaqtinchalik
    havolasiga yo'naltiramiz.
    """

    def get(self, request, kind, pk, attachment_id):
        document = get_object_or_404(self.documents(), pk=pk)
        attachment = get_object_or_404(Attachment, pk=attachment_id, document=document)
        return redirect(attachment.file.url)


# --- Inventarizatsiya ---


class CountMixin(CompanyRequiredMixin):
    permission = "counts.view"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.has_wms_perm(self.permission):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def counts(self):
        return StockCount.objects.for_company(self.request.company).filter(
            warehouse__in=self.request.user.allowed_warehouses()
        )


class CountListView(CountMixin, ListView):
    template_name = "operations/count_list.html"
    context_object_name = "counts"
    paginate_by = 30

    def get_queryset(self):
        return self.counts().select_related("warehouse", "created_by")


class CountCreateView(CountMixin, TemplateView):
    permission = "counts.do"
    template_name = "form_page.html"

    def get(self, request):
        form = StockCountForm(user=request.user)
        return self.render_to_response({"form": form, "title": _("Yangi inventarizatsiya")})

    def post(self, request):
        form = StockCountForm(request.POST, user=request.user)
        if form.is_valid():
            count = services.open_count(
                company=request.company,
                warehouse=form.cleaned_data["warehouse"],
                zone=form.cleaned_data["zone"],
                user=request.user,
            )
            return redirect("operations:count_detail", pk=count.pk)
        return self.render_to_response({"form": form, "title": _("Yangi inventarizatsiya")})


class CountDetailView(CountMixin, DetailView):
    template_name = "operations/count_detail.html"
    context_object_name = "count"

    def get_queryset(self):
        return self.counts().select_related("warehouse", "created_by", "finished_by")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lines"] = self.object.lines.select_related("product", "location")
        context["extra_form"] = CountExtraLineForm(count=self.object)
        context["is_open"] = self.object.status == StockCount.Status.OPEN
        return context

    def post(self, request, pk):
        """Sanalgan miqdorlarni saqlash, yangi qator qo'shish yoki sanoqni yakunlash."""
        count = get_object_or_404(self.counts(), pk=pk)
        if count.status != StockCount.Status.OPEN:
            raise PermissionDenied
        action = request.POST.get("action")

        if action == "finish":
            if not request.user.has_wms_perm("counts.finish"):
                raise PermissionDenied
            try:
                services.finish_count(count, request.user)
                messages.success(request, _("Inventarizatsiya yakunlandi, qoldiqlar tuzatildi."))
            except StockError as error:
                messages.error(request, str(error))

        elif action == "add_line":
            if not request.user.has_wms_perm("counts.do"):
                raise PermissionDenied
            form = CountExtraLineForm(request.POST, count=count)
            if form.is_valid():
                StockCountLine.objects.update_or_create(
                    count=count,
                    product=form.cleaned_data["product"],
                    location=form.cleaned_data["location"],
                    defaults={
                        "company": count.company,
                        "system_quantity": 0,
                        "counted_quantity": form.cleaned_data["counted_quantity"],
                    },
                )
                messages.success(request, _("Qator qo'shildi."))
            else:
                messages.error(request, _("Qator ma'lumotlari noto'g'ri."))

        else:
            if not request.user.has_wms_perm("counts.do"):
                raise PermissionDenied
            self._save_counted(request, count)
            messages.success(request, _("Saqlandi."))

        return redirect(reverse("operations:count_detail", args=[count.pk]))

    def _save_counted(self, request, count):
        # Inputlar nomi: counted_<qator id>. Bo'sh qoldirilsa — hali sanalmagan
        for line in count.lines.all():
            raw = request.POST.get(f"counted_{line.pk}", "").strip().replace(",", ".")
            if raw == "":
                value = None
            else:
                try:
                    value = max(Decimal(raw), Decimal("0"))
                except InvalidOperation:
                    continue
            if value != line.counted_quantity:
                line.counted_quantity = value
                line.save(update_fields=["counted_quantity", "updated_at"])
