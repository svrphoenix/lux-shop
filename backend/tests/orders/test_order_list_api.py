from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.orders.models import Order
from apps.users.models import User


class OrderListAPITests(APITestCase):
    user: User
    other_user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username="order-list-customer",
            email="order-list-customer@example.com",
        )
        cls.other_user = User.objects.create_user(
            username="another-order-customer",
            email="another-order-customer@example.com",
        )

    def setUp(self) -> None:
        self.client.force_authenticate(self.user)
        self.url = reverse("orders:order-list")

    @staticmethod
    def create_order(user: User, order_number: str, status: str) -> Order:
        return Order.objects.create(
            user=user,
            order_number=order_number,
            customer_email=user.email,
            customer_first_name="Test",
            customer_last_name="Customer",
            customer_phone="+380000000000",
            status=status,
            total_amount=Decimal("10.00"),
            shipping_address="Kyiv, Test street",
        )

    def test_lists_only_the_authenticated_users_orders(self) -> None:
        own_order = self.create_order(
            self.user,
            "100001",
            Order.OrderStatus.PENDING,
        )
        self.create_order(
            self.other_user,
            "100002",
            Order.OrderStatus.PENDING,
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [order["order_number"] for order in response.json()],
            [own_order.order_number],
        )

    def test_filters_orders_by_status_without_exposing_other_users_orders(
        self,
    ) -> None:
        matching_order = self.create_order(
            self.user,
            "100003",
            Order.OrderStatus.PAID,
        )
        self.create_order(
            self.user,
            "100004",
            Order.OrderStatus.CANCELLED,
        )
        self.create_order(
            self.other_user,
            "100005",
            Order.OrderStatus.PAID,
        )

        response = self.client.get(self.url, {"status": Order.OrderStatus.PAID})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [order["order_number"] for order in response.json()],
            [matching_order.order_number],
        )

    def test_rejects_unknown_status(self) -> None:
        response = self.client.get(self.url, {"status": "processing"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("status", response.json())
