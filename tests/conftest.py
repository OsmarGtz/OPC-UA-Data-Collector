import asyncio
import os
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Point to test DB before importing app config.
# TEST_DATABASE_URL is set by docker-compose when running inside the container.
# Falls back to localhost:5433 when running tests directly on the host machine.
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://opc_user:opc_password@localhost:5433/opc_test_db",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


engine_test = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine_test.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield
    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


async def _make_auth_client(role: str) -> AsyncClient:
    """Helper: register a user and return a client with Authorization header set."""
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    ac = AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://test",
    )
    await ac.__aenter__()

    username = f"test_{role}"
    payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "testpass123",
        "role": role,
    }
    await ac.post("/auth/register", json=payload)
    resp = await ac.post("/auth/login", json={"username": username, "password": "testpass123"})
    token = resp.json()["access_token"]
    ac.headers.update({"Authorization": f"Bearer {token}"})
    return ac


@pytest_asyncio.fixture
async def engineer_client():
    ac = await _make_auth_client("engineer")
    yield ac
    await ac.__aexit__(None, None, None)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def operator_client():
    ac = await _make_auth_client("operator")
    yield ac
    await ac.__aexit__(None, None, None)
    app.dependency_overrides.clear()
