from decimal import Decimal
from typing import Self

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import (
    Avg,
    Count,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
)
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.core.utils import generate_unique_slug


class Category(TimeStampedModel):
    """
    Product Category model with hierarhical structure (parent-child).
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("category name"),
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("slug (URL)"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("description"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent category"),
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name=_("active"),
    )

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "name"],
                name="unique_category_per_parent",
            ),
        ]

    def clean(self) -> None:
        super().clean()

        if self.parent_id:
            if self.parent_id == self.pk:
                raise ValidationError({"parent": "Category cannot be its own parent."})

            ancestor = self.parent
            while ancestor is not None:
                if ancestor.pk == self.pk:
                    raise ValidationError(
                        {"parent": "Circular category dependence detected."}
                    )
                ancestor = ancestor.parent

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, fallback_slug="category")
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        full_path = [self.name]
        k: Category | None = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return " -> ".join(full_path[::-1])


class ProductQuerySet(models.QuerySet):
    """
    Custom QuerySet with filter business logic.
    """

    def active(self) -> Self:
        return self.filter(is_active=True)

    def with_rating(self) -> Self:
        """Annotate products with their average rating and review count."""
        return self.annotate(
            rating_avg=Coalesce(Avg("reviews__rating"), 0.0, output_field=FloatField()),
            rating_count=Count("reviews", distinct=True),
        )

    def with_sold(self) -> Self:
        """Annotate products with quantities from non-canceled orders."""
        from apps.orders.models import Order, OrderItem

        sold = (
            OrderItem.objects.filter(product=OuterRef("pk"))
            .exclude(order__status=Order.OrderStatus.CANCELLED)
            .values("product")
            .annotate(total=Sum("quantity"))
            .values("total")
        )
        return self.annotate(
            sold_qty=Coalesce(Subquery(sold, output_field=IntegerField()), 0),
        )

    def for_listing(self) -> Self:
        """Return the complete, query-efficient public catalogue queryset."""
        return (
            self.active()
            .select_related("category")
            .with_rating()
            .with_sold()
            .order_by("-created_at")
        )


class Product(TimeStampedModel):
    name = models.CharField(max_length=255, verbose_name=_("product name"))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_("slug (URL)"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("price"),
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("category"),
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/", blank=True, verbose_name=_("main image")
    )
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name=_("active")
    )
    stock = models.PositiveIntegerField(default=0, verbose_name=_("stock quantity"))

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "-created_at"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = generate_unique_slug(self, self.name, fallback_slug="product")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Canonical public API URL for this product."""
        from django.urls import reverse

        return reverse("products:product-detail", kwargs={"slug": self.slug})

    @property
    def is_in_stock(self) -> bool:
        """Helper method to check product availability."""
        return self.stock > 0
