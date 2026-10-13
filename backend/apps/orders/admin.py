from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem
from .services import OrderCancellationError, cancel_order


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "user",
            "customer_email",
            "customer_first_name",
            "customer_last_name",
            "customer_phone",
            "status",
            "total_amount",
            "shipping_address",
        ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        status_field = self.fields.get("status")

        if isinstance(status_field, forms.ChoiceField):
            if self.instance.pk and self.instance.status == Order.OrderStatus.CANCELLED:
                status_field.disabled = True
            else:
                choices = [
                    choice
                    for choice in Order.OrderStatus.choices
                    if choice[0] != Order.OrderStatus.CANCELLED
                ]
                status_field.choices = choices

    def clean_status(self) -> str:
        status = self.cleaned_data["status"]
        if not self.instance.pk:
            return status

        status_order = [
            Order.OrderStatus.PENDING,
            Order.OrderStatus.PAID,
            Order.OrderStatus.SHIPPED,
            Order.OrderStatus.DELIVERED,
            Order.OrderStatus.CANCELLED,
        ]
        current_status = self.instance.status
        if status_order.index(status) < status_order.index(current_status):
            raise ValidationError(_("Order status cannot move backwards."))
        return status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]
    fields = ["product", "price", "quantity", "get_cost"]
    readonly_fields = ["get_cost"]

    def has_add_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_change_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return obj is None

    @admin.display(description=_("cost"))
    def get_cost(self, obj: OrderItem) -> str:
        if obj.pk:
            return f"{obj.cost:.2f}"
        return "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    actions = ["cancel_pending_orders"]
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

    @admin.action(description=_("Cancel selected pending orders and restore stock"))
    def cancel_pending_orders(self, request, queryset) -> None:
        cancelled_count = 0
        skipped_count = 0
        for order_number in queryset.values_list("order_number", flat=True).iterator():
            try:
                cancel_order(order_number)
            except OrderCancellationError:
                skipped_count += 1
            else:
                cancelled_count += 1

        if cancelled_count:
            self.message_user(
                request,
                _("%(count)d order(s) cancelled and stock restored.")
                % {"count": cancelled_count},
                level=messages.SUCCESS,
            )
        if skipped_count:
            self.message_user(
                request,
                _("%(count)d order(s) skipped because they are not pending.")
                % {"count": skipped_count},
                level=messages.WARNING,
            )

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
