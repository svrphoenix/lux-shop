from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _("profile")


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("get_username", "phone_number", "birth_day", "created_at")
    search_fields = ("user__username", "user__email", "phone_number")
    list_select_related = ("user",)

    @admin.display(description=_("user"), ordering="user__username")
    def get_username(self, obj: Profile) -> str:
        full_name = obj.user.get_full_name()
        return f"{full_name} ({obj.user.username})" if full_name else obj.user.username
