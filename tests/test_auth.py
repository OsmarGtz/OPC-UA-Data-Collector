"""
Tests for JWT authentication endpoints and route-level authorization.
"""

import pytest
from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ENGINEER = {
    "username": "eng_user",
    "email": "eng@example.com",
    "password": "password123",
    "role": "engineer",
}

_OPERATOR = {
    "username": "op_user",
    "email": "op@example.com",
    "password": "password123",
    "role": "operator",
}


async def _register(client: AsyncClient, payload: dict) -> dict:
    r = await client.post("/auth/register", json=payload)
    return r


async def _login(client: AsyncClient, username: str, password: str) -> dict:
    r = await client.post("/auth/login", json={"username": username, "password": password})
    return r


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient):
    r = await _register(client, _ENGINEER)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == _ENGINEER["username"]
    assert data["role"] == "engineer"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    await _register(client, _ENGINEER)
    r = await _register(client, {**_ENGINEER, "email": "other@example.com"})
    assert r.status_code == 409
    assert "Username" in r.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await _register(client, _ENGINEER)
    r = await _register(client, {**_ENGINEER, "username": "other_user"})
    assert r.status_code == 409
    assert "Email" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_returns_token_pair(client: AsyncClient):
    await _register(client, _ENGINEER)
    r = await _login(client, _ENGINEER["username"], _ENGINEER["password"])
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await _register(client, _ENGINEER)
    r = await _login(client, _ENGINEER["username"], "wrongpassword")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    r = await _login(client, "nobody", "password")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoint access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client: AsyncClient):
    r = await client.get("/api/v1/equipment/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_operator_can_read(client: AsyncClient):
    await _register(client, _OPERATOR)
    r = await _login(client, _OPERATOR["username"], _OPERATOR["password"])
    token = r.json()["access_token"]
    r = await client.get(
        "/api/v1/equipment/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_operator_cannot_write(client: AsyncClient):
    await _register(client, _OPERATOR)
    r = await _login(client, _OPERATOR["username"], _OPERATOR["password"])
    token = r.json()["access_token"]
    r = await client.post(
        "/api/v1/equipment/",
        json={"name": "Pump-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_engineer_can_write(client: AsyncClient):
    await _register(client, _ENGINEER)
    r = await _login(client, _ENGINEER["username"], _ENGINEER["password"])
    token = r.json()["access_token"]
    r = await client.post(
        "/api/v1/equipment/",
        json={"name": "Pump-01"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token(client: AsyncClient):
    await _register(client, _ENGINEER)
    login_r = await _login(client, _ENGINEER["username"], _ENGINEER["password"])
    refresh_token = login_r.json()["refresh_token"]

    r = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["access_token"] != login_r.json()["access_token"]


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    await _register(client, _ENGINEER)
    login_r = await _login(client, _ENGINEER["username"], _ENGINEER["password"])
    # Deliberately pass the access token where refresh is expected
    access_token = login_r.json()["access_token"]
    r = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401
