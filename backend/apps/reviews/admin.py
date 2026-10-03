# Register your models here.
from django.contrib import admin

from .models import Review


# noinspection PyUnresolvedReferences
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating"]
    search_fields = ["product__name", "user__username", "user__email"]
    autocomplete_fields = ["product", "user"]
    readonly_fields = ["created_at", "updated_at"]
