# Modular Django E-Commerce Backend

A robust, production-ready e-commerce RESTful API designed with clean architecture principles, modular domain isolation (`apps/`), and modern Python tooling (`uv`, `ruff`).

## 🚀 Key Features

* **Modular Domain Architecture:** Strictly isolated domain modules (`users`, `products`, `reviews`, `core`) using `apps.` namespace registration.
* **Tiered Settings Strategy:** Separated environments (`base.py`, `local.py`, `prod.py`) powered by `django-environ` and `.env.local`.
* **Optimized Database Queries:** Mitigation of N+1 query bottlenecks across models and admin panels using `list_select_related` and custom query optimizations.
* **Hierarchical Category System:** Self-referential product categories supporting multi-level nested catalog structures.
* **Health Check & Monitoring:** Lightweight DB connectivity endpoint (`/api/health/`) optimized for uptime monitors and orchestrators.
* **Automated Code Quality:** Integrated `pre-commit` hooks using `ruff` and `ruff-format` for linting and code formatting.

## 🛠️ Tech Stack

* **Framework:** Python 3.12+ / Django 6.1 / Django REST Framework
* **Database:** PostgreSQL
* **Dependency & Package Management:** `uv`
* **Code Quality:** Ruff, Pre-commit