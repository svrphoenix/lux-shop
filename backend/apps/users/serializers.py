from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Profile

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for User Profile."""

    class Meta:
        model = Profile
        fields = (
            "phone_number",
            "address",
            "birth_day",
            "avatar",
        )
        extra_kwargs = {
            "phone_number": {"required": False, "allow_blank": True},
            "address": {"required": False, "allow_blank": True},
            "birth_day": {"required": False, "allow_null": True},
            "avatar": {"required": False, "allow_null": True},
        }


class UserSerializer(serializers.ModelSerializer):
    """
    Main user serializer with inline profile serializer.
    """

    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",
        )
        read_only_fields = ("id", "username")

    @transaction.atomic
    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        """
        Atomically updates the User and nested Profile instances.
        """
        profile_data = validated_data.pop("profile", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile, _ = Profile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
            instance.profile = profile

        return instance


class LoginSerializer(TokenObtainPairSerializer):
    """
    Custom authorization serializer that returns tokens
    and a custom user view via UserSerializer
    """

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        data: dict[str, Any] = super().validate(attrs)
        data["user"] = UserSerializer(self.user, context=self.context).data

        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for new useer registration."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        )

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords don't match."}
            )
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        # noinspection PyUnresolvedReferences
        user: User = User.objects.create_user(**validated_data)
        return user


class LogoutSerializer(serializers.Serializer):
    """Serializer for adding refresh-token to blacklist."""

    refresh = serializers.CharField()

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        refresh_token = attrs["refresh"]
        try:
            # noinspection PyArgumentList
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"refresh": "Token is not valid."}
            ) from None
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for updating the authenticated user's password."""

    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        user = self.context["request"].user

        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError(
                {"old_password": "Current password is incorrect."}
            )

        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )

        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": "New password cannot be identical to the current password."
                }
            )

        return attrs

    def save(self, **kwargs: Any) -> Any:
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
