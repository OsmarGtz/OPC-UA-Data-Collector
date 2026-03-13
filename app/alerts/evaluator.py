"""
Alert rule evaluator — runs inside the collector's poll cycle.

For each active rule, it checks whether the matching tag's latest value
satisfies the operator+threshold condition.  If the condition is met and
has been met for at least `duration_seconds`, an Alert row is fired.
When the condition clears, the open Alert is auto-resolved.

All DB writes for a single evaluation pass share one commit so we never
leave the alerts table in a half-written state.
"""

import time
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert, AlertRule


@dataclass
class _CachedRule:
    id: int
    name: str
    tag_id: int
    operator: str
    threshold: float
    duration_seconds: float
    severity: str


@dataclass
class _ConditionState:
    """Tracks when the condition for a rule first became true."""

    started_at: float  # time.monotonic() when the condition first fired
    alert_id: int | None = None  # DB id of the open Alert row, if already persisted


class RuleEvaluator:
    """
    Stateful evaluator.  One instance should live for the lifetime of the
    collector service so that duration tracking survives across poll cycles.
    """

    _CACHE_TTL: float = 30.0  # seconds between rule re-loads from DB

    def __init__(self) -> None:
        self._state: dict[int, _ConditionState] = {}  # rule_id -> state
        self._rules_cache: list[_CachedRule] = []
        self._cache_expires_at: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check(self, session: AsyncSession, readings: list[dict]) -> None:
        """
        Evaluate all active rules against the latest readings.

        `readings` is the list of dicts passed to DatabaseWriter.bulk_insert,
        each having keys: tag_id, value, quality, timestamp.
        """
        rules = await self._get_rules(session)
        if not rules:
            return

        # Build a tag_id -> value lookup from the current poll cycle.
        # Only include Good-quality readings so bad reads don't fire alerts.
        value_by_tag: dict[int, float] = {
            r["tag_id"]: r["value"]
            for r in readings
            if r.get("quality") == "Good" and r.get("value") is not None
        }

        now_mono = time.monotonic()
        now_dt = datetime.now(UTC)
        changed = False

        for rule in rules:
            value = value_by_tag.get(rule.tag_id)
            if value is None:
                # Tag not read this cycle — leave state untouched.
                continue

            condition_met = self._evaluate(value, rule.operator, rule.threshold)
            state = self._state.get(rule.id)

            if condition_met:
                if state is None:
                    # Condition just became true.
                    self._state[rule.id] = _ConditionState(started_at=now_mono)
                    state = self._state[rule.id]

                # Check whether the required duration has elapsed.
                elapsed = now_mono - state.started_at
                if elapsed >= rule.duration_seconds and state.alert_id is None:
                    # Fire a new alert.
                    alert = Alert(
                        rule_id=rule.id,
                        triggering_value=value,
                        fired_at=now_dt,
                    )
                    session.add(alert)
                    await session.flush()  # populate alert.id
                    state.alert_id = alert.id
                    changed = True
            else:
                if state is not None and state.alert_id is not None:
                    # Condition cleared — auto-resolve the open alert.
                    result = await session.execute(select(Alert).where(Alert.id == state.alert_id))
                    open_alert = result.scalar_one_or_none()
                    if open_alert is not None and open_alert.resolved_at is None:
                        open_alert.resolved_at = now_dt
                        changed = True

                # Clear in-memory state regardless.
                self._state.pop(rule.id, None)

        if changed:
            await session.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_rules(self, session: AsyncSession) -> list[_CachedRule]:
        if time.monotonic() < self._cache_expires_at:
            return self._rules_cache

        result = await session.execute(select(AlertRule).where(AlertRule.is_active.is_(True)))
        db_rules = result.scalars().all()
        self._rules_cache = [
            _CachedRule(
                id=r.id,
                name=r.name,
                tag_id=r.tag_id,
                operator=r.operator,
                threshold=r.threshold,
                duration_seconds=r.duration_seconds,
                severity=r.severity,
            )
            for r in db_rules
        ]
        self._cache_expires_at = time.monotonic() + self._CACHE_TTL
        return self._rules_cache

    @staticmethod
    def _evaluate(value: float, operator: str, threshold: float) -> bool:
        if operator == "gt":
            return value > threshold
        if operator == "lt":
            return value < threshold
        if operator == "gte":
            return value >= threshold
        if operator == "lte":
            return value <= threshold
        return False
