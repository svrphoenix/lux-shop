from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.cart.serializers import (
    CartItemCreateSerializer,
    CartItemUpdateSerializer,
    CartMergeSerializer,
    CartSerializer,
)
from apps.cart.services import (
    CartItemNotFoundError,
    InsufficientStockError,
    ProductUnavailableError,
    add_item,
    clear_cart,
    get_cart_for_user,
    merge_guest_cart,
    remove_item,
    update_item,
)
from apps.users.models import User


class CartView(generics.GenericAPIView):
    """Retrieve or clear the authenticated user's persistent cart."""

    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        return Response(self.get_serializer(get_cart_for_user(user)).data)

    def delete(self, request: Request) -> Response:
        user = cast(User, request.user)
        return Response(self.get_serializer(clear_cart(user)).data)


class CartItemCreateView(generics.GenericAPIView):
    """Add a new product or increase its quantity in the authenticated user's cart."""

    serializer_class = CartItemCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, request.user)
        try:
            cart = add_item(user, **serializer.validated_data)
        except ProductUnavailableError as error:
            raise NotFound(str(error)) from error
        except InsufficientStockError as error:
            raise ValidationError({"quantity": [str(error)]}) from error
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )


class CartItemDetailView(generics.GenericAPIView):
    """Update line item quantity or remove a specific item from the user's cart."""

    serializer_class = CartItemUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CartItemUpdateSerializer,
        responses=CartSerializer,
        description="Set the cart line quantity to a positive value.",
    )
    def patch(self, request: Request, pk: int) -> Response:
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, request.user)
        try:
            cart = update_item(user, pk, serializer.validated_data["quantity"])
        except CartItemNotFoundError as error:
            raise NotFound(str(error)) from error
        except ProductUnavailableError as error:
            raise NotFound(str(error)) from error
        except InsufficientStockError as error:
            raise ValidationError({"quantity": [str(error)]}) from error
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )

    @extend_schema(
        request=None,
        responses=CartSerializer,
        description="Remove a line from the cart and return the updated cart.",
    )
    def delete(self, request: Request, pk: int) -> Response:
        user = cast(User, request.user)
        try:
            cart = remove_item(user, pk)
        except CartItemNotFoundError as error:
            raise NotFound(str(error)) from error
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )


class CartMergeView(generics.GenericAPIView):
    """Merge an anonymous guest cart with the authenticated user's persistent cart."""

    serializer_class = CartMergeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, request.user)
        cart = merge_guest_cart(
            user=user,
            guest_items=serializer.validated_data["items"],
        )
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )
