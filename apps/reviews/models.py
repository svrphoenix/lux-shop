# Create your models here.
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.products.models import Product


class Review(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("product"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("user"),
    )
    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message="The rating cannot be less than 1."),
            MaxValueValidator(5, message="The rating cannot be more than 5."),
        ],
        verbose_name=_("rating"),
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_("comment"),
    )

    class Meta:
        verbose_name = _("review")
        verbose_name_plural = _("reviews")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"], name="unique_user_product_review"
            )
        ]

    def __str__(self) -> str:
        return f"Review by {self.user} for {self.product} ({self.rating}/5)"
