# Register your models here.
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]
    fields = ["product", "price", "quantity", "get_cost"]
    readonly_fields = ["get_cost"]

    @admin.display(description=_("cost"))
    def get_cost(self, obj: OrderItem) -> str:
        if obj.pk:
            return f"{obj.cost:.2f}"
        return "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number",
        "get_full_name",
        "customer_email",
        "status",
        "total_amount",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "order_number",
        "customer_email",
        "customer_first_name",
        "customer_last_name",
        "customer_phone",
    ]
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]

    fieldsets = (
        (
            _("Order Details"),
            {
                "fields": (
                    "order_number",
                    "user",
                    "status",
                    "total_amount",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            _("Customer Snapshot"),
            {
                "fields": (
                    "customer_first_name",
                    "customer_last_name",
                    "customer_email",
                    "customer_phone",
                )
            },
        ),
        (
            _("Shipping Information"),
            {
                "fields": ("shipping_address",),
            },
        ),
    )

    @admin.display(description=_("full name"), ordering="customer_first_name")
    def get_full_name(self, obj: Order) -> str:
        """Returns customer's full name and enables sorting by name."""
        name = f"{obj.customer_first_name} {obj.customer_last_name}".strip()
        return name if name else "-"

    def get_readonly_fields(self, request, obj=None):
        readonly = ["order_number", "total_amount", "created_at", "updated_at"]

        if obj:
            readonly.extend(
                [
                    "user",
                    "customer_first_name",
                    "customer_last_name",
                    "customer_email",
                    "customer_phone",
                ]
            )

        return readonly
