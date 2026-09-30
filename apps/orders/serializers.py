from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.models import Product


class OrderProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "slug", "image")
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderProductSerializer(read_only=True)
    cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "price", "quantity", "cost")
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "order_number",
            "status",
            "customer_email",
            "customer_first_name",
            "customer_last_name",
            "customer_phone",
            "shipping_address",
            "total_amount",
            "items",
            "created_at",
        )
        read_only_fields = fields


class CheckoutSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=301)
    phone = serializers.CharField(max_length=32)
    city = serializers.CharField(max_length=150)
    address = serializers.CharField()

    # noinspection PyMethodMayBeStatic
    def validate_full_name(self, value: str) -> str:
        name_parts = value.split(maxsplit=1)
        if len(name_parts) < 2:
            raise serializers.ValidationError("Enter both first name and last name.")
        if any(len(part) > 150 for part in name_parts):
            raise serializers.ValidationError(
                "First name and last name must each be at most 150 characters."
            )
        return " ".join(name_parts)
