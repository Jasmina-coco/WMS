from django.contrib import admin

from apps.core.admin import ReadOnlyAdmin, ReadOnlyInline

from .models import Attachment, Document, DocumentLine, StockCount, StockCountLine


class DocumentLineInline(ReadOnlyInline):
    model = DocumentLine
    fields = ["product", "location", "to_location", "quantity"]


class AttachmentInline(ReadOnlyInline):
    model = Attachment
    fields = ["original_name", "file", "uploaded_by", "created_at"]


@admin.register(Document)
class DocumentAdmin(ReadOnlyAdmin):
    list_display = [
        "number",
        "kind",
        "status",
        "warehouse",
        "partner",
        "created_by",
        "created_at",
        "company",
    ]
    list_filter = ["company", "kind", "status"]
    search_fields = ["number", "partner"]
    date_hierarchy = "created_at"
    list_select_related = ["warehouse", "created_by", "company"]
    inlines = [DocumentLineInline, AttachmentInline]


class StockCountLineInline(ReadOnlyInline):
    model = StockCountLine
    fields = ["product", "location", "system_quantity", "counted_quantity"]


@admin.register(StockCount)
class StockCountAdmin(ReadOnlyAdmin):
    list_display = ["number", "warehouse", "zone", "status", "created_by", "created_at", "company"]
    list_filter = ["company", "status"]
    inlines = [StockCountLineInline]
