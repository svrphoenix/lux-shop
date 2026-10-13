import smtplib
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.test import SimpleTestCase

from apps.orders.notifications import send_order_emails


class OrderNotificationTests(SimpleTestCase):
    def setUp(self) -> None:
        if hasattr(mail, "outbox"):
            mail.outbox.clear()

        order_item = SimpleNamespace(
            product=SimpleNamespace(name="Test product"),
            quantity=2,
            cost=Decimal("25.00"),
        )
        self.order = SimpleNamespace(
            order_number="100001",
            customer_email="customer@example.com",
            customer_first_name="Test",
            customer_last_name="Customer",
            customer_phone="+380000000000",
            shipping_address="Kyiv, Test street",
            total_amount=Decimal("25.00"),
            get_status_display=lambda: "Очікує",
            items=SimpleNamespace(all=lambda: [order_item]),
        )

    def test_sends_order_confirmation_and_admin_notification(self) -> None:
        send_order_emails(self.order)  # type: ignore[arg-type]

        self.assertEqual(len(mail.outbox), 2)
        customer_message, admin_message = mail.outbox
        self.assertEqual(customer_message.to, ["customer@example.com"])
        self.assertEqual(admin_message.to, ["admin@example.com"])
        self.assertEqual(customer_message.from_email, "orders@example.com")
        self.assertIn("100001", customer_message.body)
        self.assertIn("Test product", customer_message.body)
        self.assertIn("25.00 UAH", admin_message.body)

    def test_admin_notification_is_attempted_when_customer_delivery_fails(
        self,
    ) -> None:
        with (
            patch(
                "apps.core.emails.send_mail",
                side_effect=[smtplib.SMTPException("Resend unavailable"), 1],
            ) as send_mail,
            self.assertLogs("apps.core.emails", level="ERROR"),
        ):
            send_order_emails(self.order)  # type: ignore[arg-type]
        self.assertEqual(
            [entry.kwargs["recipient_list"] for entry in send_mail.call_args_list],
            [["customer@example.com"], ["admin@example.com"]],
        )
