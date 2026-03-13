from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AlertRuleCreate(BaseModel):
    name: str
    tag_id: int
    operator: Literal["gt", "lt", "gte", "lte"]
    threshold: float
    duration_seconds: float = 0.0
    severity: Literal["info", "warning", "critical"] = "warning"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "High discharge pressure",
                "tag_id": 1,
                "operator": "gt",
                "threshold": 8.5,
                "duration_seconds": 30,
                "severity": "critical",
            }
        }
    )


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 3,
                "name": "High discharge pressure",
                "tag_id": 1,
                "operator": "gt",
                "threshold": 8.5,
                "duration_seconds": 30,
                "severity": "critical",
                "is_active": True,
                "created_by": 1,
                "created_at": "2024-05-20T08:00:00Z",
            }
        },
    )

    id: int
    name: str
    tag_id: int
    operator: str
    threshold: float
    duration_seconds: float
    severity: str
    is_active: bool
    created_by: int | None
    created_at: datetime


class AlertResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 17,
                "rule_id": 3,
                "triggering_value": 9.12,
                "fired_at": "2024-05-20T14:35:22Z",
                "resolved_at": None,
                "acknowledged_at": None,
                "acknowledged_by": None,
                "tag_name": "Discharge Pressure",
                "tag_unit": "bar",
                "equipment_id": 1,
                "equipment_name": "Compressor A1",
                "equipment_location": "Building 3, Floor 2, Bay 4",
            }
        },
    )

    id: int
    rule_id: int
    triggering_value: float
    fired_at: datetime
    resolved_at: datetime | None
    acknowledged_at: datetime | None
    acknowledged_by: int | None
    # Joined context — populated by list_alerts
    tag_name: str | None = None
    tag_unit: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    equipment_location: str | None = None
