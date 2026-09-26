from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.serializers import BaseSerializer

from apps.products.models import Product
from apps.reviews.models import Review
from apps.reviews.serializers import ReviewSerializer
from apps.reviews.services import can_review


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductReviewListCreateView(generics.ListCreateAPIView):
    """List product reviews or add the purchaser's one permitted review."""

    serializer_class = ReviewSerializer
    pagination_class = ReviewPagination

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @cached_property
    def product(self) -> Product:
        return get_object_or_404(
            Product.objects.active(), slug=self.kwargs["product_slug"]
        )

    def get_queryset(self):
        return (
            Review.objects.filter(product=self.product)
            .select_related("user", "user__profile")
            .order_by("-created_at")
        )

    def perform_create(self, serializer: BaseSerializer) -> None:
        product = self.product
        if not can_review(self.request.user, product):
            raise PermissionDenied(
                "You may leave one review only after purchasing this product."
            )

        try:
            with transaction.atomic():
                serializer.save(user=self.request.user, product=product)
        except IntegrityError as error:
            raise ValidationError(
                {"detail": "You have already reviewed this product."}
            ) from error
