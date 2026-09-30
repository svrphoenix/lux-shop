from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Cart(TimeStampedModel):
    """Persistent shopping cart for one authenticated customer."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name=_("user"),
    )

    class Meta:
        verbose_name = _("cart")
        verbose_name_plural = _("carts")

    def __str__(self) -> str:
        return f"Cart for {self.user}"

    @property
    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items.all()), Decimal("0.00"))


class CartItem(TimeStampedModel):
    """A product and its requested quantity in a cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("cart"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name=_("product"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_("quantity"),
    )

    class Meta:
        verbose_name = _("cart item")
        verbose_name_plural = _("cart items")
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_product_per_cart"
            ),
            models.CheckConstraint(
                name="cart_item_quantity_gt_zero",
                condition=models.Q(quantity__gt=0),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self) -> Decimal:
        return self.product.price * self.quantity

    def clean(self) -> None:
        super().clean()
        if self.product_id and self.quantity and self.quantity > self.product.stock:
            raise ValidationError(
                {
                    "quantity": _("Quantity cannot exceed available stock (%(stock)d).")
                    % {"stock": self.product.stock}
                }
            )
