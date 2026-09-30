from typing import cast

from django.db.models import QuerySet
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orders.models import Order
from apps.orders.serializers import CheckoutSerializer, OrderSerializer
from apps.orders.services import CheckoutError, create_order_from_cart
from apps.users.models import User


class OrderListView(generics.ListAPIView):
    """List the authenticated customer's orders for the account page."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        user = cast(User, self.request.user)
        return (
            Order.objects.filter(user=user)
            .prefetch_related("items__product")
            .order_by("-created_at")
        )


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information about a specific order for the authenticated user."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self) -> QuerySet[Order]:
        user = cast(User, self.request.user)
        return Order.objects.filter(user=user).prefetch_related("items__product")


class CheckoutView(generics.GenericAPIView):
    """Atomically create an order from the authenticated user's cart."""

    serializer_class = CheckoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, self.request.user)
        try:
            order = create_order_from_cart(user, serializer.validated_data)
        except CheckoutError as error:
            raise ValidationError({"detail": str(error)}) from error
        return Response(
            OrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
