from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.products.models import Category, Product

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "parent")
        read_only_fields = fields


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    rating_avg = serializers.FloatField(read_only=True)
    rating_count = serializers.IntegerField(read_only=True)
    sold_qty = serializers.IntegerField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "category",
            "image",
            "stock",
            "is_in_stock",
            "rating_avg",
            "rating_count",
            "sold_qty",
            "created_at",
        ]
        read_only_fields = fields


class ProductDetailSerializer(ProductSerializer):
    can_review = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = [*ProductSerializer.Meta.fields, "can_review"]
        read_only_fields = fields

    def get_can_review(self, product: Product) -> bool:
        request = self.context.get("request")
        if request is None:
            return False

        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return False

        from apps.reviews.services import can_review

        return can_review(user, product)
