from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import Profile

if TYPE_CHECKING:
    from apps.users.models import User


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(
    sender: type[User], instance: User, created: bool, **kwargs: Any
) -> None:
    """
    Signal to automatically create/save a profile when a user is created.
    """
    _ = (sender, kwargs)
    if getattr(instance, "_skip_profile_signal", False):
        return

    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()
