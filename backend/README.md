# Modular Django E-Commerce Backend

A modular e-commerce REST API built with Django, domain apps under `apps/`, and modern Python tooling (`uv`, `ruff`).

## 🚀 Key Features

* **Modular Domain Architecture:** Strictly isolated domain modules (`users`, `products`, `reviews`, `core`) using `apps.` namespace registration.
* **Tiered Settings Strategy:** Shared settings plus separate local, Docker development, and test modules powered by `django-environ`.
* **Optimized Database Queries:** Mitigation of N+1 query bottlenecks across models and admin panels using `list_select_related` and custom query optimizations.
* **Hierarchical Category System:** Self-referential product categories supporting multi-level nested catalog structures.
* **Health Check & Monitoring:** Lightweight DB connectivity endpoint (`/api/health/`) optimized for uptime monitors and orchestrators.
* **Nova Poshta Delivery:** Public city, branch, and parcel-locker search endpoints backed by Nova Poshta API 2.0, with 24-hour result caching.
* **Checkout Payments:** Simulated successful card payments and cash-on-delivery support; no real payment provider or card data is used.
* **Automated Code Quality:** Integrated `pre-commit` hooks using `ruff` and `ruff-format` for linting and code formatting.

## Local configuration

Copy the appropriate example file and replace its placeholder values:

* `.env.example` → `.env` for Docker Compose CLI interpolation only
  (`HOST_PORT`, `COMPOSE_PROJECT_NAME`). These values are not Django settings and
  are not passed into application containers.
* `.env.local.example` → `.env.local` for direct Django development
  (`config.settings.local`).
* `.env.dev.example` → `.env.dev` for the development Docker Compose stack
  (`config.settings.dev`).
* `.env.test.example` → `.env.test` for pytest
  (`config.settings.test`).

The Compose development stack expects `.env.dev`; its PostgreSQL container
credentials must match the database URL. Real credentials and API keys belong
only in ignored local env files, never in the example files.

For direct tests, start PostgreSQL on the host and port configured by
`.env.test`, then run `uv run pytest`. To use the isolated Docker test database:

```sh
docker compose --env-file .env.test -f docker-compose.test.yaml up \
  --build --abort-on-container-exit --exit-code-from tests
docker compose --env-file .env.test -f docker-compose.test.yaml down
```

The test Compose file requires the `POSTGRES_*` values from `.env.test` to
construct the database URL for the test container. Its `DATABASE_URL` value is
for tests run directly on the host.

The current Docker image and Compose configuration are for development/testing,
not production deployment. There is no production settings module yet.

Create a development superuser explicitly with
`docker compose exec backend uv run python manage.py createsuperuser`; the
container startup does not create or silently skip users.

## 🛠️ Tech Stack

* **Framework:** Python 3.12+ / Django 6.1 / Django REST Framework
* **Database:** PostgreSQL
* **Dependency & Package Management:** `uv`
* **Code Quality:** Ruff, Pre-commit

## REST API documentation

* OpenAPI schema: `GET /api/schema/`
* Swagger UI: `GET /api/docs/`

The schema describes the available API endpoints and request/response models.
For protected endpoints, obtain an access token from `POST /api/v1/auth/login/`
and authorize requests with `Authorization: Bearer <access-token>`. Public
endpoints do not require a token.

## Nova Poshta delivery API

Set `NOVA_POSHTA_API_KEY` in `.env.local` or `.env.dev`. The API URL defaults to
`https://api.novaposhta.ua/v2.0/json/` and can be overridden with
`NOVA_POSHTA_API_URL`.

* `GET /api/v1/delivery/cities/?q=<query>` searches cities (minimum two characters).
* `GET /api/v1/delivery/warehouses/?city=<city-ref>&type=branch|postomat&q=<query>` searches branches or parcel lockers for a city. `type` defaults to `branch`; `q` is optional.
* `GET /api/v1/delivery/streets/?city=<city-ref>&q=<query>` searches streets for courier delivery (minimum two characters).

Successful responses contain a `results` array. If Nova Poshta is unavailable,
the endpoints return `503 Service Unavailable`.

## Checkout payments

Include `payment_method` in `POST /api/v1/orders/checkout/`:

* `"card"` creates a **simulated successful** payment and marks the order as paid.
  No card number or other card details are collected.
* `"cash_on_delivery"` records a pending payment to be collected on delivery.
  This is also the default when `payment_method` is omitted.

The created order response includes a `payment` object with its method, status,
amount, currency, and whether the card payment was simulated. This mock must be
replaced by a real provider integration before accepting live card payments.