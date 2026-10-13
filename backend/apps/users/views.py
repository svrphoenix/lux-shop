from typing import TYPE_CHECKING, Any, cast
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.files.uploadedfile import UploadedFile
from django.db import DatabaseError
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.emails import get_request_language
from apps.users.notifications import send_password_reset_email
from apps.users.serializers import (
    AvatarUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class UserProfileView(RetrieveUpdateAPIView):
    """
    Endpoint for retrieving and updating the authenticated user's profile
    (GET/PUT/PATCH /api/v1/users/me/).
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user


class UserAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    # noinspection PyMethodMayBeStatic
    def patch(self, request: Request) -> Response:
        serializer = AvatarUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = cast("User", request.user)
        profile = user.profile
        previous_avatar_name = profile.avatar.name

        avatar_file = serializer.validated_data.get("avatar")

        if isinstance(avatar_file, UploadedFile):
            # avatar_file.name or "avatar.png" гарантує тип 'str' для IDE
            file_name = avatar_file.name or "avatar.png"
            profile.avatar.save(file_name, avatar_file, save=False)
            profile.avatar_preset = ""
        else:
            # setattr обходить хибне попередження PyCharm "Property 'name' cannot be set"
            profile.avatar.name = ""
            profile.avatar_preset = str(
                serializer.validated_data.get("avatar_preset", "")
            )

        new_avatar_name = profile.avatar.name
        try:
            profile.save(update_fields=["avatar", "avatar_preset", "updated_at"])
        except DatabaseError:
            if new_avatar_name and new_avatar_name != previous_avatar_name:
                profile.avatar.storage.delete(new_avatar_name)
            raise

        if previous_avatar_name and previous_avatar_name != new_avatar_name:
            profile.avatar.storage.delete(previous_avatar_name)

        return Response(UserSerializer(user).data)

    # noinspection PyMethodMayBeStatic
    def delete(self, request: Request) -> Response:
        user = cast("User", request.user)
        profile = user.profile
        previous_avatar_name = profile.avatar.name

        profile.avatar.name = ""
        profile.avatar_preset = ""
        profile.save(update_fields=["avatar", "avatar_preset", "updated_at"])

        if previous_avatar_name:
            profile.avatar.storage.delete(previous_avatar_name)

        return Response(UserSerializer(user).data)


class LoginView(TokenObtainPairView):
    """
    Custom authentication endpoint (/api/v1/auth/login/).
    Returns an extended user info and tokens.
    """

    serializer_class = LoginSerializer


class RegisterView(generics.CreateAPIView):
    """
    Endpoint for new user registration (/api/v1/auth/register/).
    Successful registration returns user data and authorization tokens.
    """

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = cast(Any, RefreshToken.for_user(user))
        user_data = UserSerializer(user, context={"request": request}).data

        response_data: dict[str, Any] = {
            "user": user_data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class LogoutView(generics.GenericAPIView):
    """
    Endpoint for logout (/api/v1/auth/logout/).
    Adds the provided refresh token to the blacklist.
    """

    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {"detail": "You have successfully logged out."},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(generics.GenericAPIView):
    """
    Endpoint for authenticated users to change their password
    (POST /api/v1/auth/change-password/).
    """

    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"detail": "Password has been successfully updated."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(generics.GenericAPIView):
    """Email a single-use password reset link without revealing account existence."""

    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            is_active=True,
        ).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/"
                f"?{urlencode({'uid': uid, 'token': token})}"
            )
            send_password_reset_email(
                user=user,
                reset_url=reset_url,
                lang=get_request_language(request),
            )

        return Response(
            {
                "detail": (
                    "If an account exists for this email, password reset "
                    "instructions will be sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """Set a new password using a valid, single-use reset token."""

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "password_reset"

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Your password has been reset. You can now sign in."},
            status=status.HTTP_200_OK,
        )
