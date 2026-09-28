from typing import cast

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
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request: Request, item_id: int) -> Response:
        serializer = CartItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = cast(User, request.user)
        try:
            cart = update_item(user, item_id, serializer.validated_data["quantity"])
        except CartItemNotFoundError as error:
            raise NotFound(str(error)) from error
        except ProductUnavailableError as error:
            raise NotFound(str(error)) from error
        except InsufficientStockError as error:
            raise ValidationError({"quantity": [str(error)]}) from error
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )

    def delete(self, request: Request, item_id: int) -> Response:
        user = cast(User, request.user)
        try:
            cart = remove_item(user, item_id)
        except CartItemNotFoundError as error:
            raise NotFound(str(error)) from error
        return Response(
            CartSerializer(cart, context=self.get_serializer_context()).data
        )


class CartMergeView(generics.GenericAPIView):
    """Merge a Next.js guest cart into the JWT-authenticated user's cart."""

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
