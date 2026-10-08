# Hop & Barley frontend

The storefront for Hop & Barley, built with Next.js App Router, React, and
TypeScript. It uses the Django REST API in `../backend` for catalogue, account,
cart, delivery, and order data.

## Features

- Product catalogue with search, category, price, stock, and ordering filters.
- Product detail pages with reviews and add-to-cart actions.
- Shopping cart and checkout with delivery and payment selection.
- Account registration, sign-in, profile and password management.
- Profile avatars with preset choices and custom image uploads.
- Password recovery by email.
- Responsive navigation and storefront pages.

## Requirements

- Docker Engine and Docker Compose v2 to run the complete stack.
- Node.js 20.9 or later and npm only when running the frontend directly on the
  host.
- The standalone backend setup is documented in
  [the backend README](../backend/README.md).

## Getting started

### Run the complete shop in Docker

From the repository root:

```sh
cp backend/.env.dev.example backend/.env.dev
docker compose up --build
```

The root Compose file starts PostgreSQL, the Django API, Next.js, and Caddy.
Open [http://localhost:8080](http://localhost:8080). Only Caddy is published
to the host; the frontend and backend communicate on the private Compose
network. API, Django admin, static, and uploaded media requests go to the
backend, while other routes go to the frontend.
The Django admin is available at
[http://localhost:8080/admin/](http://localhost:8080/admin/).

The backend container uses `config.settings.dev` and the settings in
`backend/.env.dev`. Keep secrets in that ignored local file. To change the
local proxy port:

```sh
DEV_PORT=8081 docker compose up --build
```

The frontend source is bind-mounted for live development. Its `node_modules`
are kept in a Docker volume so host dependencies do not mask the container's
Linux dependencies. On startup, the frontend compares the volume's recorded
lockfile hash with `package-lock.json` and runs `npm ci` only when they differ.
Thus dependency changes are picked up after restarting the frontend service;
the named volume does not need to be manually cleared.

The backend can also be run independently using its own Compose configuration:

```sh
cd backend
docker compose up --build
```

That standalone backend stack publishes the API directly on port `8008` by
default, including the admin at
[http://localhost:8008/admin/](http://localhost:8008/admin/); it does not
require or start the frontend.

### Run the frontend directly on the host

```sh
cd frontend
npm ci
cp .env.local.example .env.local
npm run dev
```

The example environment file targets the standalone backend's default host
port. `NEXT_PUBLIC_API_URL` is used by browser requests, while
`INTERNAL_API_URL` can set the API URL for server-rendered requests. In the
complete Docker Compose stack, Compose routes browser API requests through
Caddy and server-rendered requests directly to the backend container.

Open [http://localhost:3000](http://localhost:3000). The frontend expects the
backend API to be running at the configured URL.

## Available scripts

```sh
npm run dev        # Start the Next.js development server
npm run build      # Build the production bundle
npm run start      # Serve the production build
npm run lint       # Run ESLint
npm run typecheck  # Run the TypeScript compiler without emitting files
```

Run `npm run build` before `npm run start`.

## Main routes

| Route | Description |
| --- | --- |
| `/` | Product catalogue and filters |
| `/products/[slug]` | Product details and reviews |
| `/cart` | Shopping cart |
| `/checkout` | Delivery and payment checkout |
| `/login` | Sign in |
| `/register` | Create an account |
| `/forgot-password` | Request a password-reset link |
| `/reset-password` | Set a new password from a reset link |
| `/account` | Account profile and order history |
| `/account/password` | Change account password |

## Static assets

Storefront assets are served from `public/`; for example, `public/img/logo.svg`
is available at `/img/logo.svg`. Product and other images can also be provided
by the backend API.
