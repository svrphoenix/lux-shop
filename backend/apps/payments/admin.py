from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "method",
        "status",
        "amount",
        "currency",
        "is_mock",
        "created_at",
    )
    list_filter = ("method", "status", "is_mock", "created_at")
    search_fields = ("order__order_number", "transaction_reference")
    readonly_fields = ("created_at", "updated_at")
