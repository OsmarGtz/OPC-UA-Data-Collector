from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def get_tag(db: AsyncSession, tag_id: int) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tags_by_equipment(
    db: AsyncSession, equipment_id: int, skip: int = 0, limit: int = 100
) -> list[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.equipment_id == equipment_id).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_all_tags(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Tag]:
    result = await db.execute(select(Tag).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_tag(db: AsyncSession, data: TagCreate) -> Tag:
    tag = Tag(**data.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, data: TagUpdate) -> Tag:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.commit()
