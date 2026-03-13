from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("/", response_model=list[TagResponse])
async def list_tags(
    skip: int = 0,
    limit: int = 100,
    equipment_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if equipment_id is not None:
        return await crud.tag.get_tags_by_equipment(db, equipment_id, skip=skip, limit=limit)
    return await crud.tag.get_all_tags(db, skip=skip, limit=limit)


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    equipment = await crud.equipment.get_equipment(db, data.equipment_id)
    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipment {data.equipment_id} not found.",
        )
    return await crud.tag.create_tag(db, data)


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tag = await crud.tag.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: int,
    data: TagUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    tag = await crud.tag.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    return await crud.tag.update_tag(db, tag, data)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("engineer")),
):
    tag = await crud.tag.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found.")
    await crud.tag.delete_tag(db, tag)
