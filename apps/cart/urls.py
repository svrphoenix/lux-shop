from django.urls import path

from apps.cart.views import CartItemCreateView, CartItemDetailView, CartView

app_name = "cart"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemCreateView.as_view(), name="cart-item-create"),
    path(
        "cart/items/<int:item_id>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
]
