"""
Tests for the alert rule evaluator (unit) and the alerts REST API (integration).

Evaluator tests are pure in-memory — they use a real DB session but mock
time.monotonic so duration thresholds can be controlled precisely.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from app.alerts.evaluator import RuleEvaluator
from app.alerts.models import Alert, AlertRule
from tests.conftest import TestingSessionLocal

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def tag_and_rule_factory(engineer_client: AsyncClient):
    """
    Returns an async factory function that creates one equipment+tag via the API
    and one AlertRule directly in the DB, then yields (tag_id, rule_id).
    """

    async def _make(operator: str, threshold: float, duration: float = 0.0) -> tuple[int, int]:
        eq = (await engineer_client.post("/api/v1/equipment/", json={"name": "Factory-Eq"})).json()
        tag = (
            await engineer_client.post(
                "/api/v1/tags/",
                json={
                    "name": "test_tag",
                    "node_id": "ns=2;i=8000",
                    "equipment_id": eq["id"],
                },
            )
        ).json()
        tag_id = tag["id"]

        async with TestingSessionLocal() as session:
            rule = AlertRule(
                name="test_rule",
                tag_id=tag_id,
                operator=operator,
                threshold=threshold,
                duration_seconds=duration,
                severity="warning",
            )
            session.add(rule)
            await session.commit()
            await session.refresh(rule)
            rule_id = rule.id

        return tag_id, rule_id

    return _make


# ---------------------------------------------------------------------------
# Evaluator — operator correctness
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operator,threshold,value,should_fire",
    [
        ("gt", 10.0, 11.0, True),
        ("gt", 10.0, 9.0, False),
        ("lt", 10.0, 9.0, True),
        ("lt", 10.0, 11.0, False),
        ("gte", 10.0, 10.0, True),
        ("gte", 10.0, 9.9, False),
        ("lte", 10.0, 10.0, True),
        ("lte", 10.0, 10.1, False),
    ],
)
async def test_operator_correctness(tag_and_rule_factory, operator, threshold, value, should_fire):
    tag_id, rule_id = await tag_and_rule_factory(operator, threshold)
    evaluator = RuleEvaluator()
    readings = [{"tag_id": tag_id, "value": value, "quality": "Good"}]

    async with TestingSessionLocal() as session:
        await evaluator.check(session, readings)

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        alerts = result.scalars().all()

    if should_fire:
        assert len(alerts) == 1
        assert alerts[0].triggering_value == value
    else:
        assert len(alerts) == 0


# ---------------------------------------------------------------------------
# Duration tracking
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duration_zero_fires_immediately(tag_and_rule_factory):
    tag_id, rule_id = await tag_and_rule_factory("gt", 50.0, duration=0.0)
    evaluator = RuleEvaluator()

    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_duration_not_met_does_not_fire(tag_and_rule_factory):
    """Condition met, but elapsed time < duration → no alert yet."""
    tag_id, rule_id = await tag_and_rule_factory("gt", 50.0, duration=30.0)

    # _clock call pattern per check():
    #   cache-miss path: _get_rules calls _clock twice + check calls once = 3
    #   cache-hit  path: _get_rules calls _clock once  + check calls once = 2
    #
    # First check (t=0):  cache miss → clock returns 0.0, 0.0, 0.0
    #   _cache_expires_at = 0.0 + 30.0 = 30.0; state.started_at = 0.0
    # Second check (t=10): cache hit (10 < 30) → clock returns 10.0, 10.0
    #   elapsed = 10.0 - 0.0 = 10 < 30 → no alert fired
    clock = iter([0.0, 0.0, 0.0, 10.0, 10.0])
    evaluator = RuleEvaluator(_clock=lambda: next(clock))

    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        assert len(result.scalars().all()) == 0


@pytest.mark.asyncio
async def test_duration_met_fires_alert(tag_and_rule_factory):
    """Condition met and elapsed time >= duration → alert fires on second check."""
    tag_id, rule_id = await tag_and_rule_factory("gt", 50.0, duration=30.0)

    # First check (t=0):  cache miss → clock returns 0.0, 0.0, 0.0
    #   _cache_expires_at = 0.0 + 30.0 = 30.0; state.started_at = 0.0
    # Second check (t=31): 31 > 30 → cache miss → clock returns 31.0, 31.0, 31.0
    #   elapsed = 31.0 - 0.0 = 31 >= 30 → alert fires
    clock = iter([0.0, 0.0, 0.0, 31.0, 31.0, 31.0])
    evaluator = RuleEvaluator(_clock=lambda: next(clock))

    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        assert len(result.scalars().all()) == 1


# ---------------------------------------------------------------------------
# Auto-resolution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_condition_clears_auto_resolves(tag_and_rule_factory):
    """Once an alert fires, clearing the condition sets resolved_at."""
    tag_id, rule_id = await tag_and_rule_factory("gt", 50.0, duration=0.0)
    evaluator = RuleEvaluator()

    # Fire the alert
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 100.0, "quality": "Good"}])

    # Condition clears
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 10.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        alert = result.scalar_one()
        assert alert.resolved_at is not None


# ---------------------------------------------------------------------------
# Multiple rules / independence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_two_rules_same_tag_evaluated_independently(engineer_client: AsyncClient):
    """Two rules on the same tag fire/not-fire independently."""
    eq = (await engineer_client.post("/api/v1/equipment/", json={"name": "Multi-Rule-Eq"})).json()
    tag = (
        await engineer_client.post(
            "/api/v1/tags/",
            json={"name": "shared_tag", "node_id": "ns=2;i=8001", "equipment_id": eq["id"]},
        )
    ).json()
    tag_id = tag["id"]

    async with TestingSessionLocal() as session:
        rule_hi = AlertRule(
            name="high_rule",
            tag_id=tag_id,
            operator="gt",
            threshold=80.0,
            duration_seconds=0.0,
            severity="critical",
        )
        rule_lo = AlertRule(
            name="low_rule",
            tag_id=tag_id,
            operator="lt",
            threshold=20.0,
            duration_seconds=0.0,
            severity="info",
        )
        session.add_all([rule_hi, rule_lo])
        await session.commit()
        await session.refresh(rule_hi)
        await session.refresh(rule_lo)
        rule_hi_id, rule_lo_id = rule_hi.id, rule_lo.id

    evaluator = RuleEvaluator()
    # Value = 90 → triggers "gt 80", does NOT trigger "lt 20"
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 90.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        hi_alerts = (
            (await session.execute(select(Alert).where(Alert.rule_id == rule_hi_id)))
            .scalars()
            .all()
        )
        lo_alerts = (
            (await session.execute(select(Alert).where(Alert.rule_id == rule_lo_id)))
            .scalars()
            .all()
        )

    assert len(hi_alerts) == 1
    assert len(lo_alerts) == 0


# ---------------------------------------------------------------------------
# Alerts REST API
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_alert_rule_via_api(engineer_client: AsyncClient):
    eq = (await engineer_client.post("/api/v1/equipment/", json={"name": "API-Eq"})).json()
    tag = (
        await engineer_client.post(
            "/api/v1/tags/",
            json={"name": "api_tag", "node_id": "ns=2;i=9000", "equipment_id": eq["id"]},
        )
    ).json()

    r = await engineer_client.post(
        "/api/v1/alert-rules",
        json={
            "name": "High Temperature",
            "tag_id": tag["id"],
            "operator": "gt",
            "threshold": 90.0,
            "severity": "critical",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "High Temperature"
    assert data["operator"] == "gt"
    assert data["threshold"] == 90.0


@pytest.mark.asyncio
async def test_operator_cannot_create_alert_rule(operator_client: AsyncClient):
    r = await operator_client.post(
        "/api/v1/alert-rules",
        json={
            "name": "High Temp",
            "tag_id": 1,
            "operator": "gt",
            "threshold": 90.0,
        },
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_list_alerts_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/alerts")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_acknowledge_alert(engineer_client: AsyncClient):
    eq = (await engineer_client.post("/api/v1/equipment/", json={"name": "Ack-Eq"})).json()
    tag = (
        await engineer_client.post(
            "/api/v1/tags/",
            json={"name": "ack_tag", "node_id": "ns=2;i=9100", "equipment_id": eq["id"]},
        )
    ).json()
    tag_id = tag["id"]

    # Create rule and fire alert via evaluator
    async with TestingSessionLocal() as session:
        rule = AlertRule(
            name="ack_rule",
            tag_id=tag_id,
            operator="gt",
            threshold=0.0,
            duration_seconds=0.0,
            severity="warning",
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        rule_id = rule.id

    evaluator = RuleEvaluator()
    async with TestingSessionLocal() as session:
        await evaluator.check(session, [{"tag_id": tag_id, "value": 1.0, "quality": "Good"}])

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.rule_id == rule_id))
        alert_id = result.scalar_one().id

    r = await engineer_client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert r.status_code == 200
    data = r.json()
    assert data["acknowledged_at"] is not None
    assert data["acknowledged_by"] is not None
