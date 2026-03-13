import pytest
from httpx import AsyncClient


async def _create_equipment(client: AsyncClient, name: str = "Pump-01") -> dict:
    r = await client.post("/api/v1/equipment/", json={"name": name})
    return r.json()


@pytest.mark.asyncio
async def test_create_tag(engineer_client: AsyncClient):
    eq = await _create_equipment(engineer_client)
    payload = {
        "name": "Temperature",
        "node_id": "ns=2;i=1001",
        "unit": "°C",
        "data_type": "Float",
        "equipment_id": eq["id"],
    }
    r = await engineer_client.post("/api/v1/tags/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Temperature"
    assert data["node_id"] == "ns=2;i=1001"


@pytest.mark.asyncio
async def test_create_tag_invalid_equipment(engineer_client: AsyncClient):
    payload = {
        "name": "Temperature",
        "node_id": "ns=2;i=1001",
        "equipment_id": 9999,
    }
    r = await engineer_client.post("/api/v1/tags/", json=payload)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_tags(engineer_client: AsyncClient):
    eq = await _create_equipment(engineer_client)
    for i in range(3):
        await engineer_client.post(
            "/api/v1/tags/",
            json={"name": f"Tag-{i}", "node_id": f"ns=2;i={i}", "equipment_id": eq["id"]},
        )
    r = await engineer_client.get("/api/v1/tags/")
    assert r.status_code == 200
    assert len(r.json()) == 3


@pytest.mark.asyncio
async def test_list_tags_by_equipment(engineer_client: AsyncClient):
    eq1 = await _create_equipment(engineer_client, "Pump-01")
    eq2 = await _create_equipment(engineer_client, "Pump-02")
    await engineer_client.post(
        "/api/v1/tags/",
        json={"name": "Tag-A", "node_id": "ns=2;i=1", "equipment_id": eq1["id"]},
    )
    await engineer_client.post(
        "/api/v1/tags/",
        json={"name": "Tag-B", "node_id": "ns=2;i=2", "equipment_id": eq2["id"]},
    )
    r = await engineer_client.get(f"/api/v1/tags/?equipment_id={eq1['id']}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Tag-A"


@pytest.mark.asyncio
async def test_get_tag(engineer_client: AsyncClient):
    eq = await _create_equipment(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/tags/",
        json={"name": "Pressure", "node_id": "ns=2;i=2000", "equipment_id": eq["id"]},
    )
    tag_id = create_r.json()["id"]
    r = await engineer_client.get(f"/api/v1/tags/{tag_id}")
    assert r.status_code == 200
    assert r.json()["id"] == tag_id


@pytest.mark.asyncio
async def test_update_tag(engineer_client: AsyncClient):
    eq = await _create_equipment(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/tags/",
        json={"name": "Pressure", "node_id": "ns=2;i=2000", "equipment_id": eq["id"]},
    )
    tag_id = create_r.json()["id"]
    r = await engineer_client.patch(f"/api/v1/tags/{tag_id}", json={"unit": "bar"})
    assert r.status_code == 200
    assert r.json()["unit"] == "bar"


@pytest.mark.asyncio
async def test_delete_tag(engineer_client: AsyncClient):
    eq = await _create_equipment(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/tags/",
        json={"name": "Pressure", "node_id": "ns=2;i=2000", "equipment_id": eq["id"]},
    )
    tag_id = create_r.json()["id"]
    r = await engineer_client.delete(f"/api/v1/tags/{tag_id}")
    assert r.status_code == 204
    r = await engineer_client.get(f"/api/v1/tags/{tag_id}")
    assert r.status_code == 404
