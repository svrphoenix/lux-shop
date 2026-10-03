from django.urls import path

from apps.users.views import UserProfileView

app_name = "users"

urlpatterns = [
    path("users/me/", UserProfileView.as_view(), name="user-profile"),
]
