import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class PaymentMethod(models.TextChoices):
    CARD = "card", _("Card")
    CASH_ON_DELIVERY = "cash_on_delivery", _("Cash on delivery")


class PaymentStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    SUCCEEDED = "succeeded", _("Succeeded")
    FAILED = "failed", _("Failed")


class Payment(TimeStampedModel):
    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment",
        verbose_name=_("order"),
    )
    method = models.CharField(
        max_length=32,
        choices=PaymentMethod.choices,
        verbose_name=_("payment method"),
    )
    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        verbose_name=_("payment status"),
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("amount"),
    )
    currency = models.CharField(max_length=3, default="UAH", verbose_name=_("currency"))
    transaction_reference = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_("transaction reference"),
    )
    is_mock = models.BooleanField(default=True, verbose_name=_("simulated payment"))

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_method_display()} for order #{self.order.order_number}"

    @staticmethod
    def create_mock_reference() -> str:
        return f"mock_{uuid.uuid4().hex}"
