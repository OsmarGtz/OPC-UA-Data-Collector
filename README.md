# OPC-UA Data Collector

A production-grade industrial IoT platform that polls OPC-UA servers, stores time-series readings in PostgreSQL, evaluates configurable threshold rules, and presents a live monitoring dashboard — all containerised with Docker.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Docker Compose                                                  │
│                                                                  │
│  ┌──────────────┐     OPC-UA      ┌────────────────────────┐   │
│  │  Simulator   │◄───────────────►│  Collector (asyncua)   │   │
│  │  (asyncua)   │  tcp://4840     │  polls every 5 s       │   │
│  └──────────────┘                 └───────────┬────────────┘   │
│                                               │ SQLAlchemy      │
│  ┌──────────────┐     REST API   ┌────────────▼────────────┐   │
│  │  React SPA   │◄──────────────►│  FastAPI + Alembic      │   │
│  │  (Vite/TS)   │  /api/v1       │  JWT auth · RBAC        │   │
│  └──────────────┘                └───────────┬────────────┘   │
│                                               │ asyncpg         │
│                                        ┌──────▼──────┐         │
│                                        │ PostgreSQL  │         │
│                                        │    16       │         │
│                                        └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone https://github.com/NitzW/OPC-UA-Data-Collector.git
cd OPC-UA-Data-Collector

cp .env.example .env          # review and adjust secrets

docker compose up --build     # starts API, DB, simulator, collector, frontend
```

| Service | URL |
|---------|-----|
| React Dashboard | http://localhost:5173 |
| API (Swagger UI) | http://localhost:8000/docs |
| API (ReDoc) | http://localhost:8000/redoc |
| OPC-UA Simulator | opc.tcp://localhost:4840 |

**Default credentials:** `admin` / `password` *(change in production)*

---

## Features

| Area | What's built |
|------|-------------|
| **OPC-UA** | Async polling via `asyncua`; stores value, raw string, and quality flag (Good/Bad/Uncertain) |
| **Auth** | JWT access + refresh tokens; three roles: `operator`, `engineer`, `admin` |
| **Alerting** | Stateful rule evaluator — threshold + optional duration; auto-resolves when condition clears |
| **Dashboard** | React 18 + Vite + TanStack Query; live trend charts (Recharts), alert management |
| **User Management** | Admin-only CRUD; engineers change own password; operators read-only |
| **CI/CD** | GitHub Actions: ruff lint, mypy type-check, pytest with real Postgres, Docker build |

---

## API Examples

### 1 — Authenticate

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### 2 — Query time-series readings with a time window

```bash
TOKEN="eyJhbGci..."

curl "http://localhost:8000/api/v1/equipment/1/readings?start=2024-05-20T00:00:00Z&end=2024-05-20T23:59:59Z&limit=500" \
  -H "Authorization: Bearer $TOKEN"
```

### 3 — Create an alert rule

```bash
curl -X POST http://localhost:8000/api/v1/alert-rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High discharge pressure",
    "tag_id": 1,
    "operator": "gt",
    "threshold": 8.5,
    "duration_seconds": 30,
    "severity": "critical"
  }'
```

### 4 — List open alerts with equipment context

```bash
curl "http://localhost:8000/api/v1/alerts?status=open" \
  -H "Authorization: Bearer $TOKEN"
```

Response includes `equipment_name`, `equipment_location`, and `tag_name` — no extra round trips.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API framework | **FastAPI** | Async-native, auto OpenAPI, best-in-class DX |
| ORM | **SQLAlchemy 2.0 async** | Type-safe queries, full async support, no ORM magic |
| Migrations | **Alembic** | Schema history tracked in version control |
| Database | **PostgreSQL 16** | Time-series queries, ACID, production-proven |
| OPC-UA | **asyncua** | Pure-Python async OPC-UA client/server |
| Auth | **python-jose + passlib** | JWT HS256 tokens; bcrypt password hashing |
| Linter | **ruff** | Replaces flake8 + black + isort; 100× faster |
| Type check | **mypy** | Catches async return-type bugs at dev time |
| Testing | **pytest-asyncio + httpx** | Async tests against a real Postgres instance |
| Frontend | **React 18 + Vite + TypeScript** | Fast HMR, strict types, no CRA bloat |
| State | **TanStack Query v5** | Server-state cache, 10 s auto-refresh |
| Charts | **Recharts** | Composable, SVG-based, threshold reference lines |
| Containers | **Docker Compose** | One-command local setup; multi-stage prod image |
| CI/CD | **GitHub Actions** | Lint → type-check → test → docker-build on every push |

---

## Project Structure

```
.
├── app/
│   ├── alerts/          # Alert rule evaluation engine + REST endpoints
│   ├── auth/            # JWT auth, RBAC dependencies, user management
│   ├── crud/            # Async database access layer
│   ├── models/          # SQLAlchemy ORM models
│   ├── routers/         # Equipment, Tags, Readings REST endpoints
│   ├── schemas/         # Pydantic v2 request/response schemas
│   ├── config.py        # pydantic-settings (reads .env)
│   ├── database.py      # Async engine + session factory
│   └── main.py          # FastAPI app, middleware, lifespan
├── alembic/             # Database migrations
├── collector/           # OPC-UA polling loop → writes Readings
├── simulator/           # OPC-UA test server (generates synthetic data)
├── frontend/            # React SPA (Vite + TypeScript)
├── tests/               # pytest-asyncio integration tests
├── .github/workflows/   # CI pipeline (lint, typecheck, test, docker)
├── docker-compose.yml
├── Dockerfile           # Multi-stage: Node build → Python serve
├── Makefile             # Developer shortcuts (make up / test / lint)
└── pyproject.toml       # ruff + mypy + coverage config
```

---

## Development

```bash
make up          # docker compose up --build
make test        # pytest against db_test container
make lint        # ruff check .
make format      # ruff format .
make typecheck   # mypy app/
make migrate     # alembic upgrade head
make help        # list all targets
```

---

## Roles

| Role | Create alert rules | Acknowledge alerts | Manage users | Change any password |
|------|:-----------------:|:-----------------:|:------------:|:------------------:|
| `operator` | | | | |
| `engineer` | ✓ | ✓ | | |
| `admin` | ✓ | ✓ | ✓ | ✓ |

---

## License

MIT
