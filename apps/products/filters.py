import django_filters as filters
from django.db.models import Q, QuerySet

from apps.products.models import Category, Product


class StableOrderingFilter(filters.OrderingFilter):
    """Keep ordering deterministic when several products have the same value."""

    def filter(self, qs: QuerySet, value: list[str] | None) -> QuerySet:
        qs = super().filter(qs, value)
        if value:
            return qs.order_by(*qs.query.order_by, "-pk")
        return qs


class ProductFilter(filters.FilterSet):
    """Public catalogue filters shared by every product-list consumer."""

    search = filters.CharFilter(method="filter_search")
    category = filters.ModelMultipleChoiceFilter(
        queryset=Category.objects.all(),
        to_field_name="slug",
        method="filter_category",
    )
    min_price = filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = filters.BooleanFilter(method="filter_in_stock")
    ordering = StableOrderingFilter(
        fields=(
            ("price", "price"),
            ("created_at", "created_at"),
            ("rating_avg", "rating"),
            ("sold_qty", "popularity"),
        ),
    )

    class Meta:
        model = Product
        fields: list[str] = []

    @classmethod
    def filter_search(cls, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

    @classmethod
    def filter_category(
        cls, queryset: QuerySet, _name: str, value: QuerySet[Category]
    ) -> QuerySet:
        if not value:
            return queryset
        return queryset.filter(Q(category__in=value) | Q(category__parent__in=value))

    @classmethod
    def filter_in_stock(cls, queryset: QuerySet, _name: str, value: bool) -> QuerySet:
        if not value:
            return queryset
        return queryset.filter(stock__gt=0)
