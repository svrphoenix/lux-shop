# Hop & Barley

Hop & Barley is an e-commerce application for brewing ingredients. The project
contains a Django REST API and a Next.js storefront. The backend can run on its
own or together with the frontend behind Caddy.

## Technology

- **Backend:** Python, Django, Django REST Framework, PostgreSQL, `uv`
- **Frontend:** Next.js, React, TypeScript, npm
- **Development orchestration:** Docker Compose
- **Reverse proxy:** Caddy

## Run the complete shop with Docker

Requirements: Docker Engine and Docker Compose v2.

From the repository root, create the development environment file and start the
stack:

```sh
cp backend/.env.dev.example backend/.env.dev
```

Edit `backend/.env.dev` before starting. Set a non-placeholder Django
`SECRET_KEY` and database password. To create a development Django
superuser automatically, set all three `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_EMAIL`, and `DJANGO_SUPERUSER_PASSWORD` values. These
credentials belong in `backend/.env.dev`, not in a root `.env` file.

Start the services:

```sh
docker compose up --build
```

Open the storefront at [http://localhost:8080](http://localhost:8080). Caddy
routes `/api/`, `/admin/`, `/media/`, and `/static/` requests to Django and
routes all other paths to Next.js. Only Caddy is exposed to the host; the
application containers communicate over the private Compose network.

The admin interface is at [http://localhost:8080/admin/](http://localhost:8080/admin/).
API documentation is available at
[http://localhost:8080/api/docs/](http://localhost:8080/api/docs/), and the
health endpoint is [http://localhost:8080/api/health/](http://localhost:8080/api/health/).

To use a different local port for Caddy, set `DEV_PORT` when starting Compose:

```sh
DEV_PORT=8081 docker compose up --build
```

Stop the services with `docker compose down`. Named volumes keep the database
and uploaded media between restarts.

## Run the backend independently

The backend has its own Compose configuration and does not require the
frontend. See [backend/README.md](backend/README.md) for backend settings,
tests, and API details.

The standalone backend stack reads `backend/.env.dev` for Django and database
settings. Its host port is controlled by `HOST_PORT` in `backend/.env`, which
is only used for Compose interpolation:

```sh
cp backend/.env.example backend/.env
cp backend/.env.dev.example backend/.env.dev
cd backend
docker compose up --build
```

By default, the API and admin are available on port `8008`, for example
[http://localhost:8008/admin/](http://localhost:8008/admin/).

## Run the frontend directly on the host

The backend must be running and reachable at the API URLs configured for the
frontend. See [frontend/README.md](frontend/README.md) for environment
variables, setup, and available npm scripts.

```sh
cd frontend
npm ci
cp .env.local.example .env.local
npm run dev
```

## Project documentation

- [Backend setup, API, and testing](backend/README.md)
- [Frontend setup and routes](frontend/README.md)
