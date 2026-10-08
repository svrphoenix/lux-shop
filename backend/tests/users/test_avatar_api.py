from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from apps.users.models import User


class UserAvatarAPITests(APITestCase):
    def setUp(self) -> None:
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.user = User.objects.create_user(
            username="avatar-owner",
            email="avatar-owner@example.com",
            password="Secure-Test-Password-42!",
        )
        self.client.force_login(self.user)
        self.url = reverse("users:user-avatar")

    @staticmethod
    def make_png_upload() -> SimpleUploadedFile:
        image_content = BytesIO()
        Image.new("RGB", (2, 2), color="green").save(image_content, format="PNG")
        return SimpleUploadedFile(
            "custom-avatar.png",
            image_content.getvalue(),
            content_type="image/png",
        )

    def test_selects_existing_avatar_preset(self) -> None:
        response = self.client.patch(
            self.url,
            {"avatar_preset": "avatar3"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["profile"]["avatar_preset"], "avatar3")
        self.assertFalse(response.json()["profile"]["avatar"])

    def test_uploads_custom_avatar_and_clears_preset(self) -> None:
        self.user.profile.avatar_preset = "avatar2"
        self.user.profile.save(update_fields=["avatar_preset"])

        response = self.client.patch(
            self.url,
            {"avatar": self.make_png_upload()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["profile"]["avatar"].endswith(".png"))
        self.assertEqual(response.json()["profile"]["avatar_preset"], "")
        self.user.refresh_from_db()
        avatar_name = self.user.profile.avatar.name
        self.assertIsNotNone(avatar_name)
        assert avatar_name is not None
        self.assertTrue(self.user.profile.avatar.storage.exists(avatar_name))

    def test_rejects_unknown_avatar_preset(self) -> None:
        response = self.client.patch(
            self.url,
            {"avatar_preset": "external-image.svg"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.user.profile.avatar_preset, "")

    def test_removes_saved_avatar(self) -> None:
        self.user.profile.avatar = self.make_png_upload()
        self.user.profile.avatar_preset = "avatar2"
        self.user.profile.save()
        saved_image_name = self.user.profile.avatar.name

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["profile"]["avatar"])
        self.assertEqual(response.json()["profile"]["avatar_preset"], "")
        self.assertFalse(self.user.profile.avatar.storage.exists(saved_image_name))

    def test_avatar_endpoint_requires_authentication(self) -> None:
        self.client.logout()

        response = self.client.patch(
            self.url,
            {"avatar_preset": "avatar1"},
            format="multipart",
        )

        self.assertEqual(response.status_code, 403)
