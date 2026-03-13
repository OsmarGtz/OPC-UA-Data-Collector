from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EquipmentBase(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None


class EquipmentCreate(EquipmentBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Compressor A1",
                "description": "Main air compressor — production line 1",
                "location": "Building 3, Floor 2, Bay 4",
            }
        }
    )


class EquipmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Replaced belt assembly on 2024-06-01",
                "location": "Building 3, Floor 2, Bay 5",
            }
        }
    )


class EquipmentResponse(EquipmentBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Compressor A1",
                "description": "Main air compressor — production line 1",
                "location": "Building 3, Floor 2, Bay 4",
                "created_at": "2024-05-20T08:00:00Z",
                "updated_at": "2024-05-20T08:00:00Z",
            }
        },
    )

    id: int
    created_at: datetime
    updated_at: datetime
