from django.contrib import admin
from django.db.models import Count, QuerySet
from django.db.models.base import Model
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from apps.cart.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ("product", "get_line_total", "created_at")

    @admin.display(description=_("sum"))
    def get_line_total(self, obj: CartItem):
        return obj.line_total

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ["user", "total_quantity", "total_amount", "updated_at"]
    # noinspection PyUnresolvedReferences
    search_fields = ["user__username", "user__email"]
    list_select_related = ["user"]
    readonly_fields = ["user", "get_total_quantity", "get_total_amount"]
    fields = ["user", "get_total_quantity", "get_total_amount"]
    inlines = [CartItemInline]

    @admin.display(description=_("total quantity"))
    def get_total_quantity(self, obj: Cart) -> int:
        return obj.total_quantity

    @admin.display(description=_("total amount"))
    def get_total_amount(self, obj: Cart) -> str:
        return f"{obj.total_amount:.2f} ₴"

    def get_queryset(self, request: HttpRequest) -> QuerySet[Model]:
        """Filter out empty carts so only active carts with items are displayed."""
        return (
            super()
            .get_queryset(request)
            .annotate(items_count=Count("items"))
            .filter(items_count__gt=0)
        )

    def has_add_permission(self, request):
        return False
