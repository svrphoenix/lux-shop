"""Client for Nova Poshta API 2.0 city, warehouse, and street search."""

from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

POSTOMAT_TYPE_REF = "f9316480-5f2d-425d-bc2c-ac7cd29decf0"
NO_RESULTS_ERROR = "FindByString is not specified"
NOVA_POSHTA_REQUEST_TIMEOUT = 15


class NovaPoshtaError(Exception):
    """The Nova Poshta API is unavailable or returned an invalid response."""


@dataclass(frozen=True)
class City:
    ref: str
    name: str
    area: str
    delivery_city_ref: str = ""

    @property
    def label(self) -> str:
        return f"{self.name} ({self.area} обл.)" if self.area else self.name


@dataclass(frozen=True)
class Warehouse:
    ref: str
    city_ref: str
    city_name: str
    number: str
    name: str
    is_postomat: bool


@dataclass(frozen=True)
class Street:
    ref: str
    name: str
    street_type: str

    @property
    def label(self) -> str:
        return (
            f"{self.street_type} {self.name}".strip() if self.street_type else self.name
        )


class NovaPoshtaClient:
    def __init__(
        self,
        api_key: str,
        api_url: str,
        timeout: float = NOVA_POSHTA_REQUEST_TIMEOUT,
    ) -> None:
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    def call(self, model: str, method: str, **properties: Any) -> list[dict[str, Any]]:
        if not self.api_key:
            raise NovaPoshtaError("NOVA_POSHTA_API_KEY is not configured.")

        payload: dict[str, Any] = {
            "apiKey": self.api_key,
            "modelName": model,
            "calledMethod": method,
            "methodProperties": properties,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as error:
            raise NovaPoshtaError(f"Nova Poshta API request failed: {error}") from error

        if not isinstance(body, dict):
            raise NovaPoshtaError("Nova Poshta API returned an invalid response.")

        if not body.get("success"):
            errors = body.get("errors") or []
            if NO_RESULTS_ERROR in errors:
                return []
            raise NovaPoshtaError(
                "; ".join(str(error) for error in errors)
                or "Nova Poshta API returned an unknown error."
            )

        data = body.get("data")
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise NovaPoshtaError("Nova Poshta API returned invalid result data.")
        return data

    def search_cities(self, query: str, limit: int = 10) -> list[City]:
        settlement_rows = self.call(
            "AddressGeneral",
            "getSettlements",
            FindByString=query,
            Warehouse="1",
            Limit=str(limit),
        )
        delivery_city_rows = self.call(
            "Address",
            "getCities",
            FindByString=query,
            Limit=str(limit),
        )
        delivery_city_refs = {
            (
                row.get("Description", "").casefold(),
                row.get("AreaDescription", "").casefold(),
                row.get("SettlementType", ""),
            ): row.get("Ref", "")
            for row in delivery_city_rows
        }
        try:
            return [
                City(
                    ref=row["Ref"],
                    name=row["Description"],
                    area=row.get("AreaDescription", ""),
                    delivery_city_ref=delivery_city_refs.get(
                        (
                            row["Description"].casefold(),
                            row.get("AreaDescription", "").casefold(),
                            row.get("SettlementType", ""),
                        ),
                        "",
                    ),
                )
                for row in settlement_rows
            ]
        except (KeyError, TypeError) as error:
            raise NovaPoshtaError("Nova Poshta returned invalid city data.") from error

    def search_warehouses(
        self,
        city_ref: str,
        query: str = "",
        postomat: bool = False,
        limit: int = 20,
    ) -> list[Warehouse]:
        # Request a larger batch from NP API to avoid losing items after type filtering
        api_limit = max(limit * 3, 50)
        properties: dict[str, str] = {
            "CityRef": city_ref,
            "FindByString": query,
            "Limit": str(api_limit),
        }
        if postomat:
            properties["TypeOfWarehouseRef"] = POSTOMAT_TYPE_REF

        rows = self.call("Address", "getWarehouses", **properties)
        try:
            warehouses = [self._warehouse(row) for row in rows]
        except (KeyError, TypeError) as error:
            raise NovaPoshtaError(
                "Nova Poshta returned invalid warehouse data."
            ) from error

        return [
            warehouse for warehouse in warehouses if warehouse.is_postomat == postomat
        ][:limit]

    def search_streets(
        self,
        city_ref: str,
        query: str,
        limit: int = 10,
    ) -> list[Street]:
        rows = self.call(
            "Address",
            "searchSettlementStreets",
            StreetName=query,
            SettlementRef=city_ref,
            Limit=str(limit),
        )
        try:
            street_list = []
            for row in rows:
                addresses = row.get("Addresses")
                if addresses is None:
                    street_list.append(row)
                elif isinstance(addresses, list):
                    street_list.extend(addresses)
                else:
                    raise TypeError("Nova Poshta returned invalid street addresses.")

            return [
                Street(
                    ref=item["SettlementStreetRef"],
                    name=item["SettlementStreetDescription"],
                    street_type=item.get("StreetsTypeDescription", ""),
                )
                for item in street_list
            ][:limit]
        except (KeyError, TypeError, IndexError) as error:
            raise NovaPoshtaError(
                "Nova Poshta returned invalid street data."
            ) from error

    @staticmethod
    def _warehouse(row: dict[str, Any]) -> Warehouse:
        return Warehouse(
            ref=row["Ref"],
            city_ref=row["CityRef"],
            city_name=row.get("CityDescription", ""),
            number=row.get("Number", ""),
            name=row["Description"],
            is_postomat=row.get("CategoryOfWarehouse") == "Postomat",
        )


def get_client() -> NovaPoshtaClient:
    return NovaPoshtaClient(settings.NOVA_POSHTA_API_KEY, settings.NOVA_POSHTA_API_URL)
