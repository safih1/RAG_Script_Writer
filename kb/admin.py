from django.contrib import admin
from .models import Source, Entity, Document
from .tagging import tag_document, build_patterns



@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "actor_type", "language", "active", "feed_url")
    list_editable = ("tier", "active")


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("name", "kind")
    list_filter = ("kind",)
    search_fields = ("name", "aliases")


@admin.action(description="Mark selected as reviewed")
def mark_reviewed(modeladmin, request, queryset):
    queryset.update(reviewed=True)


@admin.action(description="Re-run automatic tagging")
def retag(modeladmin, request, queryset):
    for d in queryset:
        tag_document(d)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published", "doc_type", "reviewed")
    list_filter = ("source", "doc_type", "reviewed", "entities")
    search_fields = ("title", "full_text")
    filter_horizontal = ("entities",)
    actions = [mark_reviewed, retag]
    date_hierarchy = "published"

@admin.action(description="Re-run automatic tagging")
def retag(modeladmin, request, queryset):
    patterns = build_patterns()
    for d in queryset:
        if not d.reviewed:
            d.entities.clear()
        tag_document(d, patterns)