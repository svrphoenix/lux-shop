from decimal import Decimal

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

from apps.core.views import health_check
from apps.orders.models import Order, OrderItem

User = get_user_model()
original_each_context = admin.site.each_context


def add_admin_dashboard_context(request):
    context = original_each_context(request)
    revenue_statuses = [
        Order.OrderStatus.PAID,
        Order.OrderStatus.SHIPPED,
        Order.OrderStatus.DELIVERED,
    ]
    order_stats = Order.objects.aggregate(
        total_orders=Count("id"),
        revenue=Coalesce(
            Sum("total_amount", filter=Q(status__in=revenue_statuses)),
            Decimal("0.00"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        paid_orders=Count("id", filter=Q(status__in=revenue_statuses)),
    )
    top_products = (
        OrderItem.objects.filter(order__status__in=revenue_statuses)
        .values("product__name")
        .annotate(
            sold_quantity=Sum("quantity"),
            revenue=Sum(
                F("price") * F("quantity"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by("-sold_quantity")[:5]
    )
    user_stats = User.objects.aggregate(
        total_users=Count("id"),
        staff_users=Count("id", filter=Q(is_staff=True)),
        active_users=Count("id", filter=Q(is_active=True)),
    )

    context["admin_dashboard"] = {
        "total_orders": order_stats["total_orders"] or 0,
        "paid_orders": order_stats["paid_orders"] or 0,
        "revenue": order_stats["revenue"] or Decimal("0.00"),
        "total_users": user_stats["total_users"] or 0,
        "staff_users": user_stats["staff_users"] or 0,
        "active_users": user_stats["active_users"] or 0,
        "top_products": [
            {
                "name": item["product__name"] or "Unknown product",
                "sold_quantity": item["sold_quantity"] or 0,
                "revenue": item["revenue"] or Decimal("0.00"),
            }
            for item in top_products
        ],
    }
    return context


admin.site.index_template = "admin/custom_index.html"
admin.site.each_context = add_admin_dashboard_context  # type: ignore[method-assign]
admin.site.site_header = _(f"{settings.SITE_NAME} administration site")
admin.site.index_title = _("Welcome to site admin panel")
admin.site.site_title = _(f"{settings.SITE_NAME} admin")
admin.site.site_url = settings.FRONTEND_URL

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health_check"),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            permission_classes=[AllowAny],
        ),
        name="swagger-ui",
    ),
    path("api/v1/auth/", include("apps.users.urls_auth", namespace="auth")),
    path("api/v1/", include("apps.users.urls", namespace="users")),
    path("api/v1/", include("apps.products.urls", namespace="products")),
    path("api/v1/", include("apps.reviews.urls", namespace="reviews")),
    path("api/v1/", include("apps.cart.urls", namespace="cart")),
    path("api/v1/", include("apps.orders.urls", namespace="orders")),
    path("api/v1/delivery/", include("apps.delivery.urls", namespace="delivery")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
