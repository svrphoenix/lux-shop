from typing import Any
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import reverse

from apps.delivery.services import NovaPoshtaClient, NovaPoshtaError

API_URL = "https://api.example/json/"


def api_answer(
    data: list[dict], success: bool = True, errors: list[str] | None = None
) -> Mock:
    response = Mock()
    response.json.return_value = {"success": success, "data": data, "errors": errors or []}
    return response


class NovaPoshtaClientTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_city_search_uses_settlement_refs_and_maps_response(self) -> None:
        response = api_answer(
            [
                {
                    "Ref": "settlement-1",
                    "Description": "Львів",
                    "AreaDescription": "Львівська",
                }
            ]
        )
        with self.patch_requests(response) as post:
            cities = NovaPoshtaClient("test-key", API_URL).search_cities("Льв")

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["apiKey"], "test-key")
        self.assertEqual(
            (payload["modelName"], payload["calledMethod"]),
            ("AddressGeneral", "getSettlements"),
        )
        self.assertEqual(
            payload["methodProperties"],
            {"FindByString": "Льв", "Warehouse": "1", "Limit": "10"},
        )
        self.assertEqual(cities[0].ref, "settlement-1")
        self.assertEqual(cities[0].label, "Львів (Львівська обл.)")

    def test_warehouse_search_filters_by_requested_type(self) -> None:
        common = {"CityRef": "city-1", "CityDescription": "Львів", "Number": "1"}
        response = api_answer(
            [
                common
                | {
                    "Ref": "branch-1",
                    "Description": "Відділення №1",
                    "CategoryOfWarehouse": "Branch",
                },
                common
                | {
                    "Ref": "postomat-1",
                    "Description": "Поштомат №1",
                    "CategoryOfWarehouse": "Postomat",
                },
            ]
        )
        with self.patch_requests(response) as post:
            branches = NovaPoshtaClient("test-key", API_URL).search_warehouses("city-1")
            postomats = NovaPoshtaClient("test-key", API_URL).search_warehouses(
                "city-1", postomat=True
            )

        self.assertEqual([item.ref for item in branches], ["branch-1"])
        self.assertEqual([item.ref for item in postomats], ["postomat-1"])
        properties = post.call_args.kwargs["json"]["methodProperties"]
        self.assertEqual(
            properties["TypeOfWarehouseRef"],
            "f9316480-5f2d-425d-bc2c-ac7cd29decf0",
        )

    def test_street_search_maps_flat_api_response(self) -> None:
        response = api_answer(
            [
                {
                    "SettlementStreetRef": "street-1",
                    "SettlementStreetDescription": "Шевченка",
                    "StreetsTypeDescription": "вул.",
                },
                {
                    "SettlementStreetRef": "street-2",
                    "SettlementStreetDescription": "Шевченківська",
                    "StreetsTypeDescription": "вул.",
                },
            ]
        )
        with self.patch_requests(response) as post:
            streets = NovaPoshtaClient("test-key", API_URL).search_streets(
                "city-1", "Шев"
            )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(
            (payload["modelName"], payload["calledMethod"]),
            ("Address", "searchSettlementStreets"),
        )
        self.assertEqual(
            payload["methodProperties"],
            {"StreetName": "Шев", "SettlementRef": "city-1", "Limit": "10"},
        )
        self.assertEqual(
            [(street.ref, street.label) for street in streets],
            [("street-1", "вул. Шевченка"), ("street-2", "вул. Шевченківська")],
        )

    def test_no_matching_city_is_an_empty_result(self) -> None:
        response = api_answer([], success=False, errors=["FindByString is not specified"])
        with self.patch_requests(response):
            cities = NovaPoshtaClient("test-key", API_URL).search_cities("Qqqzz")
        self.assertEqual(cities, [])

    def test_client_surfaces_api_and_network_errors(self) -> None:
        api_error = api_answer([], success=False, errors=["API key is invalid"])
        with (
            self.patch_requests(api_error),
            self.assertRaisesRegex(NovaPoshtaError, "API key is invalid"),
        ):
            NovaPoshtaClient("test-key", API_URL).search_cities("Київ")

        with (
            self.patch_requests(side_effect=requests.ConnectionError("offline")),
            self.assertRaises(NovaPoshtaError),
        ):
            NovaPoshtaClient("test-key", API_URL).search_cities("Київ")

    def test_client_without_api_key_does_not_call_provider(self) -> None:
        with (
            self.patch_requests() as post,
            self.assertRaises(NovaPoshtaError),
        ):
            NovaPoshtaClient("", API_URL).search_cities("Київ")
        post.assert_not_called()

    def patch_requests(self, response: Mock | None = None, **kwargs: object) -> Any:
        options = dict(kwargs)
        if response is not None:
            options["return_value"] = response
        return patch("apps.delivery.services.requests.post", **options)


class DeliveryEndpointTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()
        self.nova_client_patch = self.enterContext(
            patch("apps.delivery.views.get_client")
        )
        self.nova_client = self.nova_client_patch.return_value

    def test_city_endpoint_requires_two_query_characters(self) -> None:
        response = self.client.get(reverse("delivery:cities"), {"q": "я"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})
        self.nova_client.search_cities.assert_not_called()

    def test_city_endpoint_returns_city_results(self) -> None:
        from apps.delivery.services import City

        self.nova_client.search_cities.return_value = [
            City("city-1", "Львів", "Львівська")
        ]
        response = self.client.get(reverse("delivery:cities"), {"q": "Льв"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["ref"], "city-1")
        self.assertEqual(
            response.json()["results"][0]["label"], "Львів (Львівська обл.)"
        )

    def test_warehouse_endpoint_filters_and_rejects_invalid_type(self) -> None:
        from apps.delivery.services import Warehouse

        self.nova_client.search_warehouses.return_value = [
            Warehouse("wh-1", "city-1", "Львів", "1", "Відділення №1", False)
        ]
        url = reverse("delivery:warehouses")
        response = self.client.get(url, {"city": "city-1"})
        self.assertEqual(response.status_code, 200)
        self.nova_client.search_warehouses.assert_called_once_with(
            "city-1", "", postomat=False
        )

        response = self.client.get(url, {"city": "city-1", "type": "unknown"})
        self.assertEqual(response.status_code, 400)

    def test_street_endpoint_returns_matching_streets(self) -> None:
        from apps.delivery.services import Street

        self.nova_client.search_streets.return_value = [
            Street("street-1", "Шевченка", "вул.")
        ]
        response = self.client.get(
            reverse("delivery:streets"), {"city": "city-1", "q": "Шев"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "ref": "street-1",
                        "name": "Шевченка",
                        "street_type": "вул.",
                        "label": "вул. Шевченка",
                    }
                ]
            },
        )
        self.nova_client.search_streets.assert_called_once_with("city-1", "Шев")

    def test_provider_outage_returns_service_unavailable(self) -> None:
        self.nova_client.search_cities.side_effect = NovaPoshtaError("offline")
        response = self.client.get(reverse("delivery:cities"), {"q": "Київ"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("detail", response.json())
