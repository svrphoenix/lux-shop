from dataclasses import asdict

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.delivery.services import NovaPoshtaError, get_client

CACHE_SECONDS = 60 * 60 * 24
SERVICE_UNAVAILABLE_RESPONSE = {
    "detail": _("Delivery service is currently unavailable. Please try again later.")
}


class WarehouseQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    q = serializers.CharField(required=False, default="", allow_blank=True)
    type = serializers.ChoiceField(choices=["branch", "postomat"], default="branch")


class StreetQuerySerializer(serializers.Serializer):
    city = serializers.CharField(required=True)
    q = serializers.CharField(required=True, min_length=2)


class CitySearchView(APIView):
    permission_classes = [permissions.AllowAny]

    # noinspection PyMethodMayBeStatic
    def get(self, request: Request) -> Response:
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})

        try:
            cities = cache.get_or_set(
                f"np:cities:v2:{query.lower()}",
                lambda: get_client().search_cities(query),
                CACHE_SECONDS,
            )
        except NovaPoshtaError:
            return Response(
                SERVICE_UNAVAILABLE_RESPONSE,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "results": [
                    asdict(city) | {"label": city.label} for city in (cities or [])
                ]
            }
        )


class WarehouseSearchView(APIView):
    permission_classes = [permissions.AllowAny]

    # noinspection PyMethodMayBeStatic
    def get(self, request: Request) -> Response:
        serializer = WarehouseQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        city_ref = serializer.validated_data["city"]
        query = serializer.validated_data["q"].strip()
        postomat = serializer.validated_data["type"] == "postomat"

        try:
            warehouses = cache.get_or_set(
                f"np:warehouses:{city_ref}:{postomat}:{query.lower()}",
                lambda: get_client().search_warehouses(
                    city_ref, query, postomat=postomat
                ),
                CACHE_SECONDS,
            )
        except NovaPoshtaError:
            return Response(
                SERVICE_UNAVAILABLE_RESPONSE,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({"results": [asdict(item) for item in (warehouses or [])]})


class StreetSearchView(APIView):
    """Search streets for address delivery (courier delivery)."""

    permission_classes = [permissions.AllowAny]

    # noinspection PyMethodMayBeStatic
    def get(self, request: Request) -> Response:
        serializer = StreetQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        city_ref = serializer.validated_data["city"]
        query = serializer.validated_data["q"].strip()

        try:
            cache_key = f"np:streets:v2:{city_ref}:{query.lower()}"
            streets = cache.get(cache_key)
            if streets is None:
                streets = get_client().search_streets(city_ref, query)
                if streets:
                    cache.set(cache_key, streets, CACHE_SECONDS)
        except NovaPoshtaError:
            return Response(
                SERVICE_UNAVAILABLE_RESPONSE,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "results": [
                    asdict(street) | {"label": street.label}
                    for street in (streets or [])
                ]
            }
        )
