from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.users.models import Profile

if TYPE_CHECKING:
    from apps.users.models import User


# noinspection PyUnusedLocal
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(
    _sender: type[User], instance: User, created: bool, **_kwargs: Any
) -> None:
    """
    Signal to automatically create/save a profile when a user is created.
    """
    if created:
        Profile.objects.create(user=instance)
    else:
        if hasattr(instance, "profile"):
            instance.profile.save()
        else:
            Profile.objects.create(user=instance)
