from decimal import Decimal

from rest_framework import serializers

from apps.cart.models import Cart, CartItem
from apps.products.models import Product


class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "slug", "price", "image", "stock", "is_active")
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "line_total")
        read_only_fields = fields

    @classmethod
    def get_line_total(cls, item: CartItem) -> Decimal:
        return item.line_total


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_quantity = serializers.IntegerField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = ("items", "total_quantity", "total_amount", "updated_at")
        read_only_fields = fields


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, default=1)


class CartItemUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0)


class GuestCartItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CartMergeSerializer(serializers.Serializer):
    items = GuestCartItemSerializer(many=True)
