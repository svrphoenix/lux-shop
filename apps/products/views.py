from django.db.models import QuerySet
from rest_framework import generics, permissions
from rest_framework.pagination import PageNumberPagination

from apps.products.filters import ProductFilter
from apps.products.models import Category, Product
from apps.products.serializers import (
    CategorySerializer,
    ProductDetailSerializer,
    ProductSerializer,
)


class ProductPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 100


class CategoryListView(generics.ListAPIView):
    """List top-level product categories."""

    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self) -> QuerySet[Category]:
        return Category.objects.filter(parent__isnull=True, is_active=True)


class ProductListView(generics.ListAPIView):
    """Public, paginated product list with search, filters, and ordering."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProductPagination
    filterset_class = ProductFilter

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.for_listing()


class ProductDetailView(generics.RetrieveAPIView):
    """Public product details; inactive products intentionally return 404."""

    serializer_class = ProductDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Product]:
        return Product.objects.for_listing()
