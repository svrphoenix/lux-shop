from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model with unique email.
    """

    email = models.EmailField(_("email address"), unique=True)
    _skip_profile_signal: bool = False

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


class Profile(models.Model):
    """
    User profile with additional data.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile", verbose_name=_("user")
    )
    phone_number = models.CharField(_("phone number"), max_length=20, blank=True)
    address = models.TextField(_("address of delivery"), blank=True)
    birth_day = models.DateField(_("date of birth"), blank=True, null=True)
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")

    def __str__(self):
        full_name = self.user.get_full_name()
        return (
            f"{full_name} ({self.user.username})" if full_name else self.user.username
        )
