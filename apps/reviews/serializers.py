from rest_framework import serializers

from apps.reviews.models import Review
from apps.users.models import User


class ReviewAuthorSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(source="profile.avatar", read_only=True)

    class Meta:
        model = User
        fields = ("username", "avatar")
        read_only_fields = fields


class ReviewSerializer(serializers.ModelSerializer):
    author = ReviewAuthorSerializer(source="user", read_only=True)

    class Meta:
        model = Review
        fields = (
            "id",
            "rating",
            "comment",
            "author",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")
