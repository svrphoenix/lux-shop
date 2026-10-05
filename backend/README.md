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

## Authentication and password recovery

`POST /api/v1/auth/login/` accepts `username` as either the account username
or its email address, together with `password`.

* `POST /api/v1/auth/password-reset/` accepts `{"email": "..."}` and sends a
  single-use reset link when the address belongs to an active account. The same
  response is returned when no account matches.
* `POST /api/v1/auth/password-reset/confirm/` accepts `uid`, `token`,
  `new_password`, and `new_password_confirm` from that link.
* The reset link opens the frontend `/reset-password/` page. Its host comes from
  `FRONTEND_URL`; ensure this is set to the frontend URL for the current local or
  development setup.

Reset requests are limited to five per hour per client IP. Reset emails use the
configured `DEFAULT_FROM_EMAIL` and the active email backend.

## Nova Poshta delivery API

Set `NOVA_POSHTA_API_KEY` in `.env.local` or `.env.dev`. The API URL defaults to
`https://api.novaposhta.ua/v2.0/json/` and can be overridden with
`NOVA_POSHTA_API_URL`.

* `GET /api/v1/delivery/cities/?q=<query>` searches cities (minimum two characters). Each result has `ref` (settlement reference) and `delivery_city_ref` (reference used for warehouse searches).
* `GET /api/v1/delivery/warehouses/?city=<delivery-city-ref>&type=branch|postomat&q=<query>` searches branches or parcel lockers for a city. Use the city's `delivery_city_ref`, not its `ref`; `type` defaults to `branch` and `q` is optional.
* `GET /api/v1/delivery/streets/?city=<settlement-ref>&q=<query>` searches streets for courier delivery (minimum two characters). Use the city's `ref`.

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

## Order email notifications (local/development)

Order confirmation and shop-admin notification use Resend's SMTP interface.
Set these values in `.env.local` or `.env.dev`:

* `RESEND_API_KEY` — API key from Resend.
* `RESEND_FROM_EMAIL` — bare sender email address on a domain verified in Resend.
  It is used for Django's `DEFAULT_FROM_EMAIL`, the shared sender for application
  email. Password-reset email delivery is not implemented yet.
* `SHOP_ADMIN_EMAIL` — address that receives new-order notifications.
* `SITE_NAME` — optional sender display name; defaults to `LuxShop Store`.

Resend SMTP uses `smtp.resend.com:587` with STARTTLS and the username `resend`.
When `RESEND_API_KEY` is empty, Django prints emails to the backend console
instead. No production email configuration is included.

Both messages are scheduled after the checkout transaction commits. An email
delivery failure is logged and does not undo a successfully created order.
Tests use Django's in-memory email backend and do not send real emails.
