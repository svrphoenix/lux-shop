# Create your models here.
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import F, Sum
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Order(TimeStampedModel):
    class OrderStatus(models.TextChoices):
        PENDING = "pending", _("pending")
        PAID = "paid", _("paid")
        SHIPPED = "shipped", _("shipped")
        DELIVERED = "delivered", _("delivered")
        CANCELLED = "cancelled", _("cancelled")

    order_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        verbose_name=_("order number"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name=_("user account"),
    )
    customer_email = models.EmailField(
        verbose_name=_("customer email"),
    )
    customer_first_name = models.CharField(
        max_length=150,
        verbose_name=_("customer first name"),
    )
    customer_last_name = models.CharField(
        max_length=150,
        verbose_name=_("customer last name"),
    )
    customer_phone = models.CharField(
        max_length=32,
        verbose_name=_("customer phone number"),
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name=_("status"),
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name=_("total amount"),
    )
    shipping_address = models.TextField(verbose_name=_("shipping address"))

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    @classmethod
    def _generate_order_number(cls) -> str:
        """Generates a secure, unique, auto-incrementing order number (starting from 100001)."""
        with transaction.atomic():
            last_order: Order | None = (
                Order.objects.select_for_update().order_by("-id").first()
            )
            if (
                last_order
                and last_order.order_number
                and last_order.order_number.isdigit()
            ):
                return str(int(last_order.order_number) + 1)
            return "100001"

    def recalculate_total(self) -> None:
        """
        Calculates the total order amount based on the saved OrderItems and updates
        the total_amount field in the DB without calling a full save().
        """
        aggregate_result = self.items.aggregate(
            total=Sum(F("price") * F("quantity"), default=Decimal("0.00"))
        )
        new_total: Decimal = aggregate_result["total"]

        if self.total_amount != new_total:
            self.total_amount = new_total
            self.save(update_fields=["total_amount", "updated_at"])

    def save(self, *args, **kwargs) -> None:
        if not self.order_number:
            self.order_number = self._generate_order_number()

        if self.user:
            if not self.customer_email:
                self.customer_email = self.user.email
            if not self.customer_first_name:
                self.customer_first_name = self.user.first_name
            if not self.customer_last_name:
                self.customer_last_name = self.user.last_name

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Order #{self.order_number} ({self.customer_email})"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("order"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name=_("product"),
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("price at purchase"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("quantity"),
    )

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"],
                name="unique_product_per_order",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.quantity} x {self.product.name} (Order #{self.order.order_number})"
        )

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.order.recalculate_total()

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        order = self.order
        deleted_count, deleted_objects = super().delete(*args, **kwargs)
        order.recalculate_total()
        return deleted_count, deleted_objects

    @property
    def cost(self) -> Decimal:
        return self.price * self.quantity
