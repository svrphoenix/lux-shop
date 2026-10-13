from django.urls import path

from apps.users.views import UserAvatarView, UserProfileView

app_name = "users"

urlpatterns = [
    path("users/me/", UserProfileView.as_view(), name="user-profile"),
    path("users/me/avatar/", UserAvatarView.as_view(), name="user-avatar"),
]
