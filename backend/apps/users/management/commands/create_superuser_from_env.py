import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.users.models import User


class Command(BaseCommand):
    help = "Create the configured superuser if it does not already exist."

    def handle(self, *args: object, **options: object) -> None:
        _ = (args, options)
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not any((username, email, password)):
            self.stdout.write("Superuser credentials are not configured; skipping.")
            return
        if not all((username, email, password)):
            raise CommandError(
                "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and "
                "DJANGO_SUPERUSER_PASSWORD together."
            )

        user = User.objects.filter(username=username).first()
        if user:
            if not user.is_superuser:
                raise CommandError(
                    f"Username '{username}' already exists and is not a superuser."
                )
            self.stdout.write(f"Superuser '{username}' already exists; keeping it.")
            return

        candidate = User(username=username, email=email)
        try:
            validate_password(password, user=candidate)
        except ValidationError as error:
            raise CommandError("; ".join(error.messages)) from error

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
