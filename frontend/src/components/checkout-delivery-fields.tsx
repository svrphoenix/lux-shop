"use client";

import {
  searchDeliveryCities,
  searchDeliveryStreets,
  searchDeliveryWarehouses,
} from "@/lib/client-api";
import type {
  DeliveryCity,
  DeliveryStreet,
  DeliveryWarehouse,
} from "@/lib/types";
import { useEffect, useState } from "react";

type DeliveryMethod = "branch" | "postomat" | "courier";

export function CheckoutDeliveryFields() {
  const [cityQuery, setCityQuery] = useState("");
  const [city, setCity] = useState<DeliveryCity | null>(null);
  const [cities, setCities] = useState<DeliveryCity[]>([]);
  const [deliveryMethod, setDeliveryMethod] =
    useState<DeliveryMethod>("branch");
  const [warehouseQuery, setWarehouseQuery] = useState("");
  const [warehouses, setWarehouses] = useState<DeliveryWarehouse[]>([]);
  const [warehouse, setWarehouse] = useState<DeliveryWarehouse | null>(null);
  const [streetQuery, setStreetQuery] = useState("");
  const [streets, setStreets] = useState<DeliveryStreet[]>([]);
  const [street, setStreet] = useState<DeliveryStreet | null>(null);
  const [hasSearchedStreets, setHasSearchedStreets] = useState(false);
  const [houseNumber, setHouseNumber] = useState("");
  const [apartment, setApartment] = useState("");
  const [isSearchingCities, setIsSearchingCities] = useState(false);
  const [isSearchingAddress, setIsSearchingAddress] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    if (cityQuery.trim().length < 2 || city?.label === cityQuery) {
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setIsSearchingCities(true);
      setSearchError(null);
      void searchDeliveryCities(cityQuery.trim(), controller.signal)
        .then((response) => setCities(response.results))
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setSearchError(
              error instanceof Error ? error.message : "Unable to search cities.",
            );
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsSearchingCities(false);
          }
        });
    }, 300);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [city?.label, cityQuery]);

  useEffect(() => {
    if (!city || deliveryMethod === "courier") {
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setIsSearchingAddress(true);
      setSearchError(null);
      void searchDeliveryWarehouses(
        city.delivery_city_ref,
        warehouseQuery.trim(),
        deliveryMethod,
        controller.signal,
      )
        .then((response) => setWarehouses(response.results))
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setSearchError(
              error instanceof Error
                ? error.message
                : "Unable to search delivery locations.",
            );
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsSearchingAddress(false);
          }
        });
    }, 300);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [city, deliveryMethod, warehouseQuery]);

  useEffect(() => {
    if (!city || deliveryMethod !== "courier" || streetQuery.trim().length < 2) {
      return;
    }

    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      setIsSearchingAddress(true);
      setSearchError(null);
      setStreets([]);
      setHasSearchedStreets(false);
      void searchDeliveryStreets(
        city.ref,
        streetQuery.trim(),
        controller.signal,
      )
        .then((response) => {
          setStreets(response.results);
          setHasSearchedStreets(true);
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            setSearchError(
              error instanceof Error ? error.message : "Unable to search streets.",
            );
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsSearchingAddress(false);
          }
        });
    }, 300);

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [city, deliveryMethod, streetQuery]);

  const address = warehouse
    ? `${deliveryMethod === "postomat" ? "Nova Poshta postomat" : "Nova Poshta branch"}: ${warehouse.name}`
    : street && houseNumber.trim()
      ? `Courier delivery: ${street.label}, ${houseNumber.trim()}${apartment.trim() ? `, apt. ${apartment.trim()}` : ""}`
      : "";

  const selectCity = (selectedCity: DeliveryCity) => {
    setCity(selectedCity);
    setCityQuery(selectedCity.label);
    setIsSearchingCities(false);
    setIsSearchingAddress(false);
    setCities([]);
    setWarehouses([]);
    setStreets([]);
    setWarehouse(null);
    setWarehouseQuery("");
    setStreet(null);
    setStreetQuery("");
    setHouseNumber("");
    setApartment("");
    setHasSearchedStreets(false);
  };

  const changeDeliveryMethod = (method: DeliveryMethod) => {
    setDeliveryMethod(method);
    setIsSearchingAddress(false);
    setWarehouse(null);
    setWarehouseQuery("");
    setWarehouses([]);
    setStreet(null);
    setStreetQuery("");
    setStreets([]);
    setHouseNumber("");
    setApartment("");
    setHasSearchedStreets(false);
  };

  return (
    <fieldset className="delivery-fields">
      <legend>Delivery address</legend>
      <label>
        City
        <input
          autoComplete="off"
          onChange={(event) => {
            setCityQuery(event.target.value);
            setCity(null);
            setWarehouse(null);
            setStreet(null);
            setHouseNumber("");
            setIsSearchingCities(false);
            setIsSearchingAddress(false);
          }}
          placeholder="Start typing a city"
          value={cityQuery}
        />
      </label>
      {isSearchingCities ? <p className="muted delivery-hint">Searching cities…</p> : null}
      {cityQuery.trim().length >= 2 && city?.label !== cityQuery && cities.length ? (
        <ul className="delivery-options" aria-label="Matching cities">
          {cities.map((option) => (
            <li key={option.ref}>
              <button onClick={() => selectCity(option)} type="button">
                {option.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {city ? (
        <>
          <label>
            Delivery method
            <select
              onChange={(event) =>
                changeDeliveryMethod(event.target.value as DeliveryMethod)
              }
              value={deliveryMethod}
            >
              <option value="branch">Nova Poshta branch</option>
              <option value="postomat">Nova Poshta postomat</option>
              <option value="courier">Courier delivery</option>
            </select>
          </label>
          {deliveryMethod !== "courier" ? (
            <>
              <label>
                Search {deliveryMethod === "postomat" ? "postomats" : "branches"}
                <input
                  autoComplete="off"
                  onChange={(event) => {
                    setWarehouseQuery(event.target.value);
                    setWarehouse(null);
                    setIsSearchingAddress(false);
                  }}
                  placeholder="Search by number or address"
                  value={warehouseQuery}
                />
              </label>
              {warehouse ? (
                <div className="delivery-selection" role="status">
                  <div>
                    <span className="delivery-selection-label">Selected delivery location</span>
                    <strong>{warehouse.name}</strong>
                  </div>
                  <button
                    className="delivery-selection-change"
                    onClick={() => setWarehouse(null)}
                    type="button"
                  >
                    Change
                  </button>
                </div>
              ) : warehouses.length ? (
                <ul className="delivery-options" aria-label="Delivery locations">
                  {warehouses.map((option) => (
                    <li key={option.ref}>
                      <button
                        aria-label={`Select ${option.name}`}
                        onClick={() => setWarehouse(option)}
                        type="button"
                      >
                        {option.name}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : isSearchingAddress ? (
                <p className="muted delivery-hint">Searching delivery locations…</p>
              ) : null}
            </>
          ) : (
            <>
              <label>
                Street
                <input
                  autoComplete="off"
                  onChange={(event) => {
                    setStreetQuery(event.target.value);
                    setStreet(null);
                    setStreets([]);
                    setHasSearchedStreets(false);
                    setHouseNumber("");
                    setIsSearchingAddress(false);
                  }}
                  placeholder="Start typing a street"
                  value={streetQuery}
                />
              </label>
              {street ? (
                <div className="delivery-selection" role="status">
                  <div>
                    <span className="delivery-selection-label">Selected street</span>
                    <strong>{street.label}</strong>
                  </div>
                  <button
                    className="delivery-selection-change"
                    onClick={() => {
                      setStreet(null);
                      setHouseNumber("");
                    }}
                    type="button"
                  >
                    Change
                  </button>
                </div>
              ) : streetQuery.trim().length >= 2 && streets.length ? (
                <ul className="delivery-options" aria-label="Matching streets">
                  {streets.map((option) => (
                    <li key={option.ref}>
                      <button
                        onClick={() => setStreet(option)}
                        type="button"
                      >
                        {option.label}
                      </button>
                    </li>
                  ))}
                </ul>
              ) : isSearchingAddress ? (
                <p className="muted delivery-hint">Searching streets…</p>
              ) : hasSearchedStreets && streetQuery.trim().length >= 2 ? (
                <p className="muted delivery-hint">No matching streets found.</p>
              ) : null}
              {street ? (
                <div className="delivery-house-fields">
                  <label>
                    House number
                    <input
                      onChange={(event) => setHouseNumber(event.target.value)}
                      required
                      value={houseNumber}
                    />
                  </label>
                  <label>
                    Apartment (optional)
                    <input
                      onChange={(event) => setApartment(event.target.value)}
                      value={apartment}
                    />
                  </label>
                </div>
              ) : null}
            </>
          )}
        </>
      ) : null}
      {searchError ? <p className="info-panel error-panel">{searchError}</p> : null}
      <input name="city" type="hidden" value={city?.label ?? ""} />
      <input name="address" type="hidden" value={address} />
    </fieldset>
  );
}
