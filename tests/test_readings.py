import pytest
from httpx import AsyncClient


async def _setup(client: AsyncClient) -> int:
    eq = (await client.post("/api/v1/equipment/", json={"name": "Pump-01"})).json()
    tag = (
        await client.post(
            "/api/v1/tags/",
            json={"name": "Temperature", "node_id": "ns=2;i=1001", "equipment_id": eq["id"]},
        )
    ).json()
    return tag["id"]


@pytest.mark.asyncio
async def test_create_reading(engineer_client: AsyncClient):
    tag_id = await _setup(engineer_client)
    payload = {"tag_id": tag_id, "value": 72.5, "quality": "Good"}
    r = await engineer_client.post("/api/v1/readings/", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["value"] == 72.5
    assert data["quality"] == "Good"


@pytest.mark.asyncio
async def test_create_reading_invalid_tag(engineer_client: AsyncClient):
    r = await engineer_client.post("/api/v1/readings/", json={"tag_id": 9999, "value": 1.0})
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_readings(engineer_client: AsyncClient):
    tag_id = await _setup(engineer_client)
    for v in [10.0, 20.0, 30.0]:
        await engineer_client.post("/api/v1/readings/", json={"tag_id": tag_id, "value": v})
    r = await engineer_client.get(f"/api/v1/readings/?tag_id={tag_id}")
    assert r.status_code == 200
    assert len(r.json()) == 3


@pytest.mark.asyncio
async def test_get_reading(engineer_client: AsyncClient):
    tag_id = await _setup(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/readings/", json={"tag_id": tag_id, "value": 55.0}
    )
    reading_id = create_r.json()["id"]
    r = await engineer_client.get(f"/api/v1/readings/{reading_id}")
    assert r.status_code == 200
    assert r.json()["id"] == reading_id


@pytest.mark.asyncio
async def test_update_reading(engineer_client: AsyncClient):
    tag_id = await _setup(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/readings/", json={"tag_id": tag_id, "value": 55.0}
    )
    reading_id = create_r.json()["id"]
    r = await engineer_client.patch(f"/api/v1/readings/{reading_id}", json={"quality": "Bad"})
    assert r.status_code == 200
    assert r.json()["quality"] == "Bad"


@pytest.mark.asyncio
async def test_delete_reading(engineer_client: AsyncClient):
    tag_id = await _setup(engineer_client)
    create_r = await engineer_client.post(
        "/api/v1/readings/", json={"tag_id": tag_id, "value": 55.0}
    )
    reading_id = create_r.json()["id"]
    r = await engineer_client.delete(f"/api/v1/readings/{reading_id}")
    assert r.status_code == 204
    r = await engineer_client.get(f"/api/v1/readings/{reading_id}")
    assert r.status_code == 404
