from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework.permissions import AllowAny

from apps.core.views import health_check

admin.site.site_header = _("LuxShop administration site")
admin.site.index_title = _("Welcome to site admin panel")
admin.site.site_title = _("LuxShop admin")
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
