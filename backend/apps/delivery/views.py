from dataclasses import asdict

from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.delivery.serializers import (
    CitySearchResponseSerializer,
    DeliveryErrorSerializer,
    StreetQuerySerializer,
    StreetSearchResponseSerializer,
    WarehouseQuerySerializer,
    WarehouseSearchResponseSerializer,
)
from apps.delivery.services import NovaPoshtaError, get_client

CACHE_SECONDS = 60 * 60 * 24
SERVICE_UNAVAILABLE_RESPONSE = {
    "detail": _("Delivery service is currently unavailable. Please try again later.")
}


class CitySearchView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                type=str,
                required=False,
                description="City name; searches require at least two characters.",
            )
        ],
        responses={
            200: CitySearchResponseSerializer,
            503: OpenApiResponse(response=DeliveryErrorSerializer),
        },
        description="Search settlements by name. An empty query returns no results.",
    )
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

    @extend_schema(
        parameters=[WarehouseQuerySerializer],
        responses={
            200: WarehouseSearchResponseSerializer,
            400: OpenApiResponse(description="Invalid city, query, or warehouse type."),
            503: OpenApiResponse(response=DeliveryErrorSerializer),
        },
        description="Search branches or parcel lockers in a Nova Poshta city.",
    )
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

    @extend_schema(
        parameters=[StreetQuerySerializer],
        responses={
            200: StreetSearchResponseSerializer,
            400: OpenApiResponse(
                description="City is missing or query is shorter than two characters."
            ),
            503: OpenApiResponse(response=DeliveryErrorSerializer),
        },
        description="Search streets for courier delivery in a Nova Poshta city.",
    )
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
