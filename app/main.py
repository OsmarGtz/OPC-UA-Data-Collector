import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.alerts.router import router as alerts_router
from app.auth.router import router as auth_router
from app.auth.security import hash_password
from app.database import AsyncSessionLocal
from app.models.user import User
from app.routers import equipment, readings, tags

# ── Tag descriptions shown in /docs ─────────────────────────────────────────
OPENAPI_TAGS = [
    {
        "name": "Authentication",
        "description": (
            "JWT-based authentication. **Login** returns an access token (30 min) "
            "and a refresh token (7 days). Pass the access token as "
            "`Authorization: Bearer <token>` on all protected endpoints."
        ),
    },
    {
        "name": "Users",
        "description": (
            "User account management. **Admin** role required for listing, creating, "
            "updating, and deleting accounts. Any authenticated user can change their own password."
        ),
    },
    {
        "name": "Equipment",
        "description": (
            "Physical machines or assets being monitored. Each piece of equipment "
            "has one or more OPC-UA **Tags** whose values are polled continuously."
        ),
    },
    {
        "name": "Tags",
        "description": (
            "OPC-UA data points mapped to an equipment unit. Each tag holds a `node_id` "
            "(e.g. `ns=2;i=1001`) that the collector uses to subscribe to the OPC-UA server."
        ),
    },
    {
        "name": "Readings",
        "description": (
            "Time-series values captured from OPC-UA tags. Each reading stores the "
            "numeric `value`, the original `raw_value` string, a `quality` field "
            "(`Good` / `Bad` / `Uncertain`), and a UTC timestamp."
        ),
    },
    {
        "name": "Alert Rules",
        "description": (
            "Threshold conditions evaluated against incoming readings. When a tag's "
            "value breaches a rule (e.g. pressure > 8.5 bar for 30 s), an **Alert** is fired. "
            "**Engineer** or **Admin** role required to create or delete rules."
        ),
    },
    {
        "name": "Alerts",
        "description": (
            "Fired alert events. An alert is **open** until the condition clears "
            "(auto-resolved) or an engineer acknowledges it. The list endpoint "
            "returns enriched data including equipment name, location, and tag."
        ),
    },
    {
        "name": "Health",
        "description": "Service liveness probe. Returns `{status: ok}` when the API is up.",
    },
]


# ── Default admin seed ───────────────────────────────────────────────────────
async def _seed_admin() -> None:
    """Ensure the default admin account exists with role='admin'.
    Creates it if missing; corrects the role if it was previously set wrong."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        if existing is None:
            db.add(
                User(
                    username="admin",
                    email="admin@localhost",
                    hashed_password=hash_password("password"),
                    role="admin",
                )
            )
            await db.commit()
        elif existing.role != "admin":
            existing.role = "admin"
            await db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await _seed_admin()
    yield


# ── Application ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="OPC-UA Data Collector",
    summary="Industrial IoT data collection, threshold alerting, and monitoring API.",
    description="""
## Overview

A fully async REST API that bridges **OPC-UA industrial servers** and a React monitoring
dashboard. Built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

### Capabilities

- **OPC-UA integration** — polls or subscribes to real OPC-UA nodes via `asyncua`
- **JWT authentication** — access + refresh tokens, three roles: `operator`, `engineer`, `admin`
- **Threshold alerting** — stateful rule evaluator with configurable duration and severity
- **React dashboard** — served from `/` in production (built into the Docker image)
- **CI/CD** — GitHub Actions pipeline: ruff lint, mypy type-check, pytest + coverage

### Authentication

All endpoints (except `/auth/login` and `/auth/refresh`) require a Bearer token:

```
Authorization: Bearer <access_token>
```

Use `POST /auth/login` to obtain tokens. The default admin account is:
- **Username:** `admin`  **Password:** `password`  *(change this in production)*

### Role hierarchy

| Role | Permissions |
|------|------------|
| `operator` | Read all data, change own password |
| `engineer` | Operator + create/delete alert rules, acknowledge alerts |
| `admin` | Engineer + full user management, set any user's password |
""",
    version="1.0.0",
    contact={
        "name": "OPC-UA Data Collector",
        "url": "https://github.com/NitzW/OPC-UA-Data-Collector",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(equipment.router, prefix="/api/v1")
app.include_router(tags.router, prefix="/api/v1")
app.include_router(readings.router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")


@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health() -> dict[str, str]:
    """Returns `{"status": "ok"}` when the API process is running."""
    return {"status": "ok"}


# Serve the built React app in production (when frontend/dist exists).
# Must be mounted last so /api/* routes take precedence.
if os.path.isdir("frontend/dist"):
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
