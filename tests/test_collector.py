"""
Integration tests for the collector service components.

These tests use an in-process asyncua OPC-UA server (real TCP on localhost,
port 48400) so no mocking of the OPC-UA layer is needed.  The test database
is the same db_test Postgres container used by the Phase 1 API tests.

Test layers:
  - TestOpcUaClient  : connection, reading good nodes, handling bad node IDs
  - TestDatabaseWriter : bulk_insert row count, empty-list short-circuit
  - TestCollectorIntegration : end-to-end — 3 poll cycles land the right rows
"""

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from asyncua import Server, ua
from sqlalchemy import select

from app.models.equipment import Equipment
from app.models.reading import Reading
from app.models.tag import Tag
from collector.opcua_client import OpcUaClient
from collector.writer import DatabaseWriter
from tests.conftest import TestingSessionLocal

# ---------------------------------------------------------------------------
# Constants shared between the server fixture and the DB fixture.
# Namespace index 2 is guaranteed: asyncua reserves 0 (OPC-UA standard) and
# 1 (server namespace), so the first register_namespace call always returns 2.
# ---------------------------------------------------------------------------
_OPC_BIND_URL   = "opc.tcp://0.0.0.0:48400"
_OPC_CLIENT_URL = "opc.tcp://127.0.0.1:48400"
_NS_URI         = "http://test-collector-ns"
_NS_IDX         = 2          # matches asyncua's guaranteed return value

_NODE_TEMP_ID  = 9001
_NODE_PRESS_ID = 9002

NODE_TEMP  = f"ns={_NS_IDX};i={_NODE_TEMP_ID}"
NODE_PRESS = f"ns={_NS_IDX};i={_NODE_PRESS_ID}"

TEMP_VALUE  = 71.5
PRESS_VALUE = 4.5


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def opc_test_server():
    """
    Spin up a minimal in-process OPC-UA server with two Float variable nodes.

    The server listens on localhost:48400 for the duration of the test and is
    stopped automatically when the fixture tears down.  Values are static
    (the simulator's SignalGenerator is not involved here — we want predictable
    numbers we can assert against).
    """
    server = Server()
    await server.init()
    server.set_endpoint(_OPC_BIND_URL)
    idx = await server.register_namespace(_NS_URI)

    assert idx == _NS_IDX, (
        f"Unexpected namespace index {idx}. Update _NS_IDX in test_collector.py."
    )

    objects = server.nodes.objects
    pump = await objects.add_object(idx, "TestPump")

    temp_node = await pump.add_variable(
        ua.NodeId(_NODE_TEMP_ID, idx), "temperature",
        TEMP_VALUE, varianttype=ua.VariantType.Float,
    )
    press_node = await pump.add_variable(
        ua.NodeId(_NODE_PRESS_ID, idx), "pressure",
        PRESS_VALUE, varianttype=ua.VariantType.Float,
    )
    await temp_node.set_writable(True)
    await press_node.set_writable(True)

    async with server:
        yield   # server is live while the test runs


@pytest_asyncio.fixture
async def test_tags():
    """
    Create one Equipment row + two Tag rows in the test DB and return the tags.
    Uses a dedicated session so the rows are committed and visible to other
    sessions inside the same test.
    """
    async with TestingSessionLocal() as session:
        eq = Equipment(
            name="Collector-Test-Pump",
            description="Created by test_collector.py",
            location="Test Lab",
        )
        session.add(eq)
        await session.flush()  # populate eq.id before adding tags

        tag_temp = Tag(
            name="temperature",
            node_id=NODE_TEMP,
            unit="°C",
            data_type="Float",
            equipment_id=eq.id,
        )
        tag_press = Tag(
            name="pressure",
            node_id=NODE_PRESS,
            unit="bar",
            data_type="Float",
            equipment_id=eq.id,
        )
        session.add_all([tag_temp, tag_press])
        await session.commit()
        await session.refresh(tag_temp)
        await session.refresh(tag_press)

    return [tag_temp, tag_press]


# ---------------------------------------------------------------------------
# OpcUaClient tests
# ---------------------------------------------------------------------------

class TestOpcUaClient:

    async def test_connect_succeeds(self, opc_test_server):
        """Client must connect to the in-process server without error."""
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)
        await client.disconnect()

    async def test_reads_correct_values(self, opc_test_server):
        """
        Reading the two registered nodes must return the exact Float values
        written at server startup, with Good quality.
        """
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)

        try:
            results = await client.read_node_values([NODE_TEMP, NODE_PRESS])
        finally:
            await client.disconnect()

        assert len(results) == 2

        result_map = {node_id: (value, quality) for node_id, value, quality in results}

        temp_val, temp_q = result_map[NODE_TEMP]
        assert temp_q == "Good"
        assert temp_val == pytest.approx(TEMP_VALUE, abs=0.01)

        press_val, press_q = result_map[NODE_PRESS]
        assert press_q == "Good"
        assert press_val == pytest.approx(PRESS_VALUE, abs=0.01)

    async def test_unknown_node_returns_bad_quality(self, opc_test_server):
        """
        Reading a node ID that does not exist on the server must not raise.
        Instead, OpcUaClient must return (node_id, None, "Bad") so the
        collector can record the failed read without crashing.
        """
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)

        try:
            results = await client.read_node_values([f"ns={_NS_IDX};i=99999"])
        finally:
            await client.disconnect()

        assert len(results) == 1
        _, value, quality = results[0]
        assert quality == "Bad"
        assert value is None

    async def test_disconnect_is_idempotent(self, opc_test_server):
        """Calling disconnect twice must not raise."""
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)
        await client.disconnect()
        await client.disconnect()  # second call must be safe


# ---------------------------------------------------------------------------
# DatabaseWriter tests
# ---------------------------------------------------------------------------

class TestDatabaseWriter:

    async def test_bulk_insert_returns_correct_count(self, test_tags):
        """bulk_insert must return the number of rows it inserted."""
        writer = DatabaseWriter()
        now = datetime.now(timezone.utc)
        rows = [
            {"tag_id": test_tags[0].id, "value": TEMP_VALUE,  "raw_value": str(TEMP_VALUE),  "quality": "Good", "timestamp": now},
            {"tag_id": test_tags[1].id, "value": PRESS_VALUE, "raw_value": str(PRESS_VALUE), "quality": "Good", "timestamp": now},
        ]

        async with TestingSessionLocal() as session:
            count = await writer.bulk_insert(session, rows)

        assert count == 2

    async def test_bulk_insert_persists_rows(self, test_tags):
        """Rows inserted by bulk_insert must be queryable in a separate session."""
        writer = DatabaseWriter()
        now = datetime.now(timezone.utc)
        rows = [
            {"tag_id": test_tags[0].id, "value": TEMP_VALUE,  "raw_value": str(TEMP_VALUE),  "quality": "Good", "timestamp": now},
            {"tag_id": test_tags[1].id, "value": PRESS_VALUE, "raw_value": str(PRESS_VALUE), "quality": "Good", "timestamp": now},
        ]

        async with TestingSessionLocal() as session:
            await writer.bulk_insert(session, rows)

        async with TestingSessionLocal() as verify_session:
            result = await verify_session.execute(
                select(Reading).where(
                    Reading.tag_id.in_([test_tags[0].id, test_tags[1].id])
                )
            )
            readings = result.scalars().all()

        assert len(readings) == 2
        values = {r.value for r in readings}
        assert TEMP_VALUE in values
        assert PRESS_VALUE in values

    async def test_bulk_insert_empty_list_returns_zero(self):
        """An empty row list must return 0 and must not touch the database."""
        writer = DatabaseWriter()
        async with TestingSessionLocal() as session:
            count = await writer.bulk_insert(session, [])
        assert count == 0


# ---------------------------------------------------------------------------
# End-to-end integration
# ---------------------------------------------------------------------------

class TestCollectorIntegration:

    async def test_three_poll_cycles_create_correct_row_count(
        self, opc_test_server, test_tags
    ):
        """
        Simulating 3 poll cycles (OPC-UA read → DB write) must produce
        exactly 3 × len(tags) Reading rows — one per tag per cycle.
        """
        POLL_CYCLES = 3
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)

        writer = DatabaseWriter()
        tag_by_node = {t.node_id: t for t in test_tags}
        node_ids = list(tag_by_node.keys())

        try:
            for _ in range(POLL_CYCLES):
                raw = await client.read_node_values(node_ids)
                now = datetime.now(timezone.utc)
                rows = [
                    {
                        "tag_id": tag_by_node[nid].id,
                        "value": val,
                        "raw_value": str(val),
                        "quality": quality,
                        "timestamp": now,
                    }
                    for nid, val, quality in raw
                    if nid in tag_by_node
                ]
                async with TestingSessionLocal() as session:
                    await writer.bulk_insert(session, rows)
        finally:
            await client.disconnect()

        async with TestingSessionLocal() as session:
            result = await session.execute(
                select(Reading).where(
                    Reading.tag_id.in_([t.id for t in test_tags])
                )
            )
            all_readings = result.scalars().all()

        assert len(all_readings) == POLL_CYCLES * len(test_tags)

    async def test_all_readings_have_good_quality(
        self, opc_test_server, test_tags
    ):
        """
        Every reading written from the in-process server must have
        quality='Good' since all nodes exist and the server is healthy.
        """
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)

        writer = DatabaseWriter()
        tag_by_node = {t.node_id: t for t in test_tags}

        try:
            raw = await client.read_node_values(list(tag_by_node.keys()))
            now = datetime.now(timezone.utc)
            rows = [
                {
                    "tag_id": tag_by_node[nid].id,
                    "value": val,
                    "raw_value": str(val),
                    "quality": quality,
                    "timestamp": now,
                }
                for nid, val, quality in raw
                if nid in tag_by_node
            ]
            async with TestingSessionLocal() as session:
                await writer.bulk_insert(session, rows)
        finally:
            await client.disconnect()

        async with TestingSessionLocal() as session:
            result = await session.execute(
                select(Reading).where(
                    Reading.tag_id.in_([t.id for t in test_tags])
                )
            )
            readings = result.scalars().all()

        assert len(readings) > 0
        assert all(r.quality == "Good" for r in readings)

    async def test_reading_values_match_opc_ua_source(
        self, opc_test_server, test_tags
    ):
        """
        The float values stored in the DB must match what the OPC-UA
        server was initialised with (within Float precision tolerance).
        """
        client = OpcUaClient(_OPC_CLIENT_URL)
        await client.connect_with_retry(base_delay=0.1, max_delay=1.0)

        writer = DatabaseWriter()
        tag_by_node = {t.node_id: t for t in test_tags}

        try:
            raw = await client.read_node_values(list(tag_by_node.keys()))
            now = datetime.now(timezone.utc)
            rows = [
                {
                    "tag_id": tag_by_node[nid].id,
                    "value": val,
                    "raw_value": str(val),
                    "quality": quality,
                    "timestamp": now,
                }
                for nid, val, quality in raw
                if nid in tag_by_node
            ]
            async with TestingSessionLocal() as session:
                await writer.bulk_insert(session, rows)
        finally:
            await client.disconnect()

        async with TestingSessionLocal() as session:
            result = await session.execute(
                select(Reading).where(
                    Reading.tag_id == tag_by_node[NODE_TEMP].id
                )
            )
            temp_reading = result.scalar_one()

        # OPC-UA Float is 32-bit, so allow for float32 rounding
        assert temp_reading.value == pytest.approx(TEMP_VALUE, abs=0.01)
