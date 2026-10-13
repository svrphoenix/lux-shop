from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from apps.users.models import Profile, User


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _("profile info")
    fk_name = "user"
    fields = ("phone_number", "address", "birth_day", "avatar")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    inlines = (ProfileInline,)

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "get_phone_number",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "profile__phone_number",
    )

    list_select_related = ("profile",)

    @admin.display(description=_("phone number"), ordering="profile__phone_number")
    def get_phone_number(self, obj: User) -> str:
        """Retrieves the phone number from the linked profile."""
        if hasattr(obj, "profile") and obj.profile.phone_number:
            return obj.profile.phone_number
        return "-"

    def save_model(self, request, obj: User, form, change: bool) -> None:
        if not change:
            obj._skip_profile_signal = True
        super().save_model(request, obj, form, change)
