from django.urls import path

from apps.reviews.views import ProductReviewListCreateView

app_name = "reviews"

urlpatterns = [
    path(
        "products/<slug:product_slug>/reviews/",
        ProductReviewListCreateView.as_view(),
        name="product-review-list",
    ),
]
