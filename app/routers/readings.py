from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.reading import ReadingCreate, ReadingResponse, ReadingUpdate

router = APIRouter(prefix="/readings", tags=["Readings"])


@router.get("/", response_model=list[ReadingResponse])
async def list_readings(
    tag_id: int,
    skip: int = 0,
    limit: int = 100,
    since: datetime | None = Query(default=None),
    until: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tag = await crud.tag.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return await crud.reading.get_readings_by_tag(
        db, tag_id, skip=skip, limit=limit, since=since, until=until
    )


@router.post("/", response_model=ReadingResponse, status_code=status.HTTP_201_CREATED)
async def create_reading(
    data: ReadingCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    tag = await crud.tag.get_tag(db, data.tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag {data.tag_id} not found.",
        )
    return await crud.reading.create_reading(db, data)


@router.get("/{reading_id}", response_model=ReadingResponse)
async def get_reading(
    reading_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    reading = await crud.reading.get_reading(db, reading_id)
    if not reading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found.")
    return reading


@router.patch("/{reading_id}", response_model=ReadingResponse)
async def update_reading(
    reading_id: int,
    data: ReadingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    reading = await crud.reading.get_reading(db, reading_id)
    if not reading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found.")
    return await crud.reading.update_reading(db, reading, data)


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading(
    reading_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    reading = await crud.reading.get_reading(db, reading_id)
    if not reading:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading not found.")
    await crud.reading.delete_reading(db, reading)
