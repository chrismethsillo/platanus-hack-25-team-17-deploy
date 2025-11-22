.PHONY: help install dev run test lint lint-fix format format-all clean pre-commit pre-commit-all migrate upgrade downgrade db docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make dev              - Install dev dependencies and setup pre-commit"
	@echo "  make run              - Run the application"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage"
	@echo "  make lint             - Run linters (ruff, mypy) without fixing"
	@echo "  make lint-fix         - Run linters and auto-fix issues"
	@echo "  make format           - Format code (black, ruff)"
	@echo "  make format-all       - Format all files in project"
	@echo "  make pre-commit       - Run pre-commit hooks on changed files"
	@echo "  make pre-commit-all   - Run pre-commit hooks on all files"
	@echo "  make clean            - Clean cache and build files"
	@echo "  make migrate          - Create new migration (usage: make migrate msg='description')"
	@echo "  make upgrade          - Run migrations"
	@echo "  make downgrade        - Rollback last migration"
	@echo "  make db               - Start only database container"
	@echo "  make docker-up        - Start Docker containers"
	@echo "  make docker-down      - Stop Docker containers"
	@echo "  make docker-logs      - View Docker logs"

install:
	uv sync

dev:
	@echo "📦 Installing dev dependencies..."
	uv sync --extra dev
	@echo "🔧 Setting up pre-commit hooks..."
	pre-commit install
	@echo "✅ Development environment ready!"

run:
	uv run python -m app

test:
	uv run pytest -v

test-cov:
	uv run pytest -v --cov=app --cov-report=html --cov-report=term

lint:
	@echo "🔍 Running Ruff..."
	uv run ruff check .
	@echo "🔍 Running Mypy..."
	uv run mypy .

lint-fix:
	@echo "🔧 Running Ruff with auto-fix..."
	uv run ruff check --fix .
	@echo "🔧 Running Ruff with unsafe fixes..."
	uv run ruff check --fix --unsafe-fixes .
	@echo "🔍 Running Mypy..."
	uv run mypy .

format:
	@echo "✨ Formatting with Ruff..."
	uv run ruff format .
	@echo "✨ Formatting with Black..."
	uv run black .
	@echo "🔧 Fixing imports..."
	uv run ruff check --select I --fix .

format-all:
	@echo "✨ Formatting all files..."
	uv run ruff format .
	uv run black .
	uv run ruff check --fix --unsafe-fixes .
	@echo "✅ All files formatted!"

pre-commit:
	pre-commit run

pre-commit-all:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage

migrate:
	uv run alembic revision --autogenerate -m "$(msg)"

upgrade:
	uv run alembic upgrade head

downgrade:
	uv run alembic downgrade -1

db:
	docker-compose up -d db

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api
