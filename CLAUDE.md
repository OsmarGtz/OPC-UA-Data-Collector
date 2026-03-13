# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
# Start all services (API + PostgreSQL)
docker compose up --build

# Start only the test database
docker compose up db_test -d

# Run all tests (requires db_test to be running)
pytest

# Run a single test file
pytest tests/test_equipment.py

# Run a single test by name
pytest tests/test_equipment.py::test_create_equipment

# Generate and apply migrations (run inside api container or with local venv pointed at db)
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run API locally (outside Docker, requires DATABASE_URL set)
uvicorn app.main:app --reload
```

## Architecture

The app is a fully async REST API using FastAPI + SQLAlchemy 2.0 async + PostgreSQL.

**Request flow:** Router → CRUD → DB (each layer is separate; routers handle HTTP concerns, CRUD handles queries)

**Dependency injection:** `get_db()` in `database.py` yields an `AsyncSession` per request. Tests override this via `app.dependency_overrides[get_db]` in `conftest.py`.

**Domain model:**
- `Equipment` — a physical machine or asset
- `Tag` — an OPC-UA data point on a piece of equipment; has a `node_id` (e.g. `ns=2;i=1001`) that maps to the OPC-UA node
- `Reading` — a timestamped value captured from a Tag; stores both `value` (Float) and `raw_value` (String) to handle non-numeric OPC-UA data types; has a `quality` field (Good/Bad/Uncertain) matching OPC-UA semantics

Cascade deletes: Equipment → Tag → Reading.

**Two databases:**
- Production DB on port 5432 (`opc_db`), configured via `.env`
- Test DB on port 5433 (`opc_test_db`), configured via `.env.test`, uses tmpfs for speed

**Alembic quirk:** `alembic.ini` uses `psycopg2` (sync) for the CLI; `alembic/env.py` uses `asyncpg` at runtime. Don't change this split.

## Testing

Tests use `pytest-asyncio` with `asyncio_mode = auto` (set in `pytest.ini`).

`conftest.py` fixtures:
- `setup_db` — session-scoped, creates/drops all tables once per test session
- `clean_tables` — deletes all rows after each test (autouse)
- `client` — `httpx.AsyncClient` with ASGI transport; overrides `get_db` with test session

The `DATABASE_URL` env var must point to the test DB before the app is imported. `conftest.py` sets this from `.env.test` before any app imports.

## Planned Next Phases

- Phase 2: OPC-UA client using `asyncua` library to poll/subscribe to tags
- Phase 3: Dashboard/UI
- Phase 4: Alerting and streaming
