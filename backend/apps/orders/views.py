from typing import cast

from django.db.models import QuerySet
from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order
from apps.orders.serializers import CheckoutSerializer, OrderSerializer
from apps.orders.services import (
    CheckoutError,
    OrderCancellationError,
    cancel_order,
    create_order_from_cart,
)
from apps.users.models import User


class OrderListView(generics.ListAPIView):
    """List the authenticated customer's orders for the account page."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Order]:
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        user = cast(User, self.request.user)
        queryset = (
            Order.objects.filter(user=user)
            .select_related("payment")
            .prefetch_related("items__product")
            .order_by("-created_at")
        )
        order_status = self.request.query_params.get("status")
        if order_status is None:
            return queryset

        valid_statuses = {value for value, _ in Order.OrderStatus.choices}
        if order_status not in valid_statuses:
            raise ValidationError(
                {
                    "status": (
                        "Invalid status. Choose one of: "
                        f"{', '.join(sorted(valid_statuses))}."
                    )
                }
            )
        return queryset.filter(status=order_status)


class OrderDetailView(generics.RetrieveAPIView):
    """Retrieve detailed information about a specific order for the authenticated user."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "order_number"

    def get_queryset(self) -> QuerySet[Order]:
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        user = cast(User, self.request.user)
        return (
            Order.objects.filter(user=user)
            .select_related("payment")
            .prefetch_related("items__product")
        )


class OrderCancelView(APIView):
    """Cancel the authenticated customer's pending order."""

    permission_classes = [permissions.IsAuthenticated]

    # noinspection PyMethodMayBeStatic
    def post(self, request: Request, order_number: str) -> Response:
        user = cast(User, request.user)
        try:
            order = cancel_order(order_number, user=user)
        except Order.DoesNotExist as error:
            raise NotFound("Order not found.") from error
        except OrderCancellationError as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(OrderSerializer(order).data)


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
