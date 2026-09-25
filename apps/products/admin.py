from typing import cast

from django import forms
from django.contrib import admin

from apps.products.models import Category, Product


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "description", "parent")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and "parent" in self.fields:
            parent_field = cast(forms.ModelChoiceField, self.fields["parent"])
            parent_field.queryset = Category.objects.exclude(pk=self.instance.pk)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
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
            return *self.readonly_fields, "slug"
        return self.readonly_fields

    def get_prepopulated_fields(self, request, obj=None):
        if obj:
            return {}
        return {"slug": ["name"]}
