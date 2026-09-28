from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.products.models import Product

if TYPE_CHECKING:
    from apps.users.models import User
else:
    User = get_user_model()


class CartError(Exception):
    """Base exception for cart mutations that cannot be completed."""


class CartItemNotFoundError(CartError):
    """The requested cart item is not owned by the current user."""


class ProductUnavailableError(CartError):
    """The product no longer exists or is not available for purchase."""


class InsufficientStockError(CartError):
    def __init__(self, product: Product, requested_quantity: int) -> None:
        self.product = product
        self.requested_quantity = requested_quantity
        super().__init__(
            f"Only {product.stock} units of '{product.name}' are currently available."
        )


def get_cart_for_user(user: User) -> Cart:
    """Return a cart with all product data preloaded for client representation."""
    cart, _ = Cart.objects.get_or_create(user=user)
    return Cart.objects.prefetch_related("items__product").get(pk=cart.pk)


@transaction.atomic
def add_item(user: User, product_id: int, quantity: int) -> Cart:
    """Add a quantity to a cart line without exceeding the current stock."""
    product = _get_locked_active_product(product_id)
    cart = _get_locked_cart(user)
    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart, product=product, defaults={"quantity": quantity}
    )
    if created:
        _validate_stock(product, quantity)
    else:
        requested_quantity = item.quantity + quantity
        _validate_stock(product, requested_quantity)
        item.quantity = requested_quantity
        item.save(update_fields=["quantity", "updated_at"])
    return get_cart_for_user(user)


@transaction.atomic
def update_item(user: User, item_id: int, quantity: int) -> Cart:
    """Set a cart line quantity; zero removes the line."""
    cart = _get_locked_cart(user)
    try:
        item: CartItem = (
            CartItem.objects.select_for_update()
            .select_related("product")
            .get(pk=item_id, cart=cart)
        )
    except CartItem.DoesNotExist as error:
        raise CartItemNotFoundError("Cart item was not found.") from error

    if quantity == 0:
        item.delete()
        return get_cart_for_user(user)

    product = _get_locked_active_product(item.product.id)
    _validate_stock(product, quantity)
    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return get_cart_for_user(user)


@transaction.atomic
def remove_item(user: User, item_id: int) -> Cart:
    """Remove a cart line even when the product was deactivated."""
    cart = _get_locked_cart(user)
    deleted, _ = CartItem.objects.filter(pk=item_id, cart=cart).delete()
    if not deleted:
        raise CartItemNotFoundError("Cart item was not found.")
    return get_cart_for_user(user)


@transaction.atomic
def clear_cart(user: User) -> Cart:
    """Remove all items from the user's cart."""
    cart = _get_locked_cart(user)
    cart.items.all().delete()
    return get_cart_for_user(user)


def _get_locked_cart(user: User) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return Cart.objects.select_for_update().get(pk=cart.pk)


def _get_locked_active_product(product_id: int) -> Product:
    try:
        return Product.objects.select_for_update().active().get(pk=product_id)
    except Product.DoesNotExist as error:
        raise ProductUnavailableError("Product is not available.") from error


def _validate_stock(product: Product, quantity: int) -> None:
    if quantity > product.stock:
        raise InsufficientStockError(product, quantity)


@transaction.atomic
def merge_guest_cart(user: User, guest_items: list[dict[str, int]]) -> Cart:
    """
    Merge an anonymous guest cart with the authenticated user's persistent cart.
    `guest_items` is expected in the format: [{"product_id": 1, "quantity": 2}, ...]
    """
    for item in guest_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)

        if not product_id or quantity <= 0:
            continue

        try:
            add_item(user=user, product_id=product_id, quantity=quantity)
        except (ProductUnavailableError, InsufficientStockError):
            continue

    return get_cart_for_user(user)
