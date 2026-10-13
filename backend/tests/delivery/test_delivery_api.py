from typing import Any
from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import reverse

from apps.delivery.services import NovaPoshtaClient, NovaPoshtaError

DNIPRO_SETTLEMENT_REF = "00000000-0000-4000-8000-000000000001"
DNIPRO_BRANCH_REF = "00000000-0000-4000-8000-000000000002"
DNIPRO_POSTOMAT_REF = "00000000-0000-4000-8000-000000000003"
CHORNOVOLA_STREET_REF = "00000000-0000-4000-8000-000000000004"
CHORNOVOLA_AVENUE_REF = "00000000-0000-4000-8000-000000000005"
DNIPRO_DELIVERY_CITY_REF = "00000000-0000-4000-8000-000000000006"


def api_answer(
    data: Any = None,
    success: bool = True,
    errors: list[Any] | None = None,
    warnings: list[Any] | None = None,
    **kwargs: Any,
) -> Mock:
    mock_response = Mock()
    mock_response.status_code = kwargs.get("status_code", 200)
    mock_response.json.return_value = {
        "success": success,
        "data": data if data is not None else [],
        "errors": errors if errors is not None else [],
        "warnings": warnings if warnings is not None else [],
    }
    return mock_response


class NovaPoshtaClientTests(SimpleTestCase):
    def setUp(self) -> None:
        cache.clear()
        self.client_instance = NovaPoshtaClient(
            settings.NOVA_POSHTA_API_KEY,
            settings.NOVA_POSHTA_API_URL,
        )

    def test_city_search_uses_settlement_refs_and_maps_response(self) -> None:
        response = api_answer(
            [
                {
                    "Ref": DNIPRO_SETTLEMENT_REF,
                    "Description": "Дніпро",
                    "AreaDescription": "Дніпропетровська",
                    "SettlementType": "city-type",
                }
            ]
        )
        delivery_cities_response = api_answer(
            [
                {
                    "Ref": DNIPRO_DELIVERY_CITY_REF,
                    "Description": "Дніпро",
                    "AreaDescription": "Дніпропетровська",
                    "SettlementType": "city-type",
                }
            ]
        )
        with self.patch_requests(
            side_effect=[response, delivery_cities_response, api_answer()]
        ) as post:
            cities = self.client_instance.search_cities("Дні")
            self.client_instance.search_warehouses(
                cities[0].delivery_city_ref,
                postomat=True,
            )

        settlement_payload = post.call_args_list[0].kwargs["json"]
        delivery_city_payload = post.call_args_list[1].kwargs["json"]
        self.assertEqual(settlement_payload["apiKey"], settings.NOVA_POSHTA_API_KEY)
        self.assertEqual(post.call_args.kwargs["timeout"], 15)
        self.assertEqual(
            (settlement_payload["modelName"], settlement_payload["calledMethod"]),
            ("AddressGeneral", "getSettlements"),
        )
        self.assertEqual(
            settlement_payload["methodProperties"],
            {"FindByString": "Дні", "Warehouse": "1", "Limit": "10"},
        )
        self.assertEqual(
            (delivery_city_payload["modelName"], delivery_city_payload["calledMethod"]),
            ("Address", "getCities"),
        )
        warehouse_payload = post.call_args_list[2].kwargs["json"]
        self.assertEqual(
            warehouse_payload["methodProperties"]["CityRef"],
            DNIPRO_DELIVERY_CITY_REF,
        )
        self.assertEqual(cities[0].ref, DNIPRO_SETTLEMENT_REF)
        self.assertEqual(cities[0].label, "Дніпро (Дніпропетровська обл.)")
        self.assertEqual(cities[0].delivery_city_ref, DNIPRO_DELIVERY_CITY_REF)

    def test_warehouse_search_filters_by_requested_type(self) -> None:
        common = {
            "CityRef": DNIPRO_SETTLEMENT_REF,
            "CityDescription": "Дніпро",
            "Number": "1",
        }
        response = api_answer(
            [
                common
                | {
                    "Ref": DNIPRO_BRANCH_REF,
                    "Description": "Відділення №1",
                    "CategoryOfWarehouse": "Branch",
                },
                common
                | {
                    "Ref": DNIPRO_POSTOMAT_REF,
                    "Description": "Поштомат №1",
                    "CategoryOfWarehouse": "Postomat",
                },
            ]
        )
        with self.patch_requests(response) as post:
            branches = self.client_instance.search_warehouses(DNIPRO_SETTLEMENT_REF)
            postomats = self.client_instance.search_warehouses(
                DNIPRO_SETTLEMENT_REF, postomat=True
            )

        self.assertEqual([item.ref for item in branches], [DNIPRO_BRANCH_REF])
        self.assertEqual([item.ref for item in postomats], [DNIPRO_POSTOMAT_REF])
        properties = post.call_args.kwargs["json"]["methodProperties"]
        self.assertEqual(
            properties["TypeOfWarehouseRef"],
            "f9316480-5f2d-425d-bc2c-ac7cd29decf0",
        )

    def test_street_search_maps_flat_api_response(self) -> None:
        response = api_answer(
            [
                {
                    "SettlementStreetRef": CHORNOVOLA_STREET_REF,
                    "SettlementStreetDescription": "Чорновола",
                    "StreetsTypeDescription": "вул.",
                },
                {
                    "SettlementStreetRef": CHORNOVOLA_AVENUE_REF,
                    "SettlementStreetDescription": "Чорновола",
                    "StreetsTypeDescription": "бульв.",
                },
            ]
        )
        with self.patch_requests(response) as post:
            streets = self.client_instance.search_streets(DNIPRO_SETTLEMENT_REF, "Чор")

        payload = post.call_args.kwargs["json"]
        self.assertEqual(
            (payload["modelName"], payload["calledMethod"]),
            ("Address", "searchSettlementStreets"),
        )
        self.assertEqual(
            payload["methodProperties"],
            {
                "StreetName": "Чор",
                "SettlementRef": DNIPRO_SETTLEMENT_REF,
                "Limit": "10",
            },
        )
        self.assertEqual(
            [(street.ref, street.label) for street in streets],
            [
                (CHORNOVOLA_STREET_REF, "вул. Чорновола"),
                (CHORNOVOLA_AVENUE_REF, "бульв. Чорновола"),
            ],
        )

    def test_no_matching_city_is_an_empty_result(self) -> None:
        response = api_answer(
            [], success=False, errors=["FindByString is not specified"]
        )
        with self.patch_requests(side_effect=[response, response]):
            cities = self.client_instance.search_cities("Qqqzz")
        self.assertEqual(cities, [])

    def test_client_surfaces_api_and_network_errors(self) -> None:
        api_error = api_answer([], success=False, errors=["API key is invalid"])
        with (
            self.patch_requests(api_error),
            self.assertRaisesRegex(NovaPoshtaError, "API key is invalid"),
        ):
            self.client_instance.search_cities("Київ")

        with (
            self.patch_requests(side_effect=requests.ConnectionError("offline")),
            self.assertRaises(NovaPoshtaError),
        ):
            self.client_instance.search_cities("Київ")

    def test_client_without_api_key_does_not_call_provider(self) -> None:
        with (
            self.patch_requests() as post,
            self.assertRaises(NovaPoshtaError),
        ):
            NovaPoshtaClient("", settings.NOVA_POSHTA_API_URL).search_cities("Київ")
        post.assert_not_called()

    @staticmethod
    def patch_requests(response: Mock | None = None, **kwargs: Any) -> Any:
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
            City(
                DNIPRO_SETTLEMENT_REF,
                "Дніпро",
                "Дніпропетровська",
                DNIPRO_DELIVERY_CITY_REF,
            )
        ]
        response = self.client.get(reverse("delivery:cities"), {"q": "Дні"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "ref": DNIPRO_SETTLEMENT_REF,
                        "name": "Дніпро",
                        "area": "Дніпропетровська",
                        "delivery_city_ref": DNIPRO_DELIVERY_CITY_REF,
                        "label": "Дніпро (Дніпропетровська обл.)",
                    }
                ]
            },
        )

    def test_warehouse_endpoint_filters_and_rejects_invalid_type(self) -> None:
        from apps.delivery.services import Warehouse

        self.nova_client.search_warehouses.return_value = [
            Warehouse(
                DNIPRO_BRANCH_REF,
                DNIPRO_SETTLEMENT_REF,
                "Дніпро",
                "1",
                "Відділення №1",
                False,
            )
        ]
        url = reverse("delivery:warehouses")
        response = self.client.get(url, {"city": DNIPRO_SETTLEMENT_REF})
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "ref": DNIPRO_BRANCH_REF,
                        "city_ref": DNIPRO_SETTLEMENT_REF,
                        "city_name": "Дніпро",
                        "number": "1",
                        "name": "Відділення №1",
                        "is_postomat": False,
                    }
                ]
            },
        )
        self.nova_client.search_warehouses.assert_called_once_with(
            DNIPRO_SETTLEMENT_REF, "", postomat=False
        )

        response = self.client.get(
            url, {"city": DNIPRO_SETTLEMENT_REF, "type": "unknown"}
        )
        self.assertEqual(response.status_code, 400)

    def test_street_endpoint_returns_matching_streets(self) -> None:
        from apps.delivery.services import Street

        self.nova_client.search_streets.return_value = [
            Street(CHORNOVOLA_STREET_REF, "Чорновола", "вул.")
        ]
        response = self.client.get(
            reverse("delivery:streets"),
            {"city": DNIPRO_SETTLEMENT_REF, "q": "Чор"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [
                    {
                        "ref": CHORNOVOLA_STREET_REF,
                        "name": "Чорновола",
                        "street_type": "вул.",
                        "label": "вул. Чорновола",
                    }
                ]
            },
        )
        self.nova_client.search_streets.assert_called_once_with(
            DNIPRO_SETTLEMENT_REF, "Чор"
        )

    def test_street_endpoint_rejects_short_queries_without_calling_provider(
        self,
    ) -> None:
        response = self.client.get(
            reverse("delivery:streets"),
            {"city": DNIPRO_SETTLEMENT_REF, "q": "в"},
        )

        self.assertEqual(response.status_code, 400)
        self.nova_client.search_streets.assert_not_called()

    def test_empty_street_results_are_not_cached(self) -> None:
        from apps.delivery.services import Street

        self.nova_client.search_streets.side_effect = [
            [],
            [Street(CHORNOVOLA_AVENUE_REF, "Чорновола", "бульв.")],
        ]
        url = reverse("delivery:streets")
        params = {"city": DNIPRO_SETTLEMENT_REF, "q": "Чор"}

        empty_response = self.client.get(url, params)
        found_response = self.client.get(url, params)

        self.assertEqual(empty_response.json(), {"results": []})
        self.assertEqual(
            found_response.json()["results"][0]["ref"], CHORNOVOLA_AVENUE_REF
        )
        self.assertEqual(self.nova_client.search_streets.call_count, 2)

    def test_street_provider_failure_returns_service_unavailable(self) -> None:
        from apps.delivery.services import NovaPoshtaError

        self.nova_client.search_streets.side_effect = NovaPoshtaError("offline")
        response = self.client.get(
            reverse("delivery:streets"),
            {"city": DNIPRO_SETTLEMENT_REF, "q": "Чор"},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("detail", response.json())

    def test_provider_outage_returns_service_unavailable(self) -> None:
        self.nova_client.search_cities.side_effect = NovaPoshtaError("offline")
        response = self.client.get(reverse("delivery:cities"), {"q": "Київ"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("detail", response.json())

    def test_warehouse_provider_error_is_logged_without_api_key(self) -> None:
        from apps.delivery.services import NovaPoshtaError

        self.nova_client.search_warehouses.side_effect = NovaPoshtaError(
            f"provider rejected key {settings.NOVA_POSHTA_API_KEY}"
        )

        with self.assertLogs("apps.delivery.views", level="WARNING") as logs:
            response = self.client.get(
                reverse("delivery:warehouses"),
                {"city": DNIPRO_SETTLEMENT_REF, "type": "branch"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("[redacted]", logs.output[0])
        self.assertNotIn(settings.NOVA_POSHTA_API_KEY, logs.output[0])
