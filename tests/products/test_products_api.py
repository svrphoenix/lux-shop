from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, OrderItem
from apps.products.models import Category, Product
from apps.reviews.models import Review
from apps.users.models import User


class ProductsAPITests(TestCase):
    hops: Category
    aroma: Category
    yeast: Category
    citra: Product
    saaz: Product
    us05: Product
    hidden: Product

    @classmethod
    def setUpTestData(cls) -> None:
        cls.hops = Category.objects.create(name="Hops")
        cls.aroma = Category.objects.create(name="Aroma Hops", parent=cls.hops)
        cls.yeast = Category.objects.create(name="Yeast")
        cls.citra = Product.objects.create(
            name="Citra",
            category=cls.aroma,
            price=Decimal("6.00"),
            stock=5,
            description="Tropical fruit aroma",
        )
        cls.saaz = Product.objects.create(
            name="Saaz", category=cls.hops, price=Decimal("4.00"), stock=0
        )
        cls.us05 = Product.objects.create(
            name="US-05", category=cls.yeast, price=Decimal("3.00"), stock=9
        )
        cls.hidden = Product.objects.create(
            name="Hidden", category=cls.yeast, price=Decimal("1.00"), is_active=False
        )

    def product_names(self, **params: str | list[str]) -> list[str]:
        response = self.client.get(reverse("products:product-list"), params)
        self.assertEqual(response.status_code, 200)
        return [product["name"] for product in response.json()["results"]]

    def test_list_only_shows_active_products(self) -> None:
        self.assertCountEqual(self.product_names(), ["Citra", "Saaz", "US-05"])

    def test_category_filter_includes_direct_children(self) -> None:
        self.assertCountEqual(
            self.product_names(category=self.hops.slug), ["Citra", "Saaz"]
        )

    def test_multiple_categories_search_price_and_stock_filters(self) -> None:
        self.assertCountEqual(
            self.product_names(category=[self.aroma.slug, self.yeast.slug]),
            ["Citra", "US-05"],
        )
        self.assertEqual(self.product_names(search="TROPICAL"), ["Citra"])
        self.assertCountEqual(
            self.product_names(min_price="3.50", max_price="6.00"),
            ["Citra", "Saaz"],
        )
        self.assertCountEqual(self.product_names(in_stock="true"), ["Citra", "US-05"])

    def test_ordering_by_price_rating_and_popularity(self) -> None:
        user = User.objects.create_user(username="reviewer")
        Review.objects.create(user=user, product=self.us05, rating=5)
        Review.objects.create(user=user, product=self.saaz, rating=2)
        order = Order.objects.create(
            customer_email="customer@example.com",
            customer_first_name="Test",
            customer_last_name="Customer",
            customer_phone="+380000000000",
            shipping_address="Kyiv",
        )
        OrderItem.objects.create(
            order=order, product=self.saaz, price=self.saaz.price, quantity=3
        )

        self.assertEqual(
            self.product_names(ordering="price"), ["US-05", "Saaz", "Citra"]
        )
        self.assertEqual(self.product_names(ordering="-rating")[0], "US-05")
        self.assertEqual(self.product_names(ordering="-popularity")[0], "Saaz")

    def test_detail_returns_annotated_product_and_hides_inactive_product(self) -> None:
        response = self.client.get(self.citra.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Citra")
        self.assertEqual(response.json()["rating_avg"], 0.0)
        self.assertEqual(
            self.client.get(self.hidden.get_absolute_url()).status_code,
            404,
        )

    def test_categories_list_only_returns_active_root_categories(self) -> None:
        Category.objects.create(name="Hidden root", is_active=False)

        response = self.client.get(reverse("products:category-list"))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [category["name"] for category in response.json()], ["Hops", "Yeast"]
        )
