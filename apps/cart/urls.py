from django.urls import path

from apps.cart.views import (
    CartItemCreateView,
    CartItemDetailView,
    CartMergeView,
    CartView,
)

app_name = "cart"

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemCreateView.as_view(), name="cart-item-create"),
    path(
        "cart/items/<int:pk>/",
        CartItemDetailView.as_view(),
        name="cart-item-detail",
    ),
    path("cart/merge/", CartMergeView.as_view(), name="cart-merge"),
]
