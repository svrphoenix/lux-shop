from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.payments.models import PaymentMethod
from apps.payments.services import create_payment_for_order
from apps.products.models import Product

if TYPE_CHECKING:
    from apps.users.models import User
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()


class CheckoutError(Exception):
    """The cart cannot be converted into an order."""


@transaction.atomic
def create_order_from_cart(user: User, checkout_data: dict[str, Any]) -> Order:
    """Create a pending order, snapshot prices, reserve stock, and empty the cart."""
    try:
        cart = Cart.objects.select_for_update().get(user=user)
    except Cart.DoesNotExist as error:
        raise CheckoutError("Your cart is empty.") from error

    cart_items: list[CartItem] = list(
        CartItem.objects.select_for_update().select_related("product").filter(cart=cart)
    )
    if not cart_items:
        raise CheckoutError("Your cart is empty.")

    product_ids = [item.product.pk for item in cart_items]
    products = Product.objects.select_for_update().in_bulk(product_ids)

    for item in cart_items:
        product = products.get(item.product.pk)
        if product is None or not product.is_active:
            raise CheckoutError("One or more products are no longer available.")
        if item.quantity > product.stock:
            raise CheckoutError(
                f"Only {product.stock} units of '{product.name}' are currently available."
            )

    first_name, last_name = _split_full_name(checkout_data["full_name"])
    addr_parts = (checkout_data.get("city"), checkout_data.get("address"))
    shipping_address = ", ".join([str(part) for part in addr_parts if part])
    order = Order.objects.create(
        user=user,
        customer_email=user.email,
        customer_first_name=first_name,
        customer_last_name=last_name,
        customer_phone=checkout_data["phone"],
        shipping_address=shipping_address,
    )

    order_items = [
        OrderItem(
            order=order,
            product=products[item.product.pk],
            price=products[item.product.pk].price,
            quantity=item.quantity,
        )
        for item in cart_items
    ]
    OrderItem.objects.bulk_create(order_items)

    total_amount = sum(
        (item.price * item.quantity for item in order_items), Decimal("0.00")
    )
    Order.objects.filter(pk=order.pk).update(total_amount=total_amount)
    order.total_amount = total_amount
    payment_method = PaymentMethod(
        checkout_data.get("payment_method", PaymentMethod.CASH_ON_DELIVERY)
    )
    create_payment_for_order(order, payment_method)

    for item in cart_items:
        product = products[item.product.pk]
        product.stock -= item.quantity

    Product.objects.bulk_update(list(products.values()), ["stock"])

    CartItem.objects.filter(cart=cart).delete()

    return order


def _split_full_name(full_name: str) -> tuple[str, str]:
    name_parts = full_name.strip().split(maxsplit=1)
    if not name_parts:
        return "", ""
    if len(name_parts) == 1:
        return name_parts[0], ""
    return name_parts[0], name_parts[1]
