FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]