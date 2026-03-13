from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts.models import Alert, AlertRule
from app.alerts.schemas import AlertResponse, AlertRuleCreate, AlertRuleResponse
from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.equipment import Equipment
from app.models.tag import Tag
from app.models.user import User

router = APIRouter(tags=["Alerts"])


# ---------------------------------------------------------------------------
# Alert Rules
# ---------------------------------------------------------------------------


@router.get("/alert-rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AlertRule]:
    result = await db.execute(select(AlertRule).order_by(AlertRule.id))
    return list(result.scalars().all())


@router.post(
    "/alert-rules",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert_rule(
    data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("engineer", "admin")),
) -> AlertRule:
    rule = AlertRule(
        name=data.name,
        tag_id=data.tag_id,
        operator=data.operator,
        threshold=data.threshold,
        duration_seconds=data.duration_seconds,
        severity=data.severity,
        created_by=current_user.id,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/alert-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer", "admin")),
) -> None:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found.")
    await db.delete(rule)
    await db.commit()


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    severity: str | None = Query(default=None),
    equipment_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AlertResponse]:
    stmt = (
        select(Alert, AlertRule, Tag, Equipment)
        .join(AlertRule, Alert.rule_id == AlertRule.id)
        .join(Tag, AlertRule.tag_id == Tag.id)
        .join(Equipment, Tag.equipment_id == Equipment.id)
    )

    if status_filter == "open":
        stmt = stmt.where(Alert.resolved_at.is_(None))
    elif status_filter == "resolved":
        stmt = stmt.where(Alert.resolved_at.is_not(None))

    if severity:
        stmt = stmt.where(AlertRule.severity == severity)

    if equipment_id is not None:
        stmt = stmt.where(Tag.equipment_id == equipment_id)

    stmt = stmt.order_by(Alert.fired_at.desc())
    rows = (await db.execute(stmt)).all()

    return [
        AlertResponse(
            id=alert.id,
            rule_id=alert.rule_id,
            triggering_value=alert.triggering_value,
            fired_at=alert.fired_at,
            resolved_at=alert.resolved_at,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            tag_name=tag.name,
            tag_unit=tag.unit,
            equipment_id=equipment.id,
            equipment_name=equipment.name,
            equipment_location=equipment.location,
        )
        for alert, _rule, tag, equipment in rows
    ]


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("engineer", "admin")),
) -> Alert:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    if alert.acknowledged_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Alert already acknowledged."
        )
    alert.acknowledged_at = datetime.now(UTC)
    alert.acknowledged_by = current_user.id
    await db.commit()
    await db.refresh(alert)
    return alert
