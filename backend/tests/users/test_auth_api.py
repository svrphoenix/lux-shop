from urllib.parse import parse_qs, urlparse

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.users.models import User


class AuthenticationAPITests(TestCase):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username="account-owner",
            email="owner@example.com",
            password="Test-Secure-Password-42!",
            first_name="Account",
        )

    def setUp(self) -> None:
        cache.clear()
        mail.outbox.clear()

    def test_login_accepts_username(self) -> None:
        response = self.client.post(
            reverse("auth:login"),
            {"username": "account-owner", "password": "Test-Secure-Password-42!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], "account-owner")
        self.assertIn("access", response.json())

    def test_login_accepts_email_case_insensitively(self) -> None:
        response = self.client.post(
            reverse("auth:login"),
            {"username": "OWNER@EXAMPLE.COM", "password": "Test-Secure-Password-42!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["id"], self.user.pk)

    def test_password_reset_request_sends_link_for_existing_email(self) -> None:
        response = self.client.post(
            reverse("auth:password_reset"),
            {"email": "OWNER@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        reset_url = next(
            line
            for line in mail.outbox[0].body.splitlines()
            if "/reset-password/" in line
        )
        query = parse_qs(urlparse(reset_url).query)
        self.assertIn("uid", query)
        self.assertIn("token", query)
        self.assertIn("localhost:3000/reset-password/", reset_url)

    def test_password_reset_request_does_not_disclose_unknown_email(self) -> None:
        known_response = self.client.post(
            reverse("auth:password_reset"),
            {"email": self.user.email},
        )
        unknown_response = self.client.post(
            reverse("auth:password_reset"),
            {"email": "unknown@example.com"},
        )

        self.assertEqual(known_response.status_code, 200)
        self.assertEqual(unknown_response.status_code, 200)
        self.assertEqual(known_response.json(), unknown_response.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_changes_password_and_token_is_single_use(self) -> None:
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        payload = {
            "uid": uid,
            "token": token,
            "new_password": "Another-Secure-Password-84!",
            "new_password_confirm": "Another-Secure-Password-84!",
        }

        response = self.client.post(reverse("auth:password_reset_confirm"), payload)

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["new_password"]))

        reused_token_response = self.client.post(
            reverse("auth:password_reset_confirm"), payload
        )
        self.assertEqual(reused_token_response.status_code, 400)

    def test_password_reset_rejects_mismatched_passwords(self) -> None:
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
            "token": default_token_generator.make_token(self.user),
            "new_password": "Another-Secure-Password-84!",
            "new_password_confirm": "Different-Secure-Password-85!",
        }

        response = self.client.post(reverse("auth:password_reset_confirm"), payload)

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Test-Secure-Password-42!"))

    def test_password_reset_rejects_invalid_token(self) -> None:
        payload = {
            "uid": urlsafe_base64_encode(force_bytes(self.user.pk)),
            "token": "invalid-token",
            "new_password": "Another-Secure-Password-84!",
            "new_password_confirm": "Another-Secure-Password-84!",
        }

        response = self.client.post(reverse("auth:password_reset_confirm"), payload)

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Test-Secure-Password-42!"))
