from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.equipment import Equipment
from app.schemas.equipment import EquipmentCreate, EquipmentUpdate


async def get_equipment(db: AsyncSession, equipment_id: int) -> Equipment | None:
    result = await db.execute(select(Equipment).where(Equipment.id == equipment_id))
    return result.scalar_one_or_none()


async def get_equipment_by_name(db: AsyncSession, name: str) -> Equipment | None:
    result = await db.execute(select(Equipment).where(Equipment.name == name))
    return result.scalar_one_or_none()


async def get_all_equipment(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Equipment]:
    result = await db.execute(select(Equipment).offset(skip).limit(limit))
    return list(result.scalars().all())


async def create_equipment(db: AsyncSession, data: EquipmentCreate) -> Equipment:
    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    await db.commit()
    await db.refresh(equipment)
    return equipment


async def update_equipment(
    db: AsyncSession, equipment: Equipment, data: EquipmentUpdate
) -> Equipment:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)
    await db.commit()
    await db.refresh(equipment)
    return equipment


async def delete_equipment(db: AsyncSession, equipment: Equipment) -> None:
    await db.delete(equipment)
    await db.commit()
