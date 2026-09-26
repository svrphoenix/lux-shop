from decimal import Decimal
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product
from apps.reviews.models import Review
from apps.reviews.services import can_review

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class ReviewsAPITests(APITestCase):
    client: APIClient
    product: Product
    buyer: User
    non_buyer: User

    @classmethod
    def setUpTestData(cls) -> None:
        category = Category.objects.create(name="Hops")
        cls.product = Product.objects.create(
            name="Citra Hops",
            category=category,
            price=Decimal("6.00"),
            stock=10,
            description="Explosive citrus aroma.",
        )
        cls.buyer = User.objects.create_user(
            username="homebrewer_27", email="homebrewer_27@example.com"
        )
        cls.non_buyer = User.objects.create_user(
            username="new_brewer", email="new_brewer@example.com"
        )

    @property
    def reviews_url(self) -> str:
        return reverse(
            "reviews:product-review-list",
            kwargs={"product_slug": self.product.slug},
        )

    def purchase(self, user: User, status: str) -> None:
        order = Order.objects.create(
            user=user,
            customer_email=user.email,
            customer_first_name="Test",
            customer_last_name="Customer",
            customer_phone="+380000000000",
            shipping_address="Kyiv",
            status=status,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=self.product.price,
            quantity=1,
        )

    def test_reviews_are_public_but_guests_cannot_create_them(self) -> None:
        response = self.client.get(self.reviews_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])
        self.assertEqual(
            self.client.post(
                self.reviews_url, {"rating": 5}, format="json"
            ).status_code,
            403,
        )

    def test_only_purchasers_with_completed_order_statuses_can_review(self) -> None:
        self.assertFalse(can_review(AnonymousUser(), self.product))
        self.assertFalse(can_review(self.buyer, self.product))

        for status in (Order.OrderStatus.PENDING, Order.OrderStatus.CANCELLED):
            with self.subTest(status=status):
                self.purchase(self.buyer, status)
                self.assertFalse(can_review(self.buyer, self.product))
                Order.objects.filter(user=self.buyer).delete()

        for status in (
            Order.OrderStatus.PAID,
            Order.OrderStatus.SHIPPED,
            Order.OrderStatus.DELIVERED,
        ):
            with self.subTest(status=status):
                self.purchase(self.buyer, status)
                self.assertTrue(can_review(self.buyer, self.product))
                Order.objects.filter(user=self.buyer).delete()

    def test_buyer_can_create_one_valid_review_and_sees_eligibility_change(
        self,
    ) -> None:
        self.purchase(self.buyer, Order.OrderStatus.DELIVERED)
        self.client.force_authenticate(self.buyer)

        product_response = self.client.get(self.product.get_absolute_url())
        response = self.client.post(
            self.reviews_url,
            {"rating": 5, "comment": "Explosive Citrus Aroma!"},
            format="json",
        )

        self.assertEqual(product_response.json()["can_review"], True)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["author"]["username"], self.buyer.username)
        self.assertEqual(response.json()["rating"], 5)
        self.assertFalse(can_review(self.buyer, self.product))
        self.assertFalse(
            self.client.get(self.product.get_absolute_url()).json()["can_review"]
        )

    def test_duplicate_and_non_buyer_reviews_are_rejected(self) -> None:
        self.client.force_authenticate(self.non_buyer)
        self.assertEqual(
            self.client.post(
                self.reviews_url, {"rating": 4}, format="json"
            ).status_code,
            403,
        )

        self.purchase(self.buyer, Order.OrderStatus.PAID)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.post(
                self.reviews_url, {"rating": 4}, format="json"
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.post(
                self.reviews_url, {"rating": 1}, format="json"
            ).status_code,
            403,
        )

    def test_database_constraint_prevents_duplicate_reviews(self) -> None:
        Review.objects.create(user=self.buyer, product=self.product, rating=5)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(user=self.buyer, product=self.product, rating=4)

    def test_rating_must_be_between_one_and_five(self) -> None:
        self.purchase(self.buyer, Order.OrderStatus.SHIPPED)
        self.client.force_authenticate(self.buyer)

        for rating in (0, 6, "not-a-rating"):
            with self.subTest(rating=rating):
                response = self.client.post(
                    self.reviews_url, {"rating": rating}, format="json"
                )
                self.assertEqual(response.status_code, 400)

        self.assertFalse(Review.objects.exists())

    def test_reviews_include_author_data_and_inactive_product_is_hidden(self) -> None:
        Review.objects.create(
            user=self.buyer,
            product=self.product,
            rating=5,
            comment="A must-have for hop-forward beer.",
        )

        response = self.client.get(self.reviews_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["author"]["avatar"], None)

        self.product.is_active = False
        self.product.save(update_fields=["is_active"])
        self.assertEqual(self.client.get(self.reviews_url).status_code, 404)
        self.client.force_authenticate(self.buyer)
        self.assertEqual(
            self.client.post(
                self.reviews_url, {"rating": 5}, format="json"
            ).status_code,
            404,
        )
