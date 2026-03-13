from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.equipment import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.schemas.reading import LatestReadingResponse, ReadingResponse

router = APIRouter(prefix="/equipment", tags=["Equipment"])

_404: dict[int | str, dict[str, Any]] = {404: {"description": "Equipment not found"}}
_AUTH: dict[int | str, dict[str, Any]] = {401: {"description": "Missing or invalid token"}}
_RBAC: dict[int | str, dict[str, Any]] = {403: {"description": "Insufficient role (engineer or admin required)"}}


@router.get(
    "/",
    response_model=list[EquipmentResponse],
    summary="List all equipment",
    responses={**_AUTH},
)
async def list_equipment(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return a paginated list of all registered equipment units."""
    return await crud.equipment.get_all_equipment(db, skip=skip, limit=limit)


@router.post(
    "/",
    response_model=EquipmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new equipment",
    responses={**_AUTH, **_RBAC, 409: {"description": "Name already exists"}},
)
async def create_equipment(
    data: EquipmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer", "admin")),
):
    """Register a new physical asset. Name must be unique.
    Requires **engineer** or **admin** role."""
    existing = await crud.equipment.get_equipment_by_name(db, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Equipment with name '{data.name}' already exists.",
        )
    return await crud.equipment.create_equipment(db, data)


@router.get(
    "/{equipment_id}",
    response_model=EquipmentResponse,
    summary="Get equipment by ID",
    responses={**_AUTH, **_404},
)
async def get_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Fetch a single equipment record by its primary key."""
    equipment = await crud.equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    return equipment


@router.patch(
    "/{equipment_id}",
    response_model=EquipmentResponse,
    summary="Update equipment metadata",
    responses={**_AUTH, **_RBAC, **_404},
)
async def update_equipment(
    equipment_id: int,
    data: EquipmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer", "admin")),
):
    """Partially update an equipment record (name, description, location).
    Requires **engineer** or **admin** role."""
    equipment = await crud.equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    return await crud.equipment.update_equipment(db, equipment, data)


@router.get(
    "/{equipment_id}/latest",
    response_model=list[LatestReadingResponse],
    summary="Latest reading per tag",
    responses={**_AUTH, **_404},
)
async def get_latest_readings(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return the single most recent reading for every tag on this equipment.
    Used by the dashboard overview cards."""
    equipment = await crud.equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    pairs = await crud.reading.get_latest_readings_by_equipment(db, equipment_id)
    return [
        LatestReadingResponse(
            tag_id=reading.tag_id,
            tag_name=tag.name,
            unit=tag.unit,
            value=reading.value,
            raw_value=reading.raw_value,
            quality=reading.quality,
            timestamp=reading.timestamp,
        )
        for reading, tag in pairs
    ]


@router.get(
    "/{equipment_id}/readings",
    response_model=list[ReadingResponse],
    summary="Time-series readings for equipment",
    responses={**_AUTH, **_404},
)
async def get_equipment_readings(
    equipment_id: int,
    start: datetime | None = Query(default=None, description="ISO-8601 start time (inclusive)"),
    end: datetime | None = Query(default=None, description="ISO-8601 end time (inclusive)"),
    limit: int = Query(default=1000, le=5000, description="Maximum rows to return"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return time-series readings for all tags on this equipment, optionally filtered
    by a time window. Used by the dashboard trend charts."""
    equipment = await crud.equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    return await crud.reading.get_readings_by_equipment(
        db, equipment_id, start=start, end=end, limit=limit
    )


@router.delete(
    "/{equipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete equipment",
    responses={**_AUTH, **_RBAC, **_404},
)
async def delete_equipment(
    equipment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer", "admin")),
):
    """Permanently delete an equipment record and cascade to its tags and readings.
    Requires **engineer** or **admin** role."""
    equipment = await crud.equipment.get_equipment(db, equipment_id)
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found.")
    await crud.equipment.delete_equipment(db, equipment)
