from django.urls import path

from apps.delivery.views import CitySearchView, StreetSearchView, WarehouseSearchView

app_name = "delivery"

urlpatterns = [
    path("cities/", CitySearchView.as_view(), name="cities"),
    path("warehouses/", WarehouseSearchView.as_view(), name="warehouses"),
    path("streets/", StreetSearchView.as_view(), name="streets"),
]
