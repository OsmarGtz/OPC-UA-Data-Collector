import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_equipment(engineer_client: AsyncClient):
    payload = {"name": "Pump-01", "description": "Main pump", "location": "Plant A"}
    r = await engineer_client.post("/api/v1/equipment/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Pump-01"
    assert data["location"] == "Plant A"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_equipment_duplicate(engineer_client: AsyncClient):
    payload = {"name": "Pump-01"}
    await engineer_client.post("/api/v1/equipment/", json=payload)
    r = await engineer_client.post("/api/v1/equipment/", json=payload)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_list_equipment(engineer_client: AsyncClient):
    await engineer_client.post("/api/v1/equipment/", json={"name": "Pump-01"})
    await engineer_client.post("/api/v1/equipment/", json={"name": "Pump-02"})
    r = await engineer_client.get("/api/v1/equipment/")
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_get_equipment(engineer_client: AsyncClient):
    create_r = await engineer_client.post("/api/v1/equipment/", json={"name": "Pump-01"})
    eq_id = create_r.json()["id"]
    r = await engineer_client.get(f"/api/v1/equipment/{eq_id}")
    assert r.status_code == 200
    assert r.json()["id"] == eq_id


@pytest.mark.asyncio
async def test_get_equipment_not_found(engineer_client: AsyncClient):
    r = await engineer_client.get("/api/v1/equipment/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_equipment(engineer_client: AsyncClient):
    create_r = await engineer_client.post("/api/v1/equipment/", json={"name": "Pump-01"})
    eq_id = create_r.json()["id"]
    r = await engineer_client.patch(f"/api/v1/equipment/{eq_id}", json={"location": "Plant B"})
    assert r.status_code == 200
    assert r.json()["location"] == "Plant B"


@pytest.mark.asyncio
async def test_delete_equipment(engineer_client: AsyncClient):
    create_r = await engineer_client.post("/api/v1/equipment/", json={"name": "Pump-01"})
    eq_id = create_r.json()["id"]
    r = await engineer_client.delete(f"/api/v1/equipment/{eq_id}")
    assert r.status_code == 204
    r = await engineer_client.get(f"/api/v1/equipment/{eq_id}")
    assert r.status_code == 404
