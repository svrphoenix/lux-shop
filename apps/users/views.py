from typing import Any, cast

from rest_framework import generics, permissions, status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
)


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
