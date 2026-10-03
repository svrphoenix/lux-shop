from django.contrib.auth.models import AbstractBaseUser, AnonymousUser

from apps.orders.models import Order
from apps.products.models import Product
from apps.reviews.models import Review

PURCHASED_STATUSES = (
    Order.OrderStatus.PAID,
    Order.OrderStatus.SHIPPED,
    Order.OrderStatus.DELIVERED,
)


def can_review(user: AbstractBaseUser | AnonymousUser, product: Product) -> bool:
    """
    Return whether a user may leave their single review for a product.
    A review is available only to an authenticated customer with at least one
    paid, shipped, or delivered order containing the product.
    """
    if not user.is_authenticated:
        return False

    has_purchased_product = Order.objects.filter(
        user_id=user.pk,
        status__in=PURCHASED_STATUSES,
        items__product_id=product.pk,
    ).exists()
    has_reviewed = Review.objects.filter(
        user_id=user.pk, product_id=product.pk
    ).exists()
    return has_purchased_product and not has_reviewed
