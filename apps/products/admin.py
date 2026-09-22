# Register your models here.
from django.contrib import admin

from apps.products.models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "description"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "price", "stock", "is_active"]
    list_filter = ["is_active", "category"]
    list_editable = ["price", "stock", "is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}

    fields = [
        "name",
        "slug",
        "category",
        "description",
        "price",
        "stock",
        "image",
        "is_active",
    ]

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "slug" and field is not None:
            field.widget.attrs["readonly"] = True
        return field

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("slug",)
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj:
            return {}
        return {"slug": ["name"]}
