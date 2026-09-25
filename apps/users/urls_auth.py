from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import ChangePasswordView, LoginView, LogoutView, RegisterView

app_name = "auth"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
