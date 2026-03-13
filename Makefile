.PHONY: up down build restart logs lint format typecheck test migrate shell help

# ── Docker ──────────────────────────────────────────────────────────────────
up:          ## Start all services (API + DB + frontend + simulator + collector)
	docker compose up --build

down:        ## Stop and remove containers
	docker compose down

build:       ## Rebuild images without starting
	docker compose build

restart:     ## Restart a specific service, e.g.  make restart s=api
	docker compose restart $(s)

logs:        ## Tail logs for a service, e.g.  make logs s=api
	docker compose logs -f $(s)

# ── Code quality ─────────────────────────────────────────────────────────────
lint:        ## Run ruff linter
	ruff check .

format:      ## Auto-format with ruff
	ruff format .

format-check: ## Check formatting without writing (used in CI)
	ruff format --check .

typecheck:   ## Run mypy type checker on app/
	mypy app/ --ignore-missing-imports

# ── Tests ────────────────────────────────────────────────────────────────────
test:        ## Run tests (starts db_test if not running)
	docker compose up db_test -d
	pytest -v

test-cov:    ## Run tests with coverage report
	docker compose up db_test -d
	pytest --cov=app --cov-report=term-missing -v

# ── Database ─────────────────────────────────────────────────────────────────
migrate:     ## Apply Alembic migrations (run inside api container or with local venv)
	alembic upgrade head

migration:   ## Generate a new migration, e.g.  make migration m="add index"
	alembic revision --autogenerate -m "$(m)"

# ── Utilities ────────────────────────────────────────────────────────────────
shell:       ## Open a bash shell in the api container
	docker compose exec api bash

help:        ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
