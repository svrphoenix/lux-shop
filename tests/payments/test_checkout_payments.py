from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order
from apps.payments.models import Payment, PaymentMethod, PaymentStatus
from apps.products.models import Category, Product

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class CheckoutPaymentTests(APITestCase):
    user: User
    product: Product

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username="checkout-customer",
            email="checkout@example.com",
            password="unused",
        )
        category = Category.objects.create(name="Checkout category")
        cls.product = Product.objects.create(
            name="Checkout product",
            category=category,
            price=Decimal("12.50"),
            stock=5,
            description="Product for checkout payment tests.",
        )

    def create_cart(self) -> None:
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_authenticate(self.user)

    def checkout(self, payment_method: str | None = None):
        payload = {
            "full_name": "Test Customer",
            "phone": "+380000000000",
            "city": "Львів (Львівська обл.)",
            "address": "Nova Poshta branch: Відділення №1",
        }
        if payment_method is not None:
            payload["payment_method"] = payment_method
        return self.client.post(reverse("orders:checkout"), payload, format="json")

    def test_mock_card_payment_succeeds_without_card_details(self) -> None:
        # noinspection DuplicatedCode
        self.create_cart()

        response = self.checkout(PaymentMethod.CARD)

        self.assertEqual(response.status_code, 201)
        order: Order = Order.objects.get(order_number=response.json()["order_number"])
        payment: Payment = Payment.objects.get(order=order)
        self.assertEqual(order.status, Order.OrderStatus.PAID)
        self.assertEqual(payment.method, PaymentMethod.CARD)
        self.assertEqual(payment.status, PaymentStatus.SUCCEEDED)
        self.assertEqual(payment.amount, Decimal("25.00"))
        self.assertTrue(payment.is_mock)
        self.assertIsNotNone(payment.transaction_reference)
        assert payment.transaction_reference is not None
        self.assertTrue(payment.transaction_reference.startswith("mock_"))
        self.assertEqual(response.json()["payment"]["status"], PaymentStatus.SUCCEEDED)
        self.assertTrue(response.json()["payment"]["is_mock"])
        self.assertEqual(
            set(response.json()["payment"]),
            {
                "method",
                "status",
                "amount",
                "currency",
                "transaction_reference",
                "is_mock",
                "created_at",
            },
        )
        self.assertEqual(response.json()["payment"]["method"], PaymentMethod.CARD)
        self.assertEqual(response.json()["payment"]["amount"], "25.00")
        self.assertEqual(response.json()["payment"]["currency"], "UAH")
        self.assertEqual(
            response.json()["payment"]["transaction_reference"],
            payment.transaction_reference,
        )
        refreshed_order: Order = Order.objects.get(pk=order.pk)
        self.assertEqual(
            refreshed_order.shipping_address,
            "Львів (Львівська обл.), Nova Poshta branch: Відділення №1",
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(CartItem.objects.filter(cart__user=self.user).exists())

    def test_cash_on_delivery_is_pending(self) -> None:
        # noinspection DuplicatedCode
        self.create_cart()

        response = self.checkout(PaymentMethod.CASH_ON_DELIVERY)

        self.assertEqual(response.status_code, 201)
        order: Order = Order.objects.get(order_number=response.json()["order_number"])
        payment: Payment = Payment.objects.get(order=order)
        self.assertEqual(order.status, Order.OrderStatus.PENDING)
        self.assertEqual(payment.status, PaymentStatus.PENDING)
        self.assertIsNone(payment.transaction_reference)
        self.assertFalse(payment.is_mock)
        self.assertEqual(
            response.json()["payment"]["method"], PaymentMethod.CASH_ON_DELIVERY
        )
        self.assertEqual(response.json()["payment"]["amount"], "25.00")
        self.assertEqual(response.json()["payment"]["currency"], "UAH")

    def test_payment_method_defaults_to_cash_on_delivery(self) -> None:
        self.create_cart()

        response = self.checkout()

        self.assertEqual(response.status_code, 201)
        order: Order = Order.objects.get(order_number=response.json()["order_number"])
        self.assertEqual(order.payment.method, PaymentMethod.CASH_ON_DELIVERY)

    def test_unknown_payment_method_is_rejected_before_checkout(self) -> None:
        self.create_cart()

        response = self.checkout("bank_transfer")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(CartItem.objects.filter(cart__user=self.user).exists())
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())

    def test_checkout_rejects_anonymous_user(self) -> None:
        response = self.checkout(PaymentMethod.CASH_ON_DELIVERY)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Order.objects.exists())

    def test_insufficient_stock_keeps_cart_and_creates_no_order_or_payment(
        self,
    ) -> None:
        self.create_cart()
        item: CartItem = CartItem.objects.get(cart__user=self.user)
        item.quantity = self.product.stock + 1
        item.save(update_fields=["quantity"])

        response = self.checkout(PaymentMethod.CASH_ON_DELIVERY)

        self.assertEqual(response.status_code, 400)
        refreshed_item: CartItem = CartItem.objects.get(pk=item.pk)
        self.assertEqual(refreshed_item.quantity, 6)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())

    def test_existing_order_without_payment_serializes_with_null_payment(self) -> None:
        self.client.force_authenticate(self.user)
        order: Order = Order.objects.create(
            user=self.user,
            customer_email=self.user.email,
            customer_first_name="Test",
            customer_last_name="Customer",
            customer_phone="+380000000000",
            shipping_address="Kyiv",
        )

        response = self.client.get(
            reverse("orders:order-detail", kwargs={"order_number": order.order_number})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["payment"])
