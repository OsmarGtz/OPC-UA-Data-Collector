from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReadingBase(BaseModel):
    tag_id: int
    value: float | None = None
    raw_value: str | None = None
    quality: str = "Good"


class ReadingCreate(ReadingBase):
    timestamp: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tag_id": 1,
                "value": 7.42,
                "raw_value": "7.42",
                "quality": "Good",
                "timestamp": "2024-05-20T14:30:00Z",
            }
        }
    )


class ReadingUpdate(BaseModel):
    value: float | None = None
    raw_value: str | None = None
    quality: str | None = None


class ReadingResponse(ReadingBase):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1042,
                "tag_id": 1,
                "value": 7.42,
                "raw_value": "7.42",
                "quality": "Good",
                "timestamp": "2024-05-20T14:30:00Z",
            }
        },
    )

    id: int
    timestamp: datetime


class LatestReadingResponse(BaseModel):
    """Most recent reading per tag, enriched with tag metadata.
    Returned by GET /equipment/{id}/latest."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tag_id": 1,
                "tag_name": "Discharge Pressure",
                "unit": "bar",
                "value": 7.42,
                "raw_value": "7.42",
                "quality": "Good",
                "timestamp": "2024-05-20T14:30:00Z",
            }
        }
    )

    tag_id: int
    tag_name: str
    unit: str | None
    value: float | None
    raw_value: str | None
    quality: str
    timestamp: datetime
