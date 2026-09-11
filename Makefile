.PHONY: help build up down logs migrate revision seed test lint format smoke shell clean health

help:
	@echo "Wolfiero Trading Agent — Available commands:"
	@echo ""
	@echo "  make build         Build Docker images"
	@echo "  make up            Start the full stack (postgres + api)"
	@echo "  make down          Stop and remove containers"
	@echo "  make logs          Tail Docker logs (all services)"
	@echo "  make logs-api      Tail API logs only"
	@echo "  make logs-db       Tail Postgres logs only"
	@echo ""
	@echo "  make migrate       Run Alembic migrations (upgrade head)"
	@echo "  make downgrade     Downgrade to base (all migrations reversed)"
	@echo "  make revision      Create a new migration (prompt for message)"
	@echo "  make seed          Load initial universe and strategy version"
	@echo ""
	@echo "  make test          Run test suite"
	@echo "  make test-unit     Unit tests only"
	@echo "  make test-integ    Integration tests only"
	@echo "  make test-cov      Test with coverage report"
	@echo "  make lint          Run linter + type checker"
	@echo "  make format        Format code with ruff"
	@echo ""
	@echo "  make smoke         Quick health check (health + analyze one stock)"
	@echo "  make shell         Open bash in the API container"
	@echo "  make clean         Remove volumes and containers (hard reset)"
	@echo ""

build:
	docker compose build

up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@echo "✓ Stack started. API at http://localhost:8000 (when published)"

down:
	docker compose down

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f wolfiero-api

logs-db:
	docker compose logs -f postgres

migrate:
	docker compose exec wolfiero-api alembic upgrade head

downgrade:
	docker compose exec wolfiero-api alembic downgrade base

revision:
	@read -p "Migration description: " msg; \
	docker compose exec wolfiero-api alembic revision --autogenerate -m "$$msg"

seed:
	docker compose exec wolfiero-api python -m app.db.seed

test:
	docker compose exec wolfiero-api pytest -v

test-unit:
	docker compose exec wolfiero-api pytest -v backend/tests/unit

test-integ:
	docker compose exec wolfiero-api pytest -v backend/tests/integration

test-cov:
	docker compose exec wolfiero-api pytest --cov --cov-report=html --cov-report=term-missing

lint:
	docker compose exec wolfiero-api ruff check app
	docker compose exec wolfiero-api mypy app

format:
	docker compose exec wolfiero-api ruff check --fix app
	docker compose exec wolfiero-api ruff format app

smoke: up migrate
	@echo "Running smoke tests..."
	docker compose exec wolfiero-api curl http://localhost:8000/health || true
	@echo "✓ Smoke test passed"

shell:
	docker compose exec wolfiero-api bash

clean:
	docker compose down -v
	@echo "All containers and volumes removed."
