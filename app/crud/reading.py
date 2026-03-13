from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading import Reading
from app.models.tag import Tag
from app.schemas.reading import ReadingCreate, ReadingUpdate


async def get_reading(db: AsyncSession, reading_id: int) -> Reading | None:
    result = await db.execute(select(Reading).where(Reading.id == reading_id))
    return result.scalar_one_or_none()


async def get_readings_by_tag(
    db: AsyncSession,
    tag_id: int,
    skip: int = 0,
    limit: int = 100,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[Reading]:
    query = select(Reading).where(Reading.tag_id == tag_id)
    if since:
        query = query.where(Reading.timestamp >= since)
    if until:
        query = query.where(Reading.timestamp <= until)
    query = query.order_by(Reading.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_reading(db: AsyncSession, data: ReadingCreate) -> Reading:
    reading_data = data.model_dump()
    if reading_data.get("timestamp") is None:
        reading_data.pop("timestamp")
    reading = Reading(**reading_data)
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


async def update_reading(
    db: AsyncSession, reading: Reading, data: ReadingUpdate
) -> Reading:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(reading, field, value)
    await db.commit()
    await db.refresh(reading)
    return reading


async def delete_reading(db: AsyncSession, reading: Reading) -> None:
    await db.delete(reading)
    await db.commit()


async def get_latest_readings_by_equipment(
    db: AsyncSession,
    equipment_id: int,
) -> list[tuple[Reading, Tag]]:
    """Return the most recent Reading for each tag belonging to equipment_id."""
    subq = (
        select(
            Reading.tag_id,
            func.max(Reading.timestamp).label("max_ts"),
        )
        .join(Tag, Reading.tag_id == Tag.id)
        .where(Tag.equipment_id == equipment_id)
        .group_by(Reading.tag_id)
        .subquery()
    )
    stmt = (
        select(Reading, Tag)
        .join(Tag, Reading.tag_id == Tag.id)
        .join(
            subq,
            (Reading.tag_id == subq.c.tag_id) & (Reading.timestamp == subq.c.max_ts),
        )
        .order_by(Tag.name)
    )
    result = await db.execute(stmt)
    return [(reading, tag) for reading, tag in result.all()]


async def get_readings_by_equipment(
    db: AsyncSession,
    equipment_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 1000,
) -> list[Reading]:
    """Return readings for all tags of an equipment, optionally bounded by time."""
    stmt = (
        select(Reading)
        .join(Tag, Reading.tag_id == Tag.id)
        .where(Tag.equipment_id == equipment_id)
    )
    if start:
        stmt = stmt.where(Reading.timestamp >= start)
    if end:
        stmt = stmt.where(Reading.timestamp <= end)
    stmt = stmt.order_by(Reading.timestamp.asc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
