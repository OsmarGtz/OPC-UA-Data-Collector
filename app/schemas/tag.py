from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TagBase(BaseModel):
    name: str
    description: str | None = None
    node_id: str
    unit: str | None = None
    data_type: str = "Float"
    equipment_id: int


class TagCreate(TagBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Discharge Pressure",
                "description": "Compressor outlet pressure sensor",
                "node_id": "ns=2;i=1001",
                "unit": "bar",
                "data_type": "Float",
                "equipment_id": 1,
            }
        }
    )


class TagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    node_id: str | None = None
    unit: str | None = None
    data_type: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "unit": "psi",
                "description": "Updated unit to PSI per site standard",
            }
        }
    )


class TagResponse(TagBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Discharge Pressure",
                "description": "Compressor outlet pressure sensor",
                "node_id": "ns=2;i=1001",
                "unit": "bar",
                "data_type": "Float",
                "equipment_id": 1,
                "created_at": "2024-05-20T08:00:00Z",
            }
        },
    )

    id: int
    created_at: datetime
